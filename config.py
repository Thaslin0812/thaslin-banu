import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(BASE_DIR, "Image")
LOGO_PATH = os.path.join(IMAGE_DIR, "Logo.png")
WEB_LOGO_PATH = os.path.join(IMAGE_DIR, "inverseLogo.png")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
API_URL = os.getenv("API_URL", "http://localhost:8000/generate")
FOOTER_TEXT = "LegalEase Inc. | contact@legalease.com | All Rights Reserved."
