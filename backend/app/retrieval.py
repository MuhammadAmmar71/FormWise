from dataclasses import dataclass

import httpx

from . import config, llm


@dataclass
class Chunk:
    id: str
    source_id: str
    title: str
    section: str
    content: str
    url: str
    similarity: float


def retrieve(query: str, k: int = config.TOP_K) -> list[Chunk]:
    resp = httpx.post(
        f"{config.SUPABASE_URL}/rest/v1/rpc/match_chunks",
        headers={"apikey": config.SUPABASE_SERVICE_KEY, "Authorization": f"Bearer {config.SUPABASE_SERVICE_KEY}"},
        json={"query_embedding": llm.embed_query(query), "match_count": k},
        timeout=30,
    )
    resp.raise_for_status()
    return [Chunk(**row) for row in resp.json()]
