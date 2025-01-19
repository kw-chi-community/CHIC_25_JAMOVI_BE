from langchain_google_genai import GoogleGenerativeAI
from dotenv import load_dotenv
import os
from utils import logger

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

llm = GoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=api_key,
    temperature=0.0,
    streaming=True)

logger.info("llm initialized") 