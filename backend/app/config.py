import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

CHAT_MODEL = os.getenv("CHAT_MODEL", "llama-3.3-70b-versatile")
ROUTER_MODEL = os.getenv("ROUTER_MODEL", "llama-3.1-8b-instant")
EMBED_MODEL = os.getenv("EMBED_MODEL", "gemini-embedding-001")
EMBED_DIM = 768

TOP_K = int(os.getenv("TOP_K", "5"))
# Below this cosine similarity the best chunk is treated as "not covered by the sources".
MIN_SIMILARITY = float(os.getenv("MIN_SIMILARITY", "0.55"))

ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",") if o.strip()]
RATE_LIMIT = os.getenv("RATE_LIMIT", "10/minute;100/day")
