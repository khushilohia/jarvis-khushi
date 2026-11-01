import yaml
from pathlib import Path

_cfg = None

def _load():
    global _cfg
    if _cfg is None:
        p = Path(__file__).parent.parent / "config.yaml"
        with open(p) as f:
            _cfg = yaml.safe_load(f)
    return _cfg

def get(key, default=None):
    parts = key.split(".")
    d = _load()
    for p in parts:
        if not isinstance(d, dict):
            return default
        d = d.get(p, default)
    return d
