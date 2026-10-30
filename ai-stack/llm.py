"""One way to call any model in the registry: ask(), speak(), transcribe().

Each provider uses its own official SDK. Keys come from .env (copy .env.example).
Run directly to smoke-test every model whose key is set:  .venv/bin/python llm.py
"""
import os

from dotenv import load_dotenv

load_dotenv()

# Model registry. The router picks a key from here. Costs are USD per 1M input/output tokens
# (Claude from Anthropic's price list; others are approximate, check the provider before quoting).
MODELS = {
    "opus-5.5":   {"provider": "anthropic", "id": "claude-opus-5-5",   "cost": (4.00, 20.00), "modality": "text,image"},
    "opus-5":     {"provider": "anthropic", "id": "claude-opus-5",     "cost": (5.00, 25.00), "modality": "text,image"},
    "sonnet-5.5": {"provider": "anthropic", "id": "claude-sonnet-5-5", "cost": (2.00, 10.00), "modality": "text,image"},
    "sonnet-5":   {"provider": "anthropic", "id": "claude-sonnet-5",   "cost": (2.00, 10.00), "modality": "text,image"},
    "haiku-5.5":  {"provider": "anthropic", "id": "claude-haiku-5-5",  "cost": (0.10, 0.50),  "modality": "text,image"},
    "gpt-5.6-sol": {"provider": "openai", "id": "gpt-5.6-sol",         "cost": (5.00, 30.00), "modality": "text,image"},
    "gemini-3.6-flash": {"provider": "google", "id": "gemini-3.6-flash", "cost": (1.50, 7.50), "modality": "text,image,audio"},
    "deepgram-aura": {"provider": "deepgram", "id": "aura-2-thalia-en", "cost": None, "modality": "tts"},
    "deepgram-stt":  {"provider": "deepgram", "id": "nova-3",           "cost": None, "modality": "stt"},
}

KEY_ENV = {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY",
           "google": "GEMINI_API_KEY", "deepgram": "DEEPGRAM_API_KEY"}

# Claude models that accept server-side refusal fallbacks (beta).
_FALLBACK_OK = {"claude-opus-5-5", "claude-opus-5", "claude-sonnet-5-5"}


def has_key(model_key: str) -> bool:
    return bool(os.getenv(KEY_ENV[MODELS[model_key]["provider"]]))


def ask(model_key: str, prompt: str, system: str = "", max_tokens: int = 16000, effort: str = "medium") -> str:
    """Send one text prompt, return the text answer."""
    m = MODELS[model_key]
    if not has_key(model_key):
        raise RuntimeError(f"{KEY_ENV[m['provider']]} is not set in .env, so {model_key} can't be called")

    if m["provider"] == "anthropic":
        import anthropic
        # Keys not scoped to a workspace need the workspace id sent as a header.
        ws = os.getenv("ANTHROPIC_WORKSPACE_ID")
        client = anthropic.Anthropic(default_headers={"anthropic-workspace-id": ws} if ws else None)
        kwargs = dict(model=m["id"], max_tokens=max_tokens, messages=[{"role": "user", "content": prompt}],
                      output_config={"effort": effort})
        if system:
            kwargs["system"] = system
        if m["id"] in _FALLBACK_OK:
            resp = client.beta.messages.create(**kwargs, betas=["server-side-fallback-2026-07-01"], fallbacks="default")
        else:
            resp = client.messages.create(**kwargs)
        if resp.stop_reason == "refusal":
            return f"[refused: {resp.stop_details.category if resp.stop_details else 'unknown'}]"
        return "".join(b.text for b in resp.content if b.type == "text")

    if m["provider"] == "openai":
        from openai import OpenAI
        resp = OpenAI().responses.create(model=m["id"], instructions=system or None, input=prompt)
        return resp.output_text

    if m["provider"] == "google":
        from google import genai
        from google.genai import types
        config = types.GenerateContentConfig(system_instruction=system) if system else None
        resp = genai.Client().models.generate_content(model=m["id"], contents=prompt, config=config)
        return resp.text

    raise ValueError(f"{model_key} is a {m['modality']} model; use speak() or transcribe()")


def speak(text: str, out_path: str = "speech.mp3", model_key: str = "deepgram-aura") -> str:
    """Text to speech with Deepgram Aura. Returns the saved audio file path."""
    from deepgram import DeepgramClient
    audio = DeepgramClient().speak.v1.audio.generate(text=text, model=MODELS[model_key]["id"])
    with open(out_path, "wb") as f:
        for chunk in audio:
            f.write(chunk)
    return out_path


def transcribe(audio_path: str, model_key: str = "deepgram-stt") -> str:
    """Speech to text for a recorded file. (Flux is for live streams over a WebSocket; see README.)"""
    from deepgram import DeepgramClient
    with open(audio_path, "rb") as f:
        resp = DeepgramClient().listen.v1.media.transcribe_file(
            request=f.read(), model=MODELS[model_key]["id"], smart_format=True)
    return resp.results.channels[0].alternatives[0].transcript


if __name__ == "__main__":
    for key, m in MODELS.items():
        if m["modality"] in ("tts", "stt"):
            continue
        if not has_key(key):
            print(f"{key:18} skipped, no {KEY_ENV[m['provider']]}")
            continue
        try:
            print(f"{key:18} {ask(key, 'Reply with exactly: ok', max_tokens=2000, effort='low').strip()[:60]}")
        except Exception as e:
            print(f"{key:18} ERROR {type(e).__name__}: {str(e)[:120]}")
    if os.getenv("DEEPGRAM_API_KEY"):
        path = speak("Your container has cleared customs.")
        print(f"deepgram-aura      saved {path}; transcribed back: {transcribe(path)!r}")
    else:
        print("deepgram           skipped, no DEEPGRAM_API_KEY")
