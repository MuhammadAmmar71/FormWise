from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from . import config, llm, retrieval
from .graph import FORM, TEMPLATES, build_graph

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="FormWise (unofficial)", docs_url=None, redoc_url=None)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(CORSMiddleware, allow_origins=config.ALLOWED_ORIGINS,
                   allow_methods=["GET", "POST"], allow_headers=["Content-Type"])

graph = build_graph(chat=llm.chat, retrieve=retrieval.retrieve)


class Turn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=2000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    lang: Literal["en", "de"] = "en"
    field_id: str | None = None
    history: list[Turn] = Field(default_factory=list, max_length=10)


class Citation(BaseModel):
    n: int
    title: str
    section: str
    url: str
    excerpt: str


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    lang: Literal["en", "de"]
    route: str
    pii_warning: str | None = None


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/form/anmeldung")
def form() -> dict:
    return FORM


@app.post("/chat", response_model=ChatResponse)
@limiter.limit(config.RATE_LIMIT)
def chat(request: Request, body: ChatRequest) -> ChatResponse:
    # Nothing from the request is logged or stored.
    try:
        state = graph.invoke({
            "message": body.message, "ui_lang": body.lang, "field_id": body.field_id,
            "history": [t.model_dump() for t in body.history],
        })
    except Exception as exc:  # upstream free-tier quota or network errors
        raise HTTPException(status_code=503, detail="The assistant is temporarily unavailable. Please try again later.") from exc
    return ChatResponse(
        answer=state["answer"], citations=state.get("citations", []), lang=state["lang"], route=state["route"],
        pii_warning=TEMPLATES["pii_warning"][state["lang"]] if state.get("pii_found") else None,
    )
