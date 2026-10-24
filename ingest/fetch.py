"""Download every source listed in sources.yaml into ingest/raw/ (gitignored)."""
from pathlib import Path

import httpx
import yaml

HERE = Path(__file__).parent
RAW = HERE / "raw"
HEADERS = {"User-Agent": "formwise/0.1 (unofficial student portfolio project)"}


def main() -> None:
    config = yaml.safe_load((HERE / "sources.yaml").read_text(encoding="utf-8"))
    RAW.mkdir(exist_ok=True)
    with httpx.Client(headers=HEADERS, follow_redirects=True, timeout=30) as client:
        for src in config["sources"]:
            resp = client.get(src["url"])
            resp.raise_for_status()
            (RAW / f"{src['id']}.html").write_bytes(resp.content)
            print(f"{src['id']:<20} {len(resp.content):>8} bytes")


if __name__ == "__main__":
    main()
