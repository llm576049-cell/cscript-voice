from __future__ import annotations

import json
import re
from collections import defaultdict

from parser.script_parser import ParsedLine

_MALE_TOKENS = re.compile(r"男|哥|叔|爷|爸|爹|兄|先生|老头|大爷|父|伯|舅")
_FEMALE_TOKENS = re.compile(r"女|姐|妹|妈|娘|奶|姑|嫂|小姐|阿姨|母|婶|嫂|姥")
_OLD_TOKENS = re.compile(r"爷|奶|老|姥|爹|爸爸|妈妈|大爷|老头|老太")
_YOUNG_TOKENS = re.compile(r"^小.{1,2}$|^阿.{1,2}$|^[A-Za-z]+$")

_LLM_TMPL = (
    "判断以下角色的性别和年龄段，只返回JSON数组，不要其他文字。\n"
    "gender必须是: male | female\n"
    "age必须是: young | middle | old\n\n"
    "{entries}\n\n"
    '每个对象格式：{{"name":"...","gender":"...","age":"..."}}'
)

_RULE_BASED_BACKENDS = {"rule_based"}


def _rule_infer(name: str) -> dict | None:
    """Return {gender, age} from name patterns, or None if ambiguous."""
    gender: str | None = None
    age: str | None = None

    if _MALE_TOKENS.search(name):
        gender = "male"
    elif _FEMALE_TOKENS.search(name):
        gender = "female"

    if _OLD_TOKENS.search(name):
        age = "old"
    elif _YOUNG_TOKENS.search(name):
        age = "young"

    if gender is None and age is None:
        return None
    return {"gender": gender or "female", "age": age or "young"}


def _llm_infer(
    unknown: dict[str, list[ParsedLine]], backend: str, cfg: dict
) -> dict[str, dict]:
    """Query the configured LLM backend to infer gender/age for ambiguous names."""
    entries = "\n".join(
        f"角色：{name}，台词示例：{'；'.join(ln.text for ln in lines[:3])}"
        for name, lines in unknown.items()
    )
    prompt = _LLM_TMPL.format(entries=entries)

    try:
        if backend == "ollama":
            import httpx

            host = cfg.get("ollama", {}).get("host", "http://localhost:11434").rstrip("/")
            model = cfg.get("ollama", {}).get("model", "qwen2.5:3b")
            resp = httpx.post(
                f"{host}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                },
                timeout=60.0,
            )
            resp.raise_for_status()
            data = json.loads(resp.json()["response"])

        elif backend == "claude":
            import os
            import anthropic

            model = cfg.get("claude", {}).get("model", "claude-haiku-4-5-20251001")
            client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
            msg = client.messages.create(
                model=model,
                max_tokens=256,
                messages=[{"role": "user", "content": prompt}],
            )
            data = json.loads(msg.content[0].text)

        elif backend == "transformers":
            # transformers is classification-only; skip LLM inference
            return {}

        else:
            return {}

        if not isinstance(data, list):
            return {}
        return {
            item["name"]: {"gender": item.get("gender", "female"), "age": item.get("age", "young")}
            for item in data
            if isinstance(item, dict) and "name" in item
        }
    except Exception:
        return {}


def infer_characters(
    lines: list[ParsedLine],
    existing_cfg: dict,
    analyzer_cfg: dict,
) -> dict[str, dict]:
    """Return inferred {gender, age} for characters not already in existing_cfg.

    Rule-based heuristics run first; ambiguous names are sent to the LLM backend
    unless the backend is rule_based (in which case they default to young_female).
    """
    # Group dialogue lines by character, skip already-configured ones
    char_lines: dict[str, list[ParsedLine]] = defaultdict(list)
    for ln in lines:
        if ln.character and not ln.is_scene and ln.character not in existing_cfg:
            char_lines[ln.character].append(ln)

    if not char_lines:
        return {}

    inferred: dict[str, dict] = {}
    ambiguous: dict[str, list[ParsedLine]] = {}

    for name, lns in char_lines.items():
        result = _rule_infer(name)
        if result is not None:
            inferred[name] = result
        else:
            ambiguous[name] = lns

    backend = analyzer_cfg.get("backend", "rule_based")
    if ambiguous and backend not in _RULE_BASED_BACKENDS:
        llm_results = _llm_infer(ambiguous, backend, analyzer_cfg)
        inferred.update(llm_results)

    return inferred
