import json

from . import config as C

PATH = C.REPORTS_DIR / "metrics.json"


def update(key: str, payload: dict) -> None:
    C.REPORTS_DIR.mkdir(exist_ok=True)
    data = json.loads(PATH.read_text()) if PATH.exists() else {}
    data[key] = payload
    PATH.write_text(json.dumps(data, indent=2))


def load() -> dict:
    return json.loads(PATH.read_text()) if PATH.exists() else {}
