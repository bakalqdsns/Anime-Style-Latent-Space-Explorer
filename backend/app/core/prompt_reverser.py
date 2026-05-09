"""
Prompt Reverse Engineering — LLM-powered prompt generation from style axis scores.

Primary: DeepSeek-V4-Flash (API)
Fallback: template-based prompt lookup
"""
from __future__ import annotations

import os
from typing import Optional

import httpx
from openai import OpenAI

from app.config import get_settings


settings = get_settings()


# System prompt for prompt generation
SYSTEM_PROMPT = """You are an expert anime visual prompt engineer.
Given style axis scores (from -1 to 1), generate a concise, effective prompt for AI image/video generation.

Guidelines:
- Focus on VISUAL STYLE keywords (colors, lighting, composition, mood)
- Use comma-separated keywords, not full sentences
- Max 50 words
- Only include style elements with high scores (>0.3)
- Exclude elements with negative scores (<-0.3)
- Be specific: "golden hour anime" not just "anime"
"""


def _build_user_message(style_axes: dict[str, float]) -> str:
    """Build user message with style axis scores."""
    lines = ["Style axis scores:"]
    for name, score in sorted(style_axes.items(), key=lambda x: abs(x[1]), reverse=True):
        lines.append(f"  - {name}: {score:.2f}")
    lines.append("\nGenerate a prompt in English, comma-separated, max 50 words.")
    return "\n".join(lines)


class PromptReverser:
    """
    Generate natural language prompts from style axis scores.

    Provider priority: DeepSeek-V4-Flash → OpenAI GPT-4o (fallback)
    """

    def __init__(self):
        self._deepseek_client: Optional[OpenAI] = None
        self._openai_client: Optional[OpenAI] = None

    def _get_deepseek_client(self) -> OpenAI:
        if self._deepseek_client is None:
            api_key = settings.deepseek_api_key or os.environ.get("DEEPSEEK_API_KEY", "")
            if not api_key:
                raise ValueError("DEEPSEEK_API_KEY not set. Set it in .env or env var.")
            self._deepseek_client = OpenAI(
                api_key=api_key,
                base_url=settings.deepseek_base_url or "https://api.deepseek.com",
            )
        return self._deepseek_client

    def _get_openai_client(self) -> OpenAI:
        if self._openai_client is None:
            api_key = settings.openai_api_key or os.environ.get("OPENAI_API_KEY", "")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set.")
            self._openai_client = OpenAI(api_key=api_key)
        return self._openai_client

    def generate(
        self,
        style_axes: dict[str, float],
        max_words: int = 50,
    ) -> dict:
        """
        Generate a prompt from style axis scores.

        Returns:
            {prompt, provider, confidence}
        """
        provider = settings.llm_provider or "deepseek"
        user_message = _build_user_message(style_axes)

        try:
            if provider == "deepseek":
                client = self._get_deepseek_client()
                model = settings.deepseek_model or "deepseek-chat"
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_message},
                    ],
                    temperature=0.7,
                    max_tokens=200,
                )
                prompt_text = response.choices[0].message.content.strip()
                provider_used = "deepseek"
            else:
                client = self._get_openai_client()
                model = settings.openai_model or "gpt-4o"
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_message},
                    ],
                    temperature=0.7,
                    max_tokens=200,
                )
                prompt_text = response.choices[0].message.content.strip()
                provider_used = "openai"

            # Estimate confidence based on score variance
            high_scores = [s for s in style_axes.values() if abs(s) > 0.3]
            confidence = len(high_scores) / max(len(style_axes), 1)

            return {
                "prompt": prompt_text,
                "provider": provider_used,
                "confidence": min(1.0, confidence),
                "style_axes_used": style_axes,
            }

        except Exception as e:
            # Fallback to template
            return self._fallback_prompt(style_axes)

    def _fallback_prompt(self, style_axes: dict[str, float]) -> dict:
        """Generate a basic prompt from high-scoring axes when LLM is unavailable."""
        lines = []
        for name, score in sorted(style_axes.items(), key=lambda x: x[1], reverse=True):
            if score > 0.3:
                lines.append(name.replace("_", " "))
            elif score < -0.3:
                lines.append(f"not {name.replace('_', ' ')}")

        if not lines:
            lines = ["anime style"]

        prompt_text = ", ".join(lines[:8])
        return {
            "prompt": prompt_text,
            "provider": "fallback",
            "confidence": 0.3,
            "style_axes_used": style_axes,
        }


_prompt_reverser: Optional[PromptReverser] = None


def get_prompt_reverser() -> PromptReverser:
    global _prompt_reverser
    if _prompt_reverser is None:
        _prompt_reverser = PromptReverser()
    return _prompt_reverser
