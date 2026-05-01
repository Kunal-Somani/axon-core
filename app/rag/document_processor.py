import fitz  # pymupdf
import hashlib
import pytesseract
from PIL import Image
import io
from pathlib import Path
from app.rag.embedder import embedder

CHUNK_MAX_TOKENS = 400    # safe margin below 512 embedder limit
CHUNK_OVERLAP_TOKENS = 40 # ~10% overlap for context continuity

# Deprecated: Split on word count is incorrect for transformer models.
def _chunk_text_words(text: str, source: str, page: int = 0) -> list[dict]:
    chunks = []
    words = text.split()
    step = 500 - 50 
    for i in range(0, len(words), step):
        chunk_words = words[i:i + 500]
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

def chunk_text_by_tokens(text: str, source: str, page: int = 0, 
                         max_tokens: int = CHUNK_MAX_TOKENS, overlap_tokens: int = CHUNK_OVERLAP_TOKENS) -> list[dict]:
    tokenizer = embedder._tokenizer
    if tokenizer is None:
        embedder.load()
        tokenizer = embedder._tokenizer

    token_ids = tokenizer.encode(text, add_special_tokens=False)
    chunks = []
    step = max_tokens - overlap_tokens
    
    for i in range(0, len(token_ids), step):
        chunk_ids = token_ids[i : i + max_tokens]
        if len(chunk_ids) < 20:  # skip tiny tail chunks
            continue
        chunk_text = tokenizer.decode(chunk_ids, skip_special_tokens=True)
        chunk_hash = hashlib.md5(chunk_text.encode()).hexdigest()
        chunks.append({
            "content": chunk_text,
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
        all_chunks.extend(chunk_text_by_tokens(text, source=filename, page=page_num))
    return all_chunks

def process_txt(file_bytes: bytes, filename: str) -> list[dict]:
    text = file_bytes.decode("utf-8", errors="ignore")
    return chunk_text_by_tokens(text, source=filename)

def process_image(file_bytes: bytes, filename: str) -> list[dict]:
    try:
        pil_img = Image.open(io.BytesIO(file_bytes))
        ocr_text = pytesseract.image_to_string(pil_img)
        return chunk_text_by_tokens(ocr_text, source=filename)
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
