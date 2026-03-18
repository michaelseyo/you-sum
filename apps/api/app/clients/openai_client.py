import os

from openai import AsyncOpenAI


def create_openai_client() -> AsyncOpenAI:
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    return AsyncOpenAI(api_key=api_key)
