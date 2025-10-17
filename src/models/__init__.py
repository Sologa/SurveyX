"""
Package initializer for `src.models`.

Avoid importing heavy optional dependencies at package import time.
Modules that need RAG functionality should import it explicitly:

    from src.models.rag.modeling_llamaidx import LlamaIndexWrapper

This prevents unrelated imports (e.g., `src.models.LLM.EmbedAgent`) from
failing if optional deps like `openai` or `llama_index` are not installed.
"""

# Intentionally keep this file minimal to avoid side‑effects on import.
