"""
llm.py — Dual-provider LLM helper for the Investigator Chat bonus
================================================================
Same pattern as Phase 2 (OpenAI or Gemini via LLM_PROVIDER).
Fully implemented — no TODOs.
"""

from __future__ import annotations

import os

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI


def get_llm(temperature: float = 0):
    """Return a chat model based on LLM_PROVIDER in .env."""
    provider = os.getenv("LLM_PROVIDER", "gemini").lower().strip()

    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is missing from .env")
        return ChatOpenAI(model="gpt-4.1", temperature=temperature, api_key=api_key)

    if provider == "gemini":
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is missing from .env")
        return ChatGoogleGenerativeAI(
            model="gemini-3.1-flash-lite",
            temperature=temperature,
            google_api_key=api_key,
        )

    raise ValueError(
        f"Unknown LLM_PROVIDER={provider!r}. Use 'openai' or 'gemini'."
    )
