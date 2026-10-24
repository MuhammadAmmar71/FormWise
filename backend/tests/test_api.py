from fastapi.testclient import TestClient

from app import main


class FakeGraph:
    def invoke(self, state):
        return {**state, "lang": "en", "route": "process_question", "pii_found": [],
                "answer": "Two weeks [1].", "citations": [{"n": 1, "title": "§ 17 BMG", "section": "s",
                                                           "url": "https://example.org", "excerpt": "e"}]}


def client(monkeypatch):
    monkeypatch.setattr(main, "graph", FakeGraph())
    return TestClient(main.app)


def test_form_schema(monkeypatch):
    form = client(monkeypatch).get("/form/anmeldung").json()
    ids = [f["id"] for g in form["groups"] for f in g["fields"]]
    assert "landlord_confirmation" in ids and len(ids) == len(set(ids))


def test_chat(monkeypatch):
    resp = client(monkeypatch).post("/chat", json={"message": "How long?", "lang": "en"})
    assert resp.status_code == 200
    assert resp.json()["citations"][0]["n"] == 1


def test_chat_rejects_oversized_message(monkeypatch):
    resp = client(monkeypatch).post("/chat", json={"message": "x" * 1001})
    assert resp.status_code == 422


def test_form_sources_exist_in_sources_yaml():
    import json
    from pathlib import Path

    import yaml
    root = Path(__file__).parents[2]
    known = {s["id"] for s in yaml.safe_load((root / "ingest/sources.yaml").read_text())["sources"]}
    form = json.loads((root / "backend/app/forms/anmeldung.json").read_text())
    used = {s for g in form["groups"] for f in g["fields"] for s in f["sources"]}
    used |= {s for item in form["checklist"] for s in item["sources"]}
    assert used <= known


def test_form_source_links_match_sources_yaml():
    import json
    from pathlib import Path

    import yaml
    root = Path(__file__).parents[2]
    srcs = {s["id"]: s for s in yaml.safe_load((root / "ingest/sources.yaml").read_text())["sources"]}
    form = json.loads((root / "backend/app/forms/anmeldung.json").read_text())
    assert {k: v["url"] for k, v in form["sources"].items()} == {k: v["url"] for k, v in srcs.items()}
