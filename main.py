from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
import yaml

from analyzer import create_analyzer
from audio.assembler import AudioAssembler
from parser.script_parser import ScriptParser
from tts import create_tts
from voice.manager import VoiceManager
import warnings

warnings.filterwarnings("ignore", category=FutureWarning, module="cosyvoice")

app = typer.Typer(help="Chinese screenplay reader with emotion-aware voice synthesis.")


def _load_config(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


@app.command()
def main(
    script: Path = typer.Argument(..., help="Screenplay .txt file"),
    output: Path = typer.Option(
        Path("output.mp3"), "--output", "-o", help="Output audio file"
    ),
    config: Path = typer.Option(
        Path("config.yaml"), "--config", "-c", help="Config file"
    ),
    backend: Optional[str] = typer.Option(
        None,
        "--backend",
        "-b",
        help="Emotion backend: ollama | transformers | rule_based | claude",
    ),
    model_path: Optional[str] = typer.Option(
        None,
        "--model-path",
        help="CosyVoice2 model directory (overrides config)",
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Print emotion analysis, skip TTS"
    ),
) -> None:
    cfg = _load_config(config)

    if backend:
        cfg["emotion_analyzer"]["backend"] = backend
    if model_path:
        cfg["tts"]["model_path"] = model_path

    lines = ScriptParser().parse(script)
    spoken = [ln for ln in lines if not ln.is_scene and ln.character]

    if not spoken:
        typer.echo("No dialogue lines found.", err=True)
        raise typer.Exit(1)

    typer.echo(f"Parsed {len(spoken)} dialogue lines from {script.name}")

    analyzer = create_analyzer(cfg["emotion_analyzer"])
    emotions = analyzer.analyze_batch(spoken)

    voice_mgr = VoiceManager(cfg)

    if dry_run:
        typer.echo("\n── Emotion Analysis ─────────────────────────────────")
        for line, emo in zip(spoken, emotions):
            instruct = voice_mgr.build_instruct(line.character, emo)
            profile = voice_mgr.get_profile(line.character)
            typer.echo(
                f"[{line.character}] ref={profile['ref_wav']}  "
                f"{emo.emotion}/{emo.intensity}  →  {instruct}"
            )
            typer.echo(f"    {line.text}")
        return

    tts = create_tts(cfg["tts"])
    assembler = AudioAssembler()

    prev_scene: str | None = None

    for i, (line, emo) in enumerate(zip(spoken, emotions)):
        profile = voice_mgr.get_profile(line.character)
        instruct = voice_mgr.build_instruct(line.character, emo)

        tail = line.text[:40] + ("…" if len(line.text) > 40 else "")
        typer.echo(
            f"[{i + 1}/{len(spoken)}] {line.character}"
            f" ({emo.emotion}/{emo.intensity}): {tail}"
        )

        wav = tts.synthesize(
            text=line.text,
            ref_wav=profile["ref_wav"],
            instruct_text=instruct,
        )

        scene_break = (line.scene != prev_scene) and prev_scene is not None
        assembler.add(wav, scene_break=scene_break)
        prev_scene = line.scene

    assembler.export(output)


if __name__ == "__main__":
    app()
