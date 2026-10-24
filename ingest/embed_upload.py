"""Embed ingest/chunks.jsonl with Gemini and upsert sources + chunks into Supabase.

Needs GEMINI_API_KEY, SUPABASE_URL and SUPABASE_SERVICE_KEY (env or backend/.env).
"""
import json
import math
import os
import time
from pathlib import Path

import httpx
import yaml
from dotenv import load_dotenv

HERE = Path(__file__).parent
load_dotenv(HERE.parent / "backend" / ".env")

EMBED_MODEL = os.getenv("EMBED_MODEL", "gemini-embedding-001")
EMBED_DIM = 768
BATCH = 20


def normalize(vec: list[float]) -> list[float]:
    # Gemini only normalizes the full-size embedding; truncated ones must be normalized by hand.
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def embed_documents(client: httpx.Client, texts: list[str]) -> list[list[float]]:
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/{EMBED_MODEL}"
           f":batchEmbedContents?key={os.environ['GEMINI_API_KEY']}")
    body = {"requests": [{
        "model": f"models/{EMBED_MODEL}",
        "content": {"parts": [{"text": t}]},
        "taskType": "RETRIEVAL_DOCUMENT",
        "outputDimensionality": EMBED_DIM,
    } for t in texts]}
    resp = client.post(url, json=body, timeout=60)
    resp.raise_for_status()
    return [normalize(e["values"]) for e in resp.json()["embeddings"]]


def upsert(client: httpx.Client, table: str, rows: list[dict]) -> None:
    key = os.environ["SUPABASE_SERVICE_KEY"]
    resp = client.post(
        f"{os.environ['SUPABASE_URL']}/rest/v1/{table}",
        json=rows,
        headers={"apikey": key, "Authorization": f"Bearer {key}",
                 "Prefer": "resolution=merge-duplicates"},
        timeout=60,
    )
    resp.raise_for_status()


def main() -> None:
    config = yaml.safe_load((HERE / "sources.yaml").read_text(encoding="utf-8"))
    titles = {s["id"]: s["title"] for s in config["sources"]}
    chunks = [json.loads(line) for line in (HERE / "chunks.jsonl").open(encoding="utf-8")]

    with httpx.Client() as client:
        upsert(client, "sources", [{
            "id": s["id"], "kind": s["kind"], "url": s["url"], "title": s["title"],
            "publisher": s["publisher"], "lang": s["lang"], "retrieved_at": config["retrieved_at"],
        } for s in config["sources"]])

        for i in range(0, len(chunks), BATCH):
            batch = chunks[i:i + BATCH]
            # Prefix title + section so short chunks ("Gebühren: keine") keep their context.
            texts = [f"{titles[c['source_id']]} – {c['section']}\n{c['content']}" for c in batch]
            for c, vec in zip(batch, embed_documents(client, texts), strict=True):
                c["embedding"] = vec
            upsert(client, "chunks", batch)
            print(f"uploaded {i + len(batch)}/{len(chunks)}")
            time.sleep(1)  # stay well inside the free-tier rate limit


if __name__ == "__main__":
    main()
