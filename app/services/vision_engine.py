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
            cls._instance._captioner = None
            cls._instance._load_time_ms = None
        return cls._instance

    def load(self):
        if self._captioner is not None:
            return
        from transformers import BlipProcessor, BlipForConditionalGeneration
        import torch
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Vision model not found at {MODEL_PATH}. Run scripts/download_models.sh first.")
        print(f"[Vision] Loading BLIP from {MODEL_PATH}...")
        start = time.time()
        self._processor = BlipProcessor.from_pretrained(str(MODEL_PATH))
        self._captioner = BlipForConditionalGeneration.from_pretrained(str(MODEL_PATH))
        self._load_time_ms = int((time.time() - start) * 1000)
        print(f"[Vision] Ready in {self._load_time_ms}ms")

    def describe_image(self, image_bytes: bytes) -> str:
        if self._captioner is None:
            self.load()
        import torch
        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            inputs = self._processor(image, return_tensors="pt")
            with torch.no_grad():
                out = self._captioner.generate(**inputs, max_new_tokens=100)
            return self._processor.decode(out[0], skip_special_tokens=True)
        except Exception as e:
            return f"Image captioning failed: {e}"

    def extract_text_from_image(self, image_bytes: bytes) -> str:
        try:
            image = Image.open(io.BytesIO(image_bytes))
            return pytesseract.image_to_string(image).strip()
        except Exception as e:
            return ""

    def analyze(self, image_bytes: bytes) -> str:
        caption = self.describe_image(image_bytes)
        ocr = self.extract_text_from_image(image_bytes)
        result = f"Image description: {caption}"
        if ocr:
            result += f"\n\nText found in image:\n{ocr}"
        return result

    def health_check(self) -> dict:
        return {
            "loaded": self._captioner is not None,
            "model_path": str(MODEL_PATH),
            "model_exists": MODEL_PATH.exists(),
            "load_time_ms": self._load_time_ms,
        }

vision_engine = VisionEngine()
