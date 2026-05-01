import io
import numpy as np
import soundfile as sf
import scipy.io.wavfile as wavfile
from pathlib import Path
from transformers import pipeline as hf_pipeline

MODEL_PATH = Path(__file__).parent.parent.parent / "models" / "whisper"
MODEL_PATH_TTS = Path(__file__).parent.parent.parent / "models" / "tts"

class WhisperSTT:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._pipe = None
        return cls._instance

    def load(self):
        if self._pipe is not None:
            return
            
        if not MODEL_PATH.exists():
            print(f"[Whisper] Warning: Model path {MODEL_PATH} does not exist. STT will not function.")
            return
            
        print(f"[Whisper] Loading model from {MODEL_PATH}...")
        self._pipe = hf_pipeline(
            "automatic-speech-recognition",
            model=str(MODEL_PATH),
            chunk_length_s=30,
            device="cpu"
        )
        print("[Whisper] Ready.")

    def transcribe(self, audio_bytes: bytes, mimetype: str = "audio/webm") -> str:
        if self._pipe is None:
            self.load()
        if self._pipe is None:
            return "Error: Whisper model not loaded."

        try:
            audio_array, sample_rate = sf.read(io.BytesIO(audio_bytes))
            if len(audio_array.shape) > 1:
                audio_array = audio_array.mean(axis=1)
                
            result = self._pipe({"array": audio_array, "sampling_rate": sample_rate})
            return result["text"].strip()
        except Exception as e:
            return f"Error during transcription: {e}"

    def health_check(self) -> dict:
        return {
            "loaded": self._pipe is not None,
            "model_path": str(MODEL_PATH),
            "model_exists": MODEL_PATH.exists()
        }

whisper_stt = WhisperSTT()


class KokoroTTS:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._pipeline = None
        return cls._instance

    def load(self):
        if self._pipeline is not None:
            return
            
        if not MODEL_PATH_TTS.exists():
            print(f"[Kokoro] Warning: Local path {MODEL_PATH_TTS} does not exist. Kokoro will attempt to download weights automatically on first use.")
             
        try:
            from kokoro import KPipeline
            print(f"[Kokoro] Initializing TTS pipeline (lang='a', repo={MODEL_PATH_TTS})...")
            self._pipeline = KPipeline(lang_code='a', repo_id=str(MODEL_PATH_TTS))
            print("[Kokoro] Ready.")
        except Exception as e:
            print(f"[Kokoro] Error loading TTS: {e}")

    def synthesize(self, text: str, voice: str = "af_heart") -> bytes:
        if self._pipeline is None:
            self.load()
        if self._pipeline is None:
            raise RuntimeError("TTS model not loaded or failed to initialize.")

        try:
            generator = self._pipeline(text, voice=voice, speed=1.0)
            all_audio = []
            for _, _, audio in generator:
                all_audio.append(audio)
                
            if not all_audio:
                raise RuntimeError("No audio generated.")
                
            full_audio = np.concatenate(all_audio)
            
            # Default Kokoro sample rate is 24000
            sample_rate = 24000
            
            out_buffer = io.BytesIO()
            wavfile.write(out_buffer, sample_rate, full_audio)
            return out_buffer.getvalue()
        except Exception as e:
            raise RuntimeError(f"Error during TTS synthesis: {e}")

    def health_check(self) -> dict:
        return {
            "loaded": self._pipeline is not None,
            "model_path": str(MODEL_PATH_TTS),
            "model_exists": MODEL_PATH_TTS.exists()
        }

kokoro_tts = KokoroTTS()
