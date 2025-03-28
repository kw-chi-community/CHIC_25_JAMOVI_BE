from langchain_google_genai import GoogleGenerativeAI
from dotenv import load_dotenv
import os
import logging

logger = logging.getLogger(__name__)

formatter = logging.Formatter(
    '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger.addHandler(handler)
logger.setLevel(logging.INFO)

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

llm = GoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=api_key,
    temperature=0.0,
    max_output_tokens=8192,
)

llm_lite = GoogleGenerativeAI(
    model="gemini-2.0-flash-lite-preview-02-05",
    google_api_key=api_key,
    temperature=0.0,
    max_output_tokens=8192,
)

logger.info("llm initialized") 