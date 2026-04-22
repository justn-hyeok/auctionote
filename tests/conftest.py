import json
from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def list_detail_cases() -> list[str]:
    """expected/*.json 중 detail_ 접두사인 것의 스템 목록."""
    if not (FIXTURES / "expected").exists():
        return []
    return sorted(
        p.stem for p in (FIXTURES / "expected").glob("detail_*.json")
    )


def list_list_cases() -> list[str]:
    if not (FIXTURES / "expected").exists():
        return []
    return sorted(
        p.stem for p in (FIXTURES / "expected").glob("list_*.json")
    )


def load_raw(name: str) -> str:
    return (FIXTURES / "raw" / f"{name}.html").read_text(encoding="utf-8")


def load_expected(name: str) -> dict:
    return json.loads((FIXTURES / "expected" / f"{name}.json").read_text(encoding="utf-8"))
