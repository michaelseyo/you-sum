from app.config import get_openai_api_key
from openai import AsyncOpenAI


def create_openai_client() -> AsyncOpenAI:
    return AsyncOpenAI(api_key=get_openai_api_key())
