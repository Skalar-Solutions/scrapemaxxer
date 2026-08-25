import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", str(BASE_DIR / "output")))
USER_AGENT = os.getenv("USER_AGENT", "").strip() or None
TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
DELAY = float(os.getenv("REQUEST_DELAY", "0"))
