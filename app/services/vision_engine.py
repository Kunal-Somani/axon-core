import io
import time
from pathlib import Path
from PIL import Image
import pytesseract

MODEL_PATH = Path(__file__).parent.parent.parent / "models" / "vision"

class VisionEngine:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._model = None
            cls._instance._tokenizer = None
            cls._instance._load_time_ms = None
        return cls._instance

    def load(self):
        if self._model is not None:
            return
        from transformers import AutoModelForCausalLM, AutoTokenizer
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Vision model not found at {MODEL_PATH}. Run scripts/download_models.sh first.")
        print(f"[Vision] Loading moondream2 from {MODEL_PATH}...")
        start = time.time()
        self._tokenizer = AutoTokenizer.from_pretrained(str(MODEL_PATH), trust_remote_code=True)
        self._model = AutoModelForCausalLM.from_pretrained(str(MODEL_PATH), trust_remote_code=True)
        self._model.eval()
        self._load_time_ms = int((time.time() - start) * 1000)
        print(f"[Vision] Ready in {self._load_time_ms}ms")

    def answer_visual_question(self, image_bytes: bytes, question: str) -> str:
        if self._model is None:
            self.load()
        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            enc_image = self._model.encode_image(image)
            answer = self._model.answer_question(enc_image, question, self._tokenizer)
            return answer
        except Exception as e:
            return f"Visual QA failed: {e}"

    def extract_text_from_image(self, image_bytes: bytes) -> str:
        try:
            image = Image.open(io.BytesIO(image_bytes))
            return pytesseract.image_to_string(image).strip()
        except Exception as e:
            return ""

    def analyze(self, image_bytes: bytes, user_prompt: str = "") -> str:
        question = user_prompt if user_prompt else "Describe this image in detail."
        vqa_result = self.answer_visual_question(image_bytes, question)
        ocr = self.extract_text_from_image(image_bytes)
        result = f"Visual analysis: {vqa_result}"
        if ocr and ocr not in vqa_result:
            result += f"\n\nText detected in image:\n{ocr}"
        return result

    def health_check(self) -> dict:
        return {
            "loaded": self._model is not None,
            "model_path": str(MODEL_PATH),
            "model_exists": MODEL_PATH.exists(),
            "load_time_ms": self._load_time_ms,
        }

vision_engine = VisionEngine()
