"""Explicit local LLM roles: fast ingest vision and larger interactive reasoning."""
from pathlib import Path

FAST_VISION_MODEL = 'Qwen3.5-4B-4bit'
CHAT_MODEL = 'Qwen3.8-27B-4bit'
MODEL_ROLES = {'ingest_vision': FAST_VISION_MODEL, 'agentic_chat': CHAT_MODEL}
ANALYSIS_MODELS = ('parakeet', FAST_VISION_MODEL)
MODEL_LOCK = {
    'parakeet': ('mlx-community/parakeet-tdt-0.6b-v3', 'ed2b7e8c15f9aaa0b5772e2efb986255eaef7e15'),
    FAST_VISION_MODEL: ('mlx-community/Qwen3.5-4B-4bit', '0e7ffd5c629ef7719d4cbc04069232580bfa9d9c'),
    CHAT_MODEL: ('mlx-community/Qwen3.8-27B-4bit', '10c35caafbb80f7dc6a7a432cdd11af10a6d4818'),
}


def model_path(root, role):
    """Resolve a declared role; unknown roles never silently select the small model."""
    try:
        name = MODEL_ROLES[role]
    except KeyError:
        raise ValueError('Unknown local LLM role: ' + str(role)) from None
    return Path(root) / 'models' / name
