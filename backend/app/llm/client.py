"""OpenAI-compatible transport with the API key read afresh for every call."""

import os

from openai import AsyncOpenAI


class OpenAICompatibleTransport:
    def __init__(self, base_url, model, provider = "openai-compatible"):
        self.base_url = base_url
        self.model = model
        self.provider = provider

    async def complete_json(self, system_prompt, user_prompt, max_tokens):
        api_key = os.environ.get("LLM_API_KEY", "")
        if api_key == "":
            raise RuntimeError("LLM_API_KEY is not configured")
        client = AsyncOpenAI(api_key = api_key, base_url = self.base_url)
        answer = await client.chat.completions.create(
            model = self.model,
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens = max_tokens,
            temperature = 0,
        )
        content = answer.choices[0].message.content
        if not isinstance(content, str) or content.strip() == "":
            raise ValueError("The model returned no text")
        return content
