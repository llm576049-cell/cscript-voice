# cspeak

Chinese screenplay-to-speech synthesizer. Reads a screenplay text file, analyzes the emotion of each dialogue line, and generates a single audio file using an external TTS service with emotion-aware voice synthesis.

## Purpose

Convert Chinese screenplays into narrated audio with:
- Multiple distinct voices per character (male/female, young/middle/old)
- Emotion-aware delivery — happiness, sadness, anger, fear, etc. reflected in the spoken tone

## Stack

| Layer | Choice | Notes |
|---|---|---|
| TTS | [lvoice](https://github.com/llm576049-cell/lvoice) | External HTTP service, instruct-mode for emotion |
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
  manager.py                 # maps character + emotion → lvoice instruct string
  profiles.yaml              # voice presets: young/middle/old × male/female
  assets/                    # reference WAV clips used for zero-shot cloning
tts/lvoice_tts.py            # HTTP client for lvoice's /v1/tts/instruct endpoint
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

This is mapped to a Chinese instruct string sent to lvoice's `/v1/tts/instruct` endpoint, e.g.:
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
  backend: lvoice
  base_url: http://localhost:8000
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

# point at a non-default lvoice instance
uv run python main.py script.txt --base-url http://other-host:8000
```

## One-time setup

```bash
# 1. start lvoice separately (see https://github.com/llm576049-cell/lvoice)
#    e.g. `docker compose up --build` inside that repo

# 2. install Ollama + pull default model (for emotion analysis)
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5:3b
```

## Hardware notes

- Ollama with `qwen2.5:3b` is the recommended emotion backend for this hardware
- `qwen2.5:7b` fits in RAM but is noticeably slower; `3b` is the sweet spot

## Adding a new emotion backend

1. Create `analyzer/your_backend.py` with a class extending `EmotionAnalyzer`
2. Implement `analyze(text, context, scene) -> EmotionResult`
3. Register it in `analyzer/__init__.py` `create_analyzer()` factory
4. Add config block under `emotion_analyzer:` in `config.yaml`
