import os
import time
from pathlib import Path
from typing import Generator
from llama_cpp import Llama, LlamaGrammar

MODEL_PATH = Path(__file__).parent.parent.parent / "models" / "llm" / "Phi-3-mini-4k-instruct-q4.gguf"

class LLMEngine:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._llm = None
            cls._instance._load_time_ms = None
        return cls._instance

    def load(self):
        if self._llm is not None:
            return
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"LLM model not found at {MODEL_PATH}. "
                "Run scripts/download_models.sh first."
            )
        print(f"[LLM] Loading Phi-3 from {MODEL_PATH}...")
        start = time.time()
        self._llm = Llama(
            model_path=str(MODEL_PATH),
            n_ctx=4096,
            n_threads=os.cpu_count() or 4,
            n_gpu_layers=0,
            verbose=False,
        )
        self._load_time_ms = int((time.time() - start) * 1000)
        print(f"[LLM] Ready in {self._load_time_ms}ms")

    def generate(self, prompt: str, max_tokens: int = 512, stream: bool = False):
        if self._llm is None:
            self.load()
        if stream:
            return self._stream(prompt, max_tokens)
        output = self._llm(prompt, max_tokens=max_tokens, stop=["<|end|>", "\nUser:", "\nHuman:"])
        return output["choices"][0]["text"].strip()

    def generate_structured(self, prompt: str, grammar_str: str, max_tokens: int = 150) -> str:
        if self._llm is None:
            self.load()
        grammar = LlamaGrammar.from_string(grammar_str)
        output = self._llm(
            prompt,
            max_tokens=max_tokens,
            grammar=grammar,
            stop=["<|end|>"]
        )
        return output["choices"][0]["text"].strip()

    def _stream(self, prompt: str, max_tokens: int) -> Generator[str, None, None]:
        for chunk in self._llm(
            prompt,
            max_tokens=max_tokens,
            stop=["<|end|>", "\nUser:", "\nHuman:"],
            stream=True
        ):
            token = chunk["choices"][0]["text"]
            if token:
                yield token

    def health_check(self) -> dict:
        return {
            "loaded": self._llm is not None,
            "model_path": str(MODEL_PATH),
            "model_exists": MODEL_PATH.exists(),
            "load_time_ms": self._load_time_ms,
        }

llm_engine = LLMEngine()

def build_prompt(query: str, context: str = "", history: list[dict] = []) -> str:
    system = "You are Axon, a helpful, precise AI assistant. Be direct and clear."
    if context:
        system += f"\n\nRelevant context:\n{context}"

    messages = "<|system|>\n" + system + "<|end|>\n"
    for turn in history[-6:]:
        role_tag = "<|user|>" if turn["role"] == "user" else "<|assistant|>"
        messages += f"{role_tag}\n{turn['content']}<|end|>\n"
    messages += f"<|user|>\n{query}<|end|>\n<|assistant|>\n"
    return messages
