"""One function, three interchangeable backends: Claude API, local Ollama, any OpenAI-compatible server."""
import os
import requests
import db


def complete(system: str, user: str, settings: dict | None = None, max_tokens: int = 3000) -> str:
    s = settings or db.get_settings()
    p = s["provider"]

    if p == "anthropic":
        import anthropic
        client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env/.env
        r = client.messages.create(model=s["anthropic_model"], max_tokens=max_tokens, system=system,
                                   messages=[{"role": "user", "content": user}])
        return "".join(b.text for b in r.content if b.type == "text")

    if p == "ollama":
        r = requests.post(f"{s['ollama_url'].rstrip('/')}/api/chat", timeout=600, json={
            "model": s["ollama_model"], "stream": False, "format": "json",
            "options": {"num_ctx": 8192},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]})
        r.raise_for_status()
        return r.json()["message"]["content"]

    if p == "openai_compatible":
        body = {
            "model": s["openai_model"],
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        # gpt-oss spends most of the token budget on hidden reasoning and then
        # returns a cut-off JSON object, which the translator discards.
        model_name = (s.get("openai_model") or "").lower()
        if "gpt-oss" in model_name:
            body["reasoning_effort"] = "low"
        r = requests.post(
            f"{s['openai_base_url'].rstrip('/')}/chat/completions",
            timeout=300,
            headers={"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY', '')}"},
            json=body,
        )
        r.raise_for_status()
        message = r.json()["choices"][0]["message"]
        return message.get("content") or ""

    raise ValueError(f"Unknown provider: {p}")
