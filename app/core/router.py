import json
import time
from pathlib import Path
from transformers import pipeline

MODEL_PATH = Path(__file__).parent.parent.parent / "models" / "router"

CANDIDATE_LABELS = [
    "personal_knowledge_query",
    "system_tool_execution",
    "general_conversation",
    "document_analysis",
    "image_analysis",
]

CONFIDENCE_THRESHOLD = 0.45
LOG_PATH = Path(__file__).parent.parent.parent / "logs" / "routing.jsonl"

class SemanticRouter:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._classifier = None
            cls._instance._load_time_ms = None
        return cls._instance

    def load(self):
        if self._classifier is not None:
            return
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Router model not found at {MODEL_PATH}. "
                "Run scripts/download_models.sh first."
            )
        print(f"[Router] Loading BART-MNLI from {MODEL_PATH}...")
        start = time.time()
        self._classifier = pipeline(
            "zero-shot-classification",
            model=str(MODEL_PATH),
            device=-1  # CPU
        )
        self._load_time_ms = int((time.time() - start) * 1000)
        print(f"[Router] Ready in {self._load_time_ms}ms")

    def route(self, query: str) -> dict:
        if self._classifier is None:
            self.load()
        result = self._classifier(query, CANDIDATE_LABELS, multi_label=False)

        scores = dict(zip(result["labels"], result["scores"]))
        top_label = result["labels"][0]
        top_score = result["scores"][0]

        if top_score < CONFIDENCE_THRESHOLD:
            top_label = "general_conversation"

        routing_decision = {
            "route": top_label,
            "confidence": round(top_score, 4),
            "all_scores": {k: round(v, 4) for k, v in scores.items()},
            "query_preview": query[:80],
            "timestamp": time.time(),
        }

        self._log(routing_decision)
        return routing_decision

    def _log(self, decision: dict):
        try:
            LOG_PATH.parent.mkdir(exist_ok=True)
            with open(LOG_PATH, "a") as f:
                f.write(json.dumps(decision) + "\n")
        except Exception:
            pass

    def health_check(self) -> dict:
        return {
            "loaded": self._classifier is not None,
            "model_path": str(MODEL_PATH),
            "model_exists": MODEL_PATH.exists(),
            "load_time_ms": self._load_time_ms,
        }

semantic_router = SemanticRouter()
