import fitz  # pymupdf
import hashlib
import pytesseract
from PIL import Image
import io
from pathlib import Path
from app.rag.embedder import embedder

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

def chunk_text(text: str, source: str, page: int = 0) -> list[dict]:
    chunks = []
    words = text.split()
    step = CHUNK_SIZE - CHUNK_OVERLAP
    for i in range(0, len(words), step):
        chunk_words = words[i:i + CHUNK_SIZE]
        if len(chunk_words) < 20:
            continue
        content = " ".join(chunk_words)
        chunk_hash = hashlib.md5(content.encode()).hexdigest()
        chunks.append({
            "content": content,
            "metadata": {
                "source": source,
                "page": page,
                "chunk_index": i // step,
                "hash": chunk_hash,
            }
        })
    return chunks

def process_pdf(file_bytes: bytes, filename: str) -> list[dict]:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    all_chunks = []
    for page_num, page in enumerate(doc):
        text = page.get_text()
        # Also OCR any embedded images on this page
        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            try:
                pil_img = Image.open(io.BytesIO(image_bytes))
                ocr_text = pytesseract.image_to_string(pil_img)
                if ocr_text.strip():
                    text += f"\n[Image {img_index} OCR]: {ocr_text}"
            except Exception:
                pass
        all_chunks.extend(chunk_text(text, source=filename, page=page_num))
    return all_chunks

def process_txt(file_bytes: bytes, filename: str) -> list[dict]:
    text = file_bytes.decode("utf-8", errors="ignore")
    return chunk_text(text, source=filename)

def process_image(file_bytes: bytes, filename: str) -> list[dict]:
    try:
        pil_img = Image.open(io.BytesIO(file_bytes))
        ocr_text = pytesseract.image_to_string(pil_img)
        return chunk_text(ocr_text, source=filename)
    except Exception as e:
        return []

def process_file(file_bytes: bytes, filename: str) -> list[dict]:
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return process_pdf(file_bytes, filename)
    elif ext == ".txt":
        return process_txt(file_bytes, filename)
    elif ext in [".png", ".jpg", ".jpeg"]:
        return process_image(file_bytes, filename)
    else:
        return []
