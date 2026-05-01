import numpy as np
from pathlib import Path
from transformers import AutoTokenizer, AutoModel
import torch
import torch.nn.functional as F

MODEL_PATH = Path(__file__).parent.parent.parent / "models" / "embedder"

class Embedder:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._model = None
            cls._instance._tokenizer = None
        return cls._instance

    @property
    def embedding_dim(self) -> int:
        if self._model is None:
            self.load()
        return self._model.config.hidden_size

    def load(self):
        if self._model is None:
            print(f"[Embedder] Loading from {MODEL_PATH}...")
            self._tokenizer = AutoTokenizer.from_pretrained(str(MODEL_PATH))
            self._model = AutoModel.from_pretrained(str(MODEL_PATH))
            self._model.eval()
            print("[Embedder] Ready.")

    def _mean_pool(self, model_output, attention_mask):
        token_embeddings = model_output.last_hidden_state
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

    def encode_texts(self, texts: list[str]) -> list[list[float]]:
        if self._model is None:
            self.load()
            
        all_embeddings = []
        batch_size = 32
        
        with torch.no_grad():
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i+batch_size]
                
                # Tokenize
                encoded_input = self._tokenizer(
                    batch_texts, 
                    padding=True, 
                    truncation=True, 
                    max_length=512, 
                    return_tensors='pt'
                )
                
                # Forward pass
                model_output = self._model(**encoded_input)
                
                # Pool and normalize
                embeddings = self._mean_pool(model_output, encoded_input['attention_mask'])
                embeddings = F.normalize(embeddings, p=2, dim=1)
                
                all_embeddings.extend(embeddings.tolist())
                
        return all_embeddings

    def encode_query(self, query: str) -> list[float]:
        if self._model is None:
            self.load()
            
        with torch.no_grad():
            encoded_input = self._tokenizer(
                [query], 
                padding=True, 
                truncation=True, 
                max_length=512, 
                return_tensors='pt'
            )
            model_output = self._model(**encoded_input)
            embeddings = self._mean_pool(model_output, encoded_input['attention_mask'])
            embeddings = F.normalize(embeddings, p=2, dim=1)
            
        return embeddings[0].tolist()

    def health_check(self) -> dict:
        loaded = self._model is not None
        dim = self.embedding_dim if loaded else None
        
        return {
            "loaded": loaded,
            "embedding_dim": dim,
            "model_path": str(MODEL_PATH),
            "model_exists": MODEL_PATH.exists()
        }

embedder = Embedder()
