import re
from dataclasses import dataclass
from pathlib import Path

# [场景：...] or [SCENE: ...]
SCENE_RE = re.compile(r"^\[(.+?)\]$")

# 角色名（动作）: 台词  — optional parenthetical stage direction
DIALOGUE_RE = re.compile(
    r"^([^:：(（#\[\n]+?)"  # character name
    r"(?:[（(]([^）)\n]+)[）)])?"  # optional (stage direction)
    r"\s*[:：]\s*"  # colon separator
    r"(.+)$"  # dialogue text
)

# Pure stage direction lines: （...） or (...)
STAGE_DIR_RE = re.compile(r"^[（(].+[）)]$")


@dataclass
class ParsedLine:
    character: str | None
    text: str
    stage_dir: str | None
    scene: str | None
    line_num: int
    is_scene: bool = False


class ScriptParser:
    def parse(self, path: Path) -> list[ParsedLine]:
        lines: list[ParsedLine] = []
        current_scene: str | None = None

        with open(path, encoding="utf-8") as f:
            for num, raw in enumerate(f, 1):
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue

                m = SCENE_RE.match(line)
                if m:
                    current_scene = m.group(1).strip()
                    lines.append(
                        ParsedLine(
                            character=None,
                            text=current_scene,
                            stage_dir=None,
                            scene=current_scene,
                            line_num=num,
                            is_scene=True,
                        )
                    )
                    continue

                if STAGE_DIR_RE.match(line):
                    continue

                m = DIALOGUE_RE.match(line)
                if m:
                    lines.append(
                        ParsedLine(
                            character=m.group(1).strip(),
                            text=m.group(3).strip(),
                            stage_dir=m.group(2),
                            scene=current_scene,
                            line_num=num,
                        )
                    )

        return lines
