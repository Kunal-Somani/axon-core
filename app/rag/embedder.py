from sentence_transformers import SentenceTransformer
import numpy as np
from pathlib import Path

MODEL_PATH = Path(__file__).parent.parent.parent / "models" / "embedder"

class Embedder:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._model = None
        return cls._instance

    def load(self):
        if self._model is None:
            print(f"[Embedder] Loading from {MODEL_PATH}...")
            self._model = SentenceTransformer(str(MODEL_PATH))
            print("[Embedder] Ready.")

    def encode_texts(self, texts: list[str]) -> list[list[float]]:
        if self._model is None:
            self.load()
        return self._model.encode(texts, show_progress_bar=False, convert_to_numpy=True).tolist()

    def encode_query(self, query: str) -> list[float]:
        if self._model is None:
            self.load()
        return self._model.encode([query], show_progress_bar=False, convert_to_numpy=True)[0].tolist()

embedder = Embedder()
