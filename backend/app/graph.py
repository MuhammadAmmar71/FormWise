"""LangGraph pipeline: prepare -> route -> (out_of_scope | retrieve -> answer -> check).

The chat and retrieval functions are injected so the graph can be tested offline.
"""
import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import Literal, TypedDict

from langgraph.graph import END, StateGraph

from . import config, pii
from .retrieval import Chunk

FORM = json.loads((Path(__file__).parent / "forms" / "anmeldung.json").read_text(encoding="utf-8"))
FIELDS = {f["id"]: f for g in FORM["groups"] for f in g["fields"]}

Lang = Literal["en", "de"]


class State(TypedDict, total=False):
    message: str
    ui_lang: Lang
    field_id: str | None
    history: list[dict]
    lang: Lang
    pii_found: list[str]
    route: Literal["process_question", "field_help", "out_of_scope"]
    chunks: list[Chunk]
    answer: str
    citations: list[dict]


TEMPLATES = {
    "out_of_scope": {
        "en": ("I can only help with registering your address in Germany (the Anmeldung). "
               "For other matters, please check your city's official service portal or call the "
               "public-service number 115."),
        "de": ("Ich kann nur bei der Anmeldung einer Wohnung in Deutschland helfen. "
               "Für andere Anliegen wenden Sie sich bitte an das Serviceportal Ihrer Stadt "
               "oder an die Behördennummer 115."),
    },
    "not_covered": {
        "en": ("I don't know – the official sources I have don't cover this. "
               "Please check with your local Bürgeramt (registration office)."),
        "de": ("Das weiß ich nicht – meine offiziellen Quellen decken diese Frage nicht ab. "
               "Bitte fragen Sie bei Ihrem Bürgeramt nach."),
    },
    "pii_warning": {
        "en": "Please don't enter real personal data here – this is an unofficial demo. I removed it from your message.",
        "de": "Bitte geben Sie hier keine echten persönlichen Daten ein – dies ist eine inoffizielle Demo. Ich habe sie aus Ihrer Nachricht entfernt.",
    },
}

ROUTER_PROMPT = """You decide whether a user message is about registering a residence in Germany \
(Anmeldung / Meldepflicht / Meldeschein / Wohnungsgeberbestätigung / Bürgeramt / main or secondary \
residence / deadlines / fines / documents needed for registration / filling in the registration form). \
Greetings and thanks also count as IN. \
Visas, residence permits, taxes, other forms, legal disputes and unrelated topics are OUT.
Reply with exactly one word: IN or OUT."""

ANSWER_PROMPT = """You are an unofficial assistant that helps people understand the German residence \
registration (Anmeldung). Answer ONLY from the numbered official sources below. Rules:
- Reply in {language}. Keep it short and plain (max ~150 words); use simple words, explain German terms.
- Cite every factual sentence with the source number in square brackets, e.g. [1] or [2][3].
- If the sources do not answer the question, reply with exactly: NOT_COVERED
- Never invent deadlines, fees, documents or rules. Never ask for the user's real personal data.
- The sources are in German; if you answer in English, translate faithfully.
{field_context}
Sources:
{sources}"""

_GERMAN_HINTS = re.compile(
    r"(?i)\b(ich|und|ist|nicht|muss|wie|wann|wo|was|der|die|das|mein|meine|ein|eine|anmelden|wohnung|bitte|für)\b|[äöüß]"
)
_ENGLISH_HINTS = re.compile(
    r"(?i)\b(i|and|is|not|must|how|when|where|what|the|my|a|an|register|flat|apartment|please|for|do|need)\b"
)


def detect_lang(text: str, fallback: Lang) -> Lang:
    de, en = len(_GERMAN_HINTS.findall(text)), len(_ENGLISH_HINTS.findall(text))
    if de == en:
        return fallback
    return "de" if de > en else "en"


def build_graph(
    chat: Callable[..., str],
    retrieve: Callable[[str], list[Chunk]],
):
    def prepare(state: State) -> State:
        message, found = pii.redact(state["message"])
        return {"message": message, "pii_found": found,
                "lang": detect_lang(message, state.get("ui_lang", "en"))}

    def route(state: State) -> State:
        if state.get("field_id") in FIELDS:
            return {"route": "field_help"}
        verdict = chat(
            [{"role": "system", "content": ROUTER_PROMPT}, {"role": "user", "content": state["message"]}],
            model=config.ROUTER_MODEL, max_tokens=3,
        )
        return {"route": "out_of_scope" if verdict.strip().upper().startswith("OUT") else "process_question"}

    def out_of_scope(state: State) -> State:
        return {"answer": TEMPLATES["out_of_scope"][state["lang"]], "citations": []}

    def retrieve_node(state: State) -> State:
        query = state["message"]
        if state["route"] == "field_help":
            field = FIELDS[state["field_id"]]
            query = f"{field['label']['de']} ({field['label']['en']}): {query}"
        return {"chunks": retrieve(query)}

    def answer(state: State) -> State:
        chunks = state["chunks"]
        if not chunks or chunks[0].similarity < config.MIN_SIMILARITY:
            return {"answer": "NOT_COVERED"}
        field_context = ""
        if state["route"] == "field_help":
            field = FIELDS[state["field_id"]]
            field_context = f"- The user is filling in the form field \"{field['label']['de']}\" ({field['label']['en']})."
        sources = "\n\n".join(f"[{i}] {c.title} – {c.section}\n{c.content}" for i, c in enumerate(chunks, 1))
        system = ANSWER_PROMPT.format(
            language="English" if state["lang"] == "en" else "German",
            field_context=field_context, sources=sources,
        )
        history = [m for m in state.get("history", [])[-6:] if m.get("role") in ("user", "assistant")]
        return {"answer": chat([{"role": "system", "content": system}, *history,
                                {"role": "user", "content": state["message"]}])}

    def check(state: State) -> State:
        """Grounding check: an answer without valid citations is replaced by the refusal template."""
        text, chunks = state["answer"], state["chunks"]
        cited = sorted({int(n) for n in re.findall(r"\[(\d+)\]", text)})
        valid = [n for n in cited if 1 <= n <= len(chunks)]
        if "NOT_COVERED" in text or not valid or len(valid) != len(cited):
            return {"answer": TEMPLATES["not_covered"][state["lang"]], "citations": []}
        return {"citations": [{
            "n": n, "title": chunks[n - 1].title, "section": chunks[n - 1].section,
            "url": chunks[n - 1].url, "excerpt": chunks[n - 1].content[:400],
        } for n in valid]}

    g = StateGraph(State)
    g.add_node("prepare", prepare)
    g.add_node("route", route)
    g.add_node("out_of_scope", out_of_scope)
    g.add_node("retrieve", retrieve_node)
    g.add_node("answer", answer)
    g.add_node("check", check)
    g.set_entry_point("prepare")
    g.add_edge("prepare", "route")
    g.add_conditional_edges("route", lambda s: "out_of_scope" if s["route"] == "out_of_scope" else "retrieve")
    g.add_edge("out_of_scope", END)
    g.add_edge("retrieve", "answer")
    g.add_edge("answer", "check")
    g.add_edge("check", END)
    return g.compile()
