# cspeak

Chinese screenplay-to-speech synthesizer. Feed it a screenplay, get an MP3 with distinct voices per character and emotion-aware delivery.

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [Ollama](https://ollama.com) (for the default emotion backend)
- A running [lvoice](https://github.com/llm576049-cell/lvoice) instance for speech synthesis

---

## Setup

### 1. Install Python deps

```bash
cd cspeak
uv sync
```

### 2. Install Ollama + emotion model

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5:3b
```

### 3. Start lvoice

`config.yaml`'s `tts:` section points at an [lvoice](https://github.com/llm576049-cell/lvoice)
service for synthesis. Run it separately (`docker compose up --build` in that
repo) and point `tts.base_url` at it (default: `http://localhost:8000`).

---

## Usage

### Quick test (no audio generated)

```bash
uv run python main.py example_script.txt --dry-run
```

This runs the emotion analyzer and prints what voice + tone each line would use — useful for tuning character config before committing to full TTS synthesis.

### Generate audio

```bash
uv run python main.py example_script.txt -o output.mp3
```

### All options

```
uv run python main.py [SCRIPT] [OPTIONS]

Arguments:
  SCRIPT              Screenplay .txt file

Options:
  -o, --output PATH   Output audio file [default: output.mp3]
  -c, --config PATH   Config file [default: config.yaml]
  -b, --backend TEXT  Emotion backend: ollama | transformers | rule_based | claude
      --base-url      lvoice service URL (overrides config.yaml)
      --dry-run       Print emotion analysis only, skip TTS
```

---

## Writing a screenplay

Create a `.txt` file with this format:

```
[场景：北京，清晨的胡同]

阿强: 你来干什么？
小梅（低声）: 我……我只是想见你一面。
阿强: 不必了。走吧。

[场景：室内，昏暗的灯光下]

老李（严肃地）: 你知道自己在做什么吗？
阿强（哽咽）: 我知道……对不起。
```

| Element | Syntax | Notes |
|---|---|---|
| Scene header | `[场景：...]` | Sets emotion context for subsequent lines |
| Dialogue | `角色名: 台词` | Basic line |
| With stage direction | `角色名（动作）: 台词` | Direction informs emotion analysis |
| Stage direction only | `（旁白文字）` | Skipped — not spoken |
| Comment | `# ...` | Ignored |

---

## Configuring characters

Edit `config.yaml` to assign a voice to each character:

```yaml
characters:
  阿强:
    gender: male
    age: young      # young | middle | old
  小梅:
    gender: female
    age: young
  老李:
    gender: male
    age: old
```

Available voice presets: `young_male`, `middle_male`, `old_male`, `young_female`, `middle_female`, `old_female`, `cantonese_female`.

Unrecognized characters fall back to `young_female`.

---

## Emotion backends

Switch backend in `config.yaml` or with `--backend`:

| Backend | Quality | Speed | Requires |
|---|---|---|---|
| `ollama` | Good | ~3–5 s/line | Ollama + `qwen2.5:3b` |
| `transformers` | Good | slow first load, then fast | `uv sync --extra transformers` |
| `rule_based` | Basic | Instant | Nothing |
| `claude` | Best | Fast (cloud) | `ANTHROPIC_API_KEY` + `uv sync --extra claude` |

### Install optional backends

```bash
# transformers (downloads ~1.1 GB model on first run)
uv sync --extra transformers

# Claude API
uv sync --extra claude
ANTHROPIC_API_KEY=sk-... uv run python main.py script.txt
```

---

## Development

```bash
# lint + format
uv run ruff check --fix . && uv run ruff format .
```
