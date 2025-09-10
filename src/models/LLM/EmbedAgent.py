import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import hashlib
import math
import random
import requests

# Optional progress bar; fall back to no-op if not installed
try:  # noqa: SIM105
    from tqdm import tqdm as _tqdm  # type: ignore
except Exception:  # pragma: no cover - optional dep not always present
    def _tqdm(iterable, **kwargs):  # type: ignore
        return iterable

# Optional heavy dependency; keep import safe for offline/lightweight runs
try:  # noqa: SIM105
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding  # type: ignore
except Exception:  # pragma: no cover - optional dep not always present
    HuggingFaceEmbedding = None  # type: ignore

from src.configs.config import (
    BASE_DIR,
    DEFAULT_EMBED_LOCAL_MODEL,
    DEFAULT_EMBED_ONLINE_MODEL,
    EMBED_REMOTE_URL,
    EMBED_TOKEN,
)
from src.configs.logger import get_logger

logger = get_logger("src.models.LLM.EmbedAgent")


class EmbedAgent:
    """
    A class to handle remote text embedding using a specified API.
    Supports multi-threading for batch processing.
    """

    def __init__(self, token=EMBED_TOKEN, remote_url=EMBED_REMOTE_URL) -> None:
        """
        Initialize the EmbedAgent.

        Args:
            token (str): Authentication token for the remote API.
            remote_url (str): URL of the remote embedding API.
        """
        self.remote_url = remote_url
        self.token = token
        self.header = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }
        # Decide model path/name: prefer local cache dir if present
        self._use_fallback = False
        self.local_embedding_model = None
        local_dir = Path(BASE_DIR) / "models" / "bge-base"
        preferred_model = (
            str(local_dir) if local_dir.exists() else DEFAULT_EMBED_ONLINE_MODEL
        )

        if HuggingFaceEmbedding is not None:
            try:
                self.local_embedding_model = HuggingFaceEmbedding(
                    model_name=preferred_model
                )
            except Exception as e:
                logger.info(
                    f"{e}\nFailed to load embedding model {preferred_model}, try to use local model {DEFAULT_EMBED_LOCAL_MODEL}."
                )
                try:
                    self.local_embedding_model = HuggingFaceEmbedding(
                        model_name=DEFAULT_EMBED_LOCAL_MODEL
                    )
                except Exception as e2:
                    logger.warning(
                        f"{e2}\nHuggingFace embedding unavailable; falling back to deterministic numpy embedding."
                    )
                    self._use_fallback = True
        else:
            logger.info(
                "llama_index not installed; using deterministic numpy embedding fallback."
            )
            self._use_fallback = True

    def remote_embed(
        self,
        text: str,
        max_try: int = 15,
        debug: bool = False,
        model: str = "BAAI/bge-m3",
    ) -> list:
        """
        Embed text using the remote API.

        Args:
            text (str): Input text to embed.
            max_try (int, optional): Maximum number of retry attempts.
            debug (bool, optional): Whether to return debug information.
            model (str, optional): Model name for the remote API.

        Returns:
            list: Embedding vector or error message.
        """
        url = self.remote_url
        json_data = json.dumps(
            {"model": model, "input": text, "encoding_format": "float"}
        )

        try:
            response = requests.post(url, headers=self.header, data=json_data)
        except Exception as e:
            logger.error(f"Initial request failed: {e}")
            response = None
            for attempt in range(max_try):
                try:
                    response = requests.post(url, headers=self.header, data=json_data)
                    if response.status_code == 200:
                        logger.info(f"Retry {attempt + 1}/{max_try} succeeded.")
                        break
                except Exception as e:
                    logger.error(f"Retry {attempt + 1}/{max_try} failed: {e}")
                    response = None

        if response is None:
            error_msg = "embed response code: 000"
            if debug:
                return error_msg, response
            return []

        if response.status_code != 200:
            error_msg = f"embed response code: {response.status_code}\n{response.text}"
            logger.error(error_msg)
            if debug:
                return error_msg, response
            return []

        try:
            res = response.json()
            embedding = res["data"][0]["embedding"]
            if debug:
                return embedding, response
            return embedding
        except json.JSONDecodeError as e:
            logger.error(f"JSON decoding failed: {e}")
            if debug:
                return "JSON decoding failed", response
            return []

    def __remote_embed_task(self, index: int, text: str):
        """
        Internal method to handle embedding tasks in threads.

        Args:
            index (int): Index of the text in the input list.
            text (str): Text to embed.

        Returns:
            tuple: (index, embedding)
        """
        embedding = self.remote_embed(text)
        return index, embedding

    def batch_remote_embed(
        self, texts: list[str], worker: int = 10, desc: str = "Batch Embedding..."
    ) -> list:
        """
        Batch process text embeddings using multi-threading.

        Args:
            texts (list[str]): List of texts to embed.
            worker (int, optional): Number of worker threads.
            desc (str, optional): Description for the progress bar.

        Returns:
            list: List of embedding vectors.
        """
        embeddings = ["no response"] * len(texts)
        with ThreadPoolExecutor(max_workers=worker) as executor:
            future_l = [
                executor.submit(self.__remote_embed_task, i, texts[i])
                for i in range(len(texts))
            ]
            for future in _tqdm(
                as_completed(future_l),
                desc=desc,
                total=len(future_l),
                dynamic_ncols=True,
            ):
                i, embedding = future.result()
                embeddings[i] = embedding
        return embeddings

    def _fallback_embed(self, text: str, dim: int = 768) -> list[float]:
        """Deterministic lightweight embedding when HF model is unavailable.

        Produces a non-zero, unit-normalized vector seeded from text hash.
        """
        # Stable 64-bit seed from SHA256 of text
        h = hashlib.sha256(text.encode("utf-8", errors="ignore")).digest()
        seed = int.from_bytes(h[:8], "big", signed=False) % (2**32)
        rng = random.Random(seed)
        vec = [rng.gauss(0.0, 1.0) for _ in range(dim)]
        # Unit normalize to keep cosine similarity meaningful
        norm = math.sqrt(sum(v * v for v in vec))
        if norm == 0:
            return vec
        return [v / norm for v in vec]

    def local_embed(self, text: str) -> list[float]:
        if self._use_fallback or self.local_embedding_model is None:
            return self._fallback_embed(text)
        embedding = self.local_embedding_model.get_text_embedding(text)
        return embedding

    def batch_local_embed(self, text_l: list[str]) -> list[list[float]]:
        if self._use_fallback or self.local_embedding_model is None:
            return [self._fallback_embed(t) for t in text_l]
        embed_documents = self.local_embedding_model.get_text_embedding_batch(
            text_l, show_progress=True
        )
        return embed_documents


if __name__ == "__main__":
    text_list = ["text1", "text2", "text4"]
    embed_agent = EmbedAgent()
    embedding = embed_agent.batch_remote_embed(text_list)
    print(embedding)
    logger.info("Embedding complete.")

    embedding = embed_agent.batch_local_embed(text_list)
    print(embedding)
