import json
import os
import tempfile
from pathlib import Path
from typing import Any


def read(path: Path) -> Any:
    return json.loads(path.read_bytes())


def encode(value: Any, *, compact: bool = False) -> bytes:
    options = {"separators": (",", ":")} if compact else {"indent": 2}
    return (json.dumps(value, ensure_ascii=False, allow_nan=False, **options) + "\n").encode()


def write(path: Path, content: bytes) -> None:
    if path.exists() and path.read_bytes() == content:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(dir=path.parent, delete=False)
    temporary = Path(handle.name)
    try:
        with handle:
            handle.write(content)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
