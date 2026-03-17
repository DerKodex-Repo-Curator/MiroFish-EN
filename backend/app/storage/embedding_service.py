"""
EmbeddingService — embedding via Ollama or OpenAI-compatible API.

Supports two backends:
  - Ollama: /api/embed endpoint (local, nomic-embed-text, 768 dims)
  - OpenAI-compatible: /v1/embeddings endpoint (cloud or local)

Auto-detects backend from EMBEDDING_BASE_URL.
"""

import time
import logging
from typing import List, Optional

import requests

from ..config import Config

logger = logging.getLogger('mirofish.embedding')


class EmbeddingService:
    """Generate embeddings using Ollama or OpenAI-compatible API."""

    def __init__(
        self,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        max_retries: int = 3,
        timeout: int = 30,
    ):
        self.model = model or Config.EMBEDDING_MODEL
        self.base_url = (base_url or Config.EMBEDDING_BASE_URL).rstrip('/')
        self.api_key = api_key or Config.EMBEDDING_API_KEY
        self.max_retries = max_retries
        self.timeout = timeout

        # Auto-detect backend from URL
        self._use_openai = '/v1' in self.base_url or 'openai.com' in self.base_url

        if self._use_openai:
            self._embed_url = f"{self.base_url}/embeddings"
        else:
            self._embed_url = f"{self.base_url}/api/embed"

        # Dimensions: explicit config > auto-detect from first request
        self._dimensions = Config.EMBEDDING_DIMENSIONS or None
        self._detected_dimensions: Optional[int] = None

        # Simple in-memory cache (text -> embedding vector)
        self._cache: dict[str, List[float]] = {}
        self._cache_max_size = 2000

    @property
    def dimensions(self) -> int:
        """Return embedding dimensions (configured or detected)."""
        if self._dimensions:
            return self._dimensions
        if self._detected_dimensions:
            return self._detected_dimensions
        # Fallback defaults by known model
        if 'nomic' in self.model:
            return 768
        if 'text-embedding-3-small' in self.model:
            return 1536
        if 'text-embedding-3-large' in self.model:
            return 3072
        return 1536  # safe default for OpenAI models

    def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        if not text or not text.strip():
            raise EmbeddingError("Cannot embed empty text")

        text = text.strip()

        if text in self._cache:
            return self._cache[text]

        vectors = self._request_embeddings([text])
        vector = vectors[0]

        self._cache_put(text, vector)
        return vector

    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Generate embeddings for multiple texts with caching."""
        if not texts:
            return []

        results: List[Optional[List[float]]] = [None] * len(texts)
        uncached_indices: List[int] = []
        uncached_texts: List[str] = []

        for i, text in enumerate(texts):
            text = text.strip() if text else ""
            if text in self._cache:
                results[i] = self._cache[text]
            elif text:
                uncached_indices.append(i)
                uncached_texts.append(text)
            else:
                results[i] = [0.0] * self.dimensions

        if uncached_texts:
            all_vectors: List[List[float]] = []
            for start in range(0, len(uncached_texts), batch_size):
                batch = uncached_texts[start:start + batch_size]
                vectors = self._request_embeddings(batch)
                all_vectors.extend(vectors)

            for idx, vec, text in zip(uncached_indices, all_vectors, uncached_texts):
                results[idx] = vec
                self._cache_put(text, vec)

        return results  # type: ignore

    def _request_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Route to Ollama or OpenAI endpoint based on auto-detected backend."""
        if self._use_openai:
            return self._request_openai(texts)
        else:
            return self._request_ollama(texts)

    def _request_openai(self, texts: List[str]) -> List[List[float]]:
        """Call OpenAI-compatible /v1/embeddings endpoint."""
        payload = {
            "model": self.model,
            "input": texts,
        }

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        return self._do_request(payload, headers, self._parse_openai_response, len(texts))

    def _request_ollama(self, texts: List[str]) -> List[List[float]]:
        """Call Ollama /api/embed endpoint."""
        payload = {
            "model": self.model,
            "input": texts,
        }

        return self._do_request(payload, {}, self._parse_ollama_response, len(texts))

    def _do_request(self, payload, headers, parser, expected_count) -> List[List[float]]:
        """HTTP POST with retry and exponential backoff."""
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self._embed_url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                data = response.json()

                embeddings = parser(data)
                if len(embeddings) != expected_count:
                    raise EmbeddingError(
                        f"Expected {expected_count} embeddings, got {len(embeddings)}"
                    )

                # Auto-detect dimensions from first successful response
                if embeddings and not self._detected_dimensions:
                    self._detected_dimensions = len(embeddings[0])
                    logger.info(f"Detected embedding dimensions: {self._detected_dimensions}")

                return embeddings

            except requests.exceptions.ConnectionError as e:
                last_error = e
                logger.warning(
                    f"Embedding connection failed (attempt {attempt + 1}/{self.max_retries}): {e}"
                )
            except requests.exceptions.Timeout as e:
                last_error = e
                logger.warning(
                    f"Embedding request timed out (attempt {attempt + 1}/{self.max_retries})"
                )
            except requests.exceptions.HTTPError as e:
                last_error = e
                logger.error(f"Embedding HTTP error: {e.response.status_code} - {e.response.text}")
                if e.response.status_code >= 500:
                    pass  # retry
                else:
                    raise EmbeddingError(f"Embedding request failed: {e}") from e
            except (KeyError, ValueError) as e:
                raise EmbeddingError(f"Invalid embedding response: {e}") from e

            if attempt < self.max_retries - 1:
                wait = 2 ** attempt
                logger.info(f"Retrying in {wait}s...")
                time.sleep(wait)

        raise EmbeddingError(
            f"Embedding failed after {self.max_retries} retries: {last_error}"
        )

    @staticmethod
    def _parse_openai_response(data: dict) -> List[List[float]]:
        """Extract embeddings from OpenAI response format: {data: [{embedding: [...]}]}"""
        items = data.get("data", [])
        items.sort(key=lambda x: x.get("index", 0))
        return [item["embedding"] for item in items]

    @staticmethod
    def _parse_ollama_response(data: dict) -> List[List[float]]:
        """Extract embeddings from Ollama response format: {embeddings: [[...]]}"""
        return data.get("embeddings", [])

    def _cache_put(self, text: str, vector: List[float]) -> None:
        """Add to cache, evicting oldest entries if full."""
        if len(self._cache) >= self._cache_max_size:
            keys_to_remove = list(self._cache.keys())[:self._cache_max_size // 10]
            for key in keys_to_remove:
                del self._cache[key]
        self._cache[text] = vector

    def health_check(self) -> bool:
        """Check if embedding endpoint is reachable."""
        try:
            vec = self.embed("health check")
            return len(vec) > 0
        except Exception:
            return False


class EmbeddingError(Exception):
    """Raised when embedding generation fails."""
    pass
