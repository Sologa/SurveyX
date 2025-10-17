"""
Package initializer for `src.models.LLM`.

Expose key classes at package level so that

    from src.models.LLM import ChatAgent, EmbedAgent

returns the class objects (not submodules).
Prefer explicit imports when possible:

    from src.models.LLM.ChatAgent import ChatAgent
    from src.models.LLM.EmbedAgent import EmbedAgent
"""

from .ChatAgent import ChatAgent
from .EmbedAgent import EmbedAgent

__all__ = ["ChatAgent", "EmbedAgent"]
