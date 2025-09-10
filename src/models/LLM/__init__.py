"""
Package initializer for `src.models.LLM`.

Do not import submodules here to avoid pulling heavy or optional
dependencies (e.g., `tenacity`, `requests`, `llama_index`) when the
package is imported. Import needed classes directly from their modules:

    from src.models.LLM.ChatAgent import ChatAgent
    from src.models.LLM.EmbedAgent import EmbedAgent
"""

# Keep empty to prevent side effects on import.
