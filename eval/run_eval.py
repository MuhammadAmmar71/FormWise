"""Evaluate retrieval and answering against eval/questions.jsonl.

  python eval/run_eval.py              # retrieval only (embeddings + Supabase, no chat LLM)
  python eval/run_eval.py --full       # full graph: routing, citations, refusals (uses Groq quota)

Needs the same environment as the backend (backend/.env).
"""
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app import llm, retrieval  # noqa: E402
from app.graph import TEMPLATES, build_graph  # noqa: E402

K = 5


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true", help="run the whole LangGraph pipeline")
    args = parser.parse_args()

    items = [json.loads(line) for line in (ROOT / "eval/questions.jsonl").open(encoding="utf-8")]
    in_scope = [i for i in items if not i.get("out_of_scope")]

    hits = 0
    for item in in_scope:
        got = [c.source_id for c in retrieval.retrieve(item["q"], k=K)]
        hit = any(s in got for s in item["expect"])
        hits += hit
        print(f"{'✓' if hit else '✗'} {item['q'][:70]:<70} {got}")
        time.sleep(0.5)
    print(f"\nRetrieval hit@{K}: {hits}/{len(in_scope)} = {hits / len(in_scope):.0%}")

    if not args.full:
        return

    graph = build_graph(chat=llm.chat, retrieve=retrieval.retrieve)
    cited = refused_ok = 0
    for item in items:
        state = graph.invoke({"message": item["q"], "ui_lang": item["lang"]})
        if item.get("out_of_scope"):
            ok = state["route"] == "out_of_scope"
            refused_ok += ok
        else:
            ok = bool(state.get("citations")) and state["answer"] not in TEMPLATES["not_covered"].values()
            cited += ok
        print(f"{'✓' if ok else '✗'} [{state['route']}] {item['q'][:60]} -> {state['answer'][:80]!r}")
        time.sleep(2)  # Groq free tier: stay under the per-minute limit
    n_out = len(items) - len(in_scope)
    print(f"\nAnswered with valid citations: {cited}/{len(in_scope)} = {cited / len(in_scope):.0%}")
    print(f"Out-of-scope correctly refused: {refused_ok}/{n_out}")


if __name__ == "__main__":
    main()
