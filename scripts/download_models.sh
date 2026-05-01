#!/bin/bash
set -e

echo "=== Axon Model Downloader ==="
echo "This will download ~6.5GB of model weights. Ensure you have enough disk space."
echo ""

pip install -q huggingface_hub

# Model 1: Sentence Embedder
if [ ! -f "models/embedder/config.json" ]; then
  echo "[1/6] Downloading all-MiniLM-L6-v2 (embedding model)..."
  python3 -c "
from huggingface_hub import snapshot_download
snapshot_download(repo_id='sentence-transformers/all-MiniLM-L6-v2', local_dir='./models/embedder', ignore_patterns=['*.h5','*.ot','*.msgpack','flax_model*','tf_model*'])
print('Embedder downloaded.')
"
else
  echo "[1/6] Embedder already present, skipping."
fi

# Model 2: Zero-shot Router
if [ ! -f "models/router/config.json" ]; then
  echo "[2/6] Downloading facebook/bart-large-mnli (semantic router)..."
  python3 -c "
from huggingface_hub import snapshot_download
snapshot_download(repo_id='facebook/bart-large-mnli', local_dir='./models/router', ignore_patterns=['*.h5','*.ot','*.msgpack','flax_model*','tf_model*'])
print('Router downloaded.')
"
else
  echo "[2/6] Router already present, skipping."
fi

# Model 3: Vision / Image Captioning
if [ ! -f "models/vision/config.json" ]; then
  echo "[3/6] Downloading vikhyatk/moondream2 (vision model)..."
  python3 -c "
from huggingface_hub import snapshot_download
snapshot_download(repo_id='vikhyatk/moondream2', local_dir='./models/vision',
  ignore_patterns=['*.h5','*.ot','*.msgpack','flax_model*','tf_model*'])
print('moondream2 downloaded.')
"
else
  echo "[3/6] Vision model already present, skipping."
fi

# Model 4: LLM (Phi-3 GGUF)
if [ ! -f "models/llm/Phi-3-mini-4k-instruct-q4.gguf" ]; then
  echo "[4/6] Downloading Phi-3-mini-4k-instruct GGUF (local LLM)..."
  python3 -c "
from huggingface_hub import hf_hub_download
hf_hub_download(
  repo_id='microsoft/Phi-3-mini-4k-instruct-gguf',
  filename='Phi-3-mini-4k-instruct-q4.gguf',
  local_dir='./models/llm'
)
print('LLM downloaded.')
"
else
  echo "[4/6] LLM already present, skipping."
fi

# Model 5: Cross-Encoder Reranker
if [ ! -f "models/reranker/config.json" ]; then
  echo "[5/6] Downloading cross-encoder/ms-marco-MiniLM-L-6-v2 (reranker)..."
  python3 -c "
from huggingface_hub import snapshot_download
snapshot_download(repo_id='cross-encoder/ms-marco-MiniLM-L-6-v2', local_dir='./models/reranker',
  ignore_patterns=['*.h5','*.ot','*.msgpack','flax_model*','tf_model*'])
print('Reranker downloaded.')
"
else
  echo "[5/6] Reranker already present, skipping."
fi

# Model 6: Whisper STT
if [ ! -f "models/whisper/config.json" ]; then
  echo "[6/6] Downloading openai/whisper-tiny.en (speech-to-text)..."
  python3 -c "
from huggingface_hub import snapshot_download
snapshot_download(repo_id='openai/whisper-tiny.en', local_dir='./models/whisper',
  ignore_patterns=['*.h5','*.ot','*.msgpack','flax_model*','tf_model*'])
print('Whisper downloaded.')
"
else
  echo "[6/6] Whisper already present, skipping."
fi

echo ""
echo "NOTE: Kokoro TTS model will be downloaded automatically on first use by the kokoro library."
echo "=== All models ready (~6.5GB total) ==="
