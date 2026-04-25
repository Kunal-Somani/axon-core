#!/bin/bash
set -e

echo "=== Axon Model Downloader ==="
echo "This will download ~4GB of model weights. Ensure you have enough disk space."
echo ""

pip install -q huggingface_hub

# Model 1: Sentence Embedder
if [ ! -f "models/embedder/config.json" ]; then
  echo "[1/4] Downloading all-MiniLM-L6-v2 (embedding model)..."
  python3 -c "
from huggingface_hub import snapshot_download
snapshot_download(repo_id='sentence-transformers/all-MiniLM-L6-v2', local_dir='./models/embedder', ignore_patterns=['*.h5','*.ot','*.msgpack','flax_model*','tf_model*'])
print('Embedder downloaded.')
"
else
  echo "[1/4] Embedder already present, skipping."
fi

# Model 2: Zero-shot Router
if [ ! -f "models/router/config.json" ]; then
  echo "[2/4] Downloading facebook/bart-large-mnli (semantic router)..."
  python3 -c "
from huggingface_hub import snapshot_download
snapshot_download(repo_id='facebook/bart-large-mnli', local_dir='./models/router', ignore_patterns=['*.h5','*.ot','*.msgpack','flax_model*','tf_model*'])
print('Router downloaded.')
"
else
  echo "[2/4] Router already present, skipping."
fi

# Model 3: Vision / Image Captioning
if [ ! -f "models/vision/config.json" ]; then
  echo "[3/4] Downloading Salesforce/blip-image-captioning-base (vision model)..."
  python3 -c "
from huggingface_hub import snapshot_download
snapshot_download(repo_id='Salesforce/blip-image-captioning-base', local_dir='./models/vision', ignore_patterns=['*.h5','*.ot','*.msgpack','flax_model*','tf_model*'])
print('Vision model downloaded.')
"
else
  echo "[3/4] Vision model already present, skipping."
fi

# Model 4: LLM (Phi-3 GGUF)
if [ ! -f "models/llm/Phi-3-mini-4k-instruct-q4.gguf" ]; then
  echo "[4/4] Downloading Phi-3-mini-4k-instruct GGUF (local LLM)..."
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
  echo "[4/4] LLM already present, skipping."
fi

echo ""
echo "=== All models ready ==="
