from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import typer
import yaml

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
        help="Emotion backend override: ollama | transformers | rule_based | claude",
    ),
    model_path: Optional[str] = typer.Option(
        None, "--model-path", help="CosyVoice2 model directory (overrides config)"
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

    # --- parse ---
    from parser.script_parser import ScriptParser

    lines = ScriptParser().parse(script)
    spoken = [l for l in lines if not l.is_scene and l.character]

    if not spoken:
        typer.echo("No dialogue lines found.", err=True)
        raise typer.Exit(1)

    typer.echo(f"Parsed {len(spoken)} dialogue lines from {script.name}")

    # --- analyze emotions ---
    from analyzer import create_analyzer

    analyzer = create_analyzer(cfg["emotion_analyzer"])
    emotions = analyzer.analyze_batch(spoken)

    # --- voice manager ---
    from voice.manager import VoiceManager

    voice_mgr = VoiceManager(cfg)

    # --- dry-run: just print analysis ---
    if dry_run:
        typer.echo("\n── Emotion Analysis ─────────────────────────────────────")
        for line, emo in zip(spoken, emotions):
            instruct = voice_mgr.build_instruct(line.character, emo)
            profile = voice_mgr.get_profile(line.character)
            typer.echo(
                f"[{line.character}] spk={profile['spk_id']}  "
                f"{emo.emotion}/{emo.intensity}  →  {instruct}"
            )
            typer.echo(f"    {line.text}")
        return

    # --- TTS + assemble ---
    from tts.cosyvoice_tts import CosyVoiceTTS
    from audio.assembler import AudioAssembler

    tts = CosyVoiceTTS(cfg["tts"]["model_path"])
    assembler = AudioAssembler()

    prev_scene: str | None = None

    for i, (line, emo) in enumerate(zip(spoken, emotions)):
        profile = voice_mgr.get_profile(line.character)
        instruct = voice_mgr.build_instruct(line.character, emo)

        typer.echo(
            f"[{i + 1}/{len(spoken)}] {line.character} ({emo.emotion}/{emo.intensity}): "
            f"{line.text[:40]}{'…' if len(line.text) > 40 else ''}"
        )

        wav = tts.synthesize(
            text=line.text,
            spk_id=profile["spk_id"],
            instruct_text=instruct,
        )

        scene_break = (line.scene != prev_scene) and prev_scene is not None
        assembler.add(wav, scene_break=scene_break)
        prev_scene = line.scene

    assembler.export(output)


if __name__ == "__main__":
    app()
