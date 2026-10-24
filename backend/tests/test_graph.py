from app.graph import TEMPLATES, build_graph, detect_lang
from app.retrieval import Chunk

CHUNKS = [
    Chunk("bmg-17#0", "bmg-17", "§ 17 BMG – Anmeldung, Abmeldung", "§ 17 BMG – Anmeldung, Abmeldung",
          "(1) Wer eine Wohnung bezieht, hat sich innerhalb von zwei Wochen nach dem Einzug bei der Meldebehörde anzumelden.",
          "https://www.gesetze-im-internet.de/bmg/__17.html", 0.82),
    Chunk("bmg-19#0", "bmg-19", "§ 19 BMG – Mitwirkung des Wohnungsgebers", "§ 19 BMG",
          "(1) Der Wohnungsgeber ist verpflichtet, bei der Anmeldung mitzuwirken.",
          "https://www.gesetze-im-internet.de/bmg/__19.html", 0.70),
]


class FakeChat:
    def __init__(self, route="IN", answer="You must register within two weeks of moving in [1]."):
        self.route, self.answer_text, self.calls = route, answer, []

    def __call__(self, messages, model=None, **kwargs):
        self.calls.append(messages)
        return self.route if kwargs.get("max_tokens") == 3 else self.answer_text


def run(chat, message, chunks=CHUNKS, **extra):
    queries = []

    def retrieve(q):
        queries.append(q)
        return chunks

    state = build_graph(chat=chat, retrieve=retrieve).invoke({"message": message, "ui_lang": "en", **extra})
    return state, queries


def test_detect_lang():
    assert detect_lang("Wie lange habe ich Zeit, mich anzumelden?", "en") == "de"
    assert detect_lang("How long do I have to register?", "de") == "en"
    assert detect_lang("Anmeldung?", "de") == "de"


def test_grounded_answer_returns_citations():
    state, _ = run(FakeChat(), "How long do I have to register?")
    assert state["route"] == "process_question"
    assert [c["n"] for c in state["citations"]] == [1]
    assert state["citations"][0]["url"].endswith("__17.html")


def test_out_of_scope_skips_retrieval():
    state, queries = run(FakeChat(route="OUT"), "How do I apply for a Blue Card?")
    assert state["answer"] == TEMPLATES["out_of_scope"]["en"]
    assert queries == []


def test_uncited_answer_is_replaced_by_refusal():
    state, _ = run(FakeChat(answer="You have 30 days."), "How long do I have to register?")
    assert state["answer"] == TEMPLATES["not_covered"]["en"] and state["citations"] == []


def test_invalid_citation_number_is_refused():
    state, _ = run(FakeChat(answer="Two weeks [7]."), "How long do I have to register?")
    assert state["answer"] == TEMPLATES["not_covered"]["en"]


def test_low_similarity_does_not_call_answer_llm():
    weak = [Chunk(**{**CHUNKS[0].__dict__, "similarity": 0.2})]
    chat = FakeChat()
    state, _ = run(chat, "What is the capital of Peru?", chunks=weak)
    assert state["answer"] == TEMPLATES["not_covered"]["en"]
    assert len(chat.calls) == 1  # router only


def test_field_help_bypasses_router_and_adds_field_to_query():
    chat = FakeChat()
    state, queries = run(chat, "What do I write here?", field_id="residence_type")
    assert state["route"] == "field_help"
    assert "Art der Wohnung" in queries[0]
    assert len(chat.calls) == 1  # answer only, no router call


def test_pii_is_redacted_before_llm():
    chat = FakeChat()
    state, queries = run(chat, "My email is max@example.org, how long do I have to register?")
    assert state["pii_found"] == ["EMAIL"]
    assert "max@example.org" not in str(chat.calls) and "max@example.org" not in queries[0]
