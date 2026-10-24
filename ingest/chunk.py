"""Turn raw HTML into retrieval chunks (ingest/chunks.jsonl).

Statutes are split by Absatz, "(1)", "(2)", ..., and merged up to MAX_CHARS.
Portal pages are split by their H2 sections, keeping only the allow-listed ones.
"""
import json
import re
from pathlib import Path

import yaml
from bs4 import BeautifulSoup

HERE = Path(__file__).parent
RAW = HERE / "raw"
OUT = HERE / "chunks.jsonl"
MAX_CHARS = 1800


def clean(text: str) -> str:
    lines = (re.sub(r"[ \t\u00a0]+", " ", line).strip() for line in text.splitlines())
    text = "\n".join(line for line in lines if line)
    # Re-attach list markers ("1.", "a)") that the HTML puts on their own line.
    return re.sub(r"(?m)^(\d+\.|[a-z]\))\n", r"\1 ", text)


def pack(parts: list[str]) -> list[str]:
    """Greedily merge consecutive parts into chunks of at most MAX_CHARS."""
    chunks, current = [], ""
    for part in parts:
        if len(part) > MAX_CHARS and "\n" in part:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(pack(part.split("\n")))
            continue
        if current and len(current) + len(part) + 1 > MAX_CHARS:
            chunks.append(current)
            current = part
        else:
            current = f"{current}\n{part}" if current else part
    if current:
        chunks.append(current)
    return chunks


def statute_sections(soup: BeautifulSoup, src: dict) -> list[tuple[str, str]]:
    body = soup.find("div", class_="jnhtml")
    text = clean(body.get_text("\n"))
    absaetze = re.split(r"\n(?=\(\d+[a-z]?\) )", "\n" + text)
    return [(src["title"], chunk) for chunk in pack([a.strip() for a in absaetze if a.strip()])]


def portal_sections(soup: BeautifulSoup, src: dict) -> list[tuple[str, str]]:
    h1 = soup.find("h1")
    out = []
    intro = h1.find_next_sibling("div", class_="block")
    if intro:
        out.extend(("Überblick", chunk) for chunk in pack(clean(intro.get_text("\n")).split("\n")))
    wanted = set(src.get("sections", []))
    for h2 in soup.find_all("h2"):
        name = h2.get_text(strip=True)
        if name in wanted:
            body = clean(h2.parent.get_text("\n"))
            out.extend((name, chunk) for chunk in pack(body.split("\n")))
    return out


def main() -> None:
    config = yaml.safe_load((HERE / "sources.yaml").read_text(encoding="utf-8"))
    n = 0
    with OUT.open("w", encoding="utf-8") as f:
        for src in config["sources"]:
            soup = BeautifulSoup((RAW / f"{src['id']}.html").read_bytes(), "html.parser")
            splitter = statute_sections if src["kind"] == "statute" else portal_sections
            for i, (section, content) in enumerate(splitter(soup, src)):
                f.write(json.dumps({
                    "id": f"{src['id']}#{i}",
                    "source_id": src["id"],
                    "lang": src["lang"],
                    "section": section,
                    "content": content,
                    "url": src["url"],
                }, ensure_ascii=False) + "\n")
                n += 1
    print(f"wrote {n} chunks to {OUT.relative_to(HERE.parent)}")


if __name__ == "__main__":
    main()
