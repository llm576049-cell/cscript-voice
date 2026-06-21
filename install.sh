#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
log()  { echo -e "${GREEN}[install]${NC} $*"; }
warn() { echo -e "${YELLOW}[warn]${NC} $*"; }
die()  { echo -e "${RED}[error]${NC} $*" >&2; exit 1; }

# ── 1. Prerequisites ────────────────────────────────────────────────────────
log "Checking prerequisites..."
command -v uv >/dev/null 2>&1 || die "uv not found. Install: https://docs.astral.sh/uv/"

# ── 2. Python + Python deps ─────────────────────────────────────────────────
log "Installing Python 3.13..."
uv python install 3.13

log "Installing Python dependencies..."
uv sync --python 3.13

# ── 3. Ollama emotion model ─────────────────────────────────────────────────
if command -v ollama >/dev/null 2>&1; then
    log "Pulling Ollama emotion model (qwen2.5:3b)..."
    ollama pull qwen2.5:3b
else
    warn "Ollama not found — install from https://ollama.com, then run: ollama pull qwen2.5:3b"
    warn "Or switch to another emotion backend in config.yaml (rule_based requires nothing)."
fi

# ── Done ────────────────────────────────────────────────────────────────────
log "Setup complete."
log "Make sure an lvoice instance is running (https://github.com/llm576049-cell/lvoice)"
log "and that config.yaml's tts.base_url points at it. Then try:"
log "  uv run python main.py example_script.txt --dry-run"
log "  uv run python main.py example_script.txt -o output.mp3"
