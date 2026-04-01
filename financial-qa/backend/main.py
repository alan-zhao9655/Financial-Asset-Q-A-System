import warnings
import logging

# Suppress noisy yfinance / pandas deprecation warnings
warnings.filterwarnings("ignore", message="Timestamp.utcnow is deprecated")
warnings.filterwarnings("ignore", message="The 'unit' keyword")
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Configure structured logging for the application
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
# Silence noisy third-party loggers
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("yfinance").setLevel(logging.WARNING)
logging.getLogger("peewee").setLevel(logging.WARNING)

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import query, chat

app = FastAPI(title="Financial Asset Q&A System", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query.router, prefix="/api")
app.include_router(chat.router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}
