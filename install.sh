#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COSYVOICE_DIR="$SCRIPT_DIR/CosyVoice"
MATCHA_DIR="$COSYVOICE_DIR/third_party/Matcha-TTS"
MODEL_DIR="$SCRIPT_DIR/pretrained_models/CosyVoice2-0.5B"
MODEL_ID="iic/CosyVoice2-0.5B"

# Pinned commits — change these deliberately when upgrading CosyVoice
COSYVOICE_COMMIT="ace7c47f41bbd303aa6bf1ea80e6f9fbd595cd40"
MATCHA_COMMIT="dd9105b34bf2be2230f4aa1e4769fb586a3c824e"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
log()  { echo -e "${GREEN}[install]${NC} $*"; }
warn() { echo -e "${YELLOW}[warn]${NC} $*"; }
die()  { echo -e "${RED}[error]${NC} $*" >&2; exit 1; }

# ── 1. Prerequisites ────────────────────────────────────────────────────────
log "Checking prerequisites..."
command -v uv  >/dev/null 2>&1 || die "uv not found. Install: https://docs.astral.sh/uv/"
command -v git >/dev/null 2>&1 || die "git not found."

# ── 2. Python + Python deps ─────────────────────────────────────────────────
log "Installing Python 3.13..."
uv python install 3.13

log "Installing Python dependencies..."
uv sync --python 3.13 --extra tts

# ── 3. CosyVoice ────────────────────────────────────────────────────────────
if [ ! -d "$COSYVOICE_DIR/.git" ]; then
    log "Cloning CosyVoice..."
    git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git "$COSYVOICE_DIR"
fi

log "Pinning CosyVoice to $COSYVOICE_COMMIT..."
git -C "$COSYVOICE_DIR" checkout "$COSYVOICE_COMMIT"

log "Pinning Matcha-TTS to $MATCHA_COMMIT..."
git -C "$MATCHA_DIR" checkout "$MATCHA_COMMIT"

log "Writing CosyVoice .pth files into venv..."
SITE=$(uv run python -c "import site; print(site.getsitepackages()[0])")
echo "$COSYVOICE_DIR"  > "$SITE/cosyvoice.pth"
echo "$MATCHA_DIR"     > "$SITE/matcha.pth"

# ── 4. Model weights ────────────────────────────────────────────────────────
if [ -f "$MODEL_DIR/cosyvoice2.yaml" ]; then
    log "Model weights already present, skipping download."
else
    log "Downloading $MODEL_ID (~2 GB)..."
    uv run python - <<EOF
from modelscope import snapshot_download
snapshot_download("$MODEL_ID", local_dir="$MODEL_DIR")
EOF
fi

# ── 5. Ollama emotion model ─────────────────────────────────────────────────
if command -v ollama >/dev/null 2>&1; then
    log "Pulling Ollama emotion model (qwen2.5:3b)..."
    ollama pull qwen2.5:3b
else
    warn "Ollama not found — install from https://ollama.com, then run: ollama pull qwen2.5:3b"
    warn "Or switch to another emotion backend in config.yaml (rule_based requires nothing)."
fi

# ── Done ────────────────────────────────────────────────────────────────────
log "Setup complete. Try:"
log "  uv run python main.py example_script.txt --dry-run"
log "  uv run python main.py example_script.txt -o output.mp3"
