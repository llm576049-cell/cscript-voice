# cspeak

Chinese screenplay-to-speech synthesizer. Reads a screenplay text file, analyzes the emotion of each dialogue line, and generates a single audio file using CosyVoice 2 with emotion-aware voice synthesis.

## Purpose

Convert Chinese screenplays into narrated audio with:
- Multiple distinct voices per character (male/female, young/middle/old)
- Emotion-aware delivery — happiness, sadness, anger, fear, etc. reflected in the spoken tone
- Fully local inference (no mandatory cloud services)

## Stack

| Layer | Choice | Notes |
|---|---|---|
| TTS | CosyVoice 2 (`CosyVoice2-0.5B`) | Local, instruct-mode for emotion |
| Emotion analysis | Configurable (see below) | Ollama default |
| Audio assembly | pydub | Stitches WAV clips, exports MP3 |
| CLI | typer | |
| Package manager | uv | Run `uv sync` to install deps |

## Project layout

```
main.py                      # CLI entry point
config.yaml                  # all runtime config lives here
example_script.txt           # sample screenplay
parser/script_parser.py      # parses screenplay → ParsedLine list
analyzer/
  base.py                    # EmotionResult dataclass + abstract interface
  rule_based.py              # keyword dict, no ML (instant, weakest)
  ollama.py                  # local LLM via Ollama HTTP API (default)
  transformers.py            # xlm-roberta zero-shot (offline, ~1.1 GB download)
  claude.py                  # Anthropic API (optional, needs ANTHROPIC_API_KEY)
  __init__.py                # create_analyzer() factory
voice/
  manager.py                 # maps character + emotion → CosyVoice instruct string
  profiles.yaml              # voice presets: young/middle/old × male/female
tts/cosyvoice_tts.py         # thin wrapper around CosyVoice2.inference_instruct2()
audio/assembler.py           # pydub concat with scene-aware pause lengths
```

## Screenplay format

```
[场景：北京，清晨的胡同]       ← scene header (sets context for emotion analysis)

角色名: 台词                   ← basic dialogue
角色名（动作）: 台词            ← dialogue with inline stage direction
（旁白）                       ← pure stage direction — skipped, not spoken
# comment                     ← ignored
```

## Emotion system

All backends return `EmotionResult(emotion, intensity)`:

- **emotion**: `happy | sad | angry | fearful | tender | surprised | serious | neutral`
- **intensity**: `low | medium | high`

This is mapped to a Chinese instruct string sent to CosyVoice 2, e.g.:
`"用悲伤的语气，像年迈的男性说话，声音低沉沙哑"`

## Config

Everything is in `config.yaml`. Key sections:

```yaml
emotion_analyzer:
  backend: ollama        # switch here: ollama | transformers | rule_based | claude

characters:
  角色名:
    gender: male         # male | female
    age: young           # young | middle | old

tts:
  model_path: pretrained_models/CosyVoice2-0.5B
```

## Common commands

```bash
# install base deps
uv sync

# install transformers backend (downloads ~1.1 GB model on first run)
uv sync --extra transformers

# install Claude backend
uv sync --extra claude

# dry-run: inspect emotion analysis without generating audio
uv run python main.py example_script.txt --dry-run

# generate audio
uv run python main.py example_script.txt -o output.mp3

# override backend at runtime
uv run python main.py script.txt --backend rule_based --dry-run

# install CosyVoice2 into the managed venv (do this once after cloning CosyVoice)
uv pip install -e /path/to/CosyVoice'[all]'
```

## One-time setup (CosyVoice 2 + model)

```bash
# 1. clone CosyVoice and install into this venv
git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git
uv pip install -e CosyVoice'[all]'

# 2. download CosyVoice2-0.5B model weights (~2 GB)
uv run python - <<'EOF'
from modelscope import snapshot_download
snapshot_download('iic/CosyVoice2-0.5B', local_dir='pretrained_models/CosyVoice2-0.5B')
EOF

# 3. install Ollama + pull default model (for emotion analysis)
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5:3b
```

## Hardware notes

Developed on Intel N100, 16 GB RAM, integrated GPU only (no CUDA).
- CosyVoice 2 runs CPU-only — expect ~5–15 s per dialogue line
- Ollama with `qwen2.5:3b` is the recommended emotion backend for this hardware
- `qwen2.5:7b` fits in RAM but is noticeably slower; `3b` is the sweet spot

## Adding a new emotion backend

1. Create `analyzer/your_backend.py` with a class extending `EmotionAnalyzer`
2. Implement `analyze(text, context, scene) -> EmotionResult`
3. Register it in `analyzer/__init__.py` `create_analyzer()` factory
4. Add config block under `emotion_analyzer:` in `config.yaml`
