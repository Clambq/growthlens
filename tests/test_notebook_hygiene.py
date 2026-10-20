from __future__ import annotations

import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_notebooks_have_no_absolute_paths_secrets_or_hidden_execution_state() -> None:
    notebook_paths = sorted((PROJECT_ROOT / "notebooks").glob("*.ipynb"))

    assert len(notebook_paths) == 4
    for path in notebook_paths:
        notebook = json.loads(path.read_text(encoding="utf-8"))
        serialized = json.dumps(notebook, ensure_ascii=False)
        assert not re.search(r"[A-Za-z]:[\\/]Users[\\/]", serialized), path.name
        assert "/home/" not in serialized, path.name
        assert "kaggle.json" not in serialized.lower(), path.name
        for cell in notebook["cells"]:
            if cell["cell_type"] == "code":
                assert cell.get("execution_count") is None, path.name
                assert cell.get("outputs", []) == [], path.name


def test_readme_make_commands_reference_existing_targets() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    makefile = (PROJECT_ROOT / "Makefile").read_text(encoding="utf-8")
    declared = {
        target
        for target in re.findall(r"^([a-z][a-z0-9-]+):", makefile, flags=re.MULTILINE)
    }
    referenced = set(re.findall(r"(?:make|mingw32-make) ([a-z][a-z0-9-]+)", readme))

    assert referenced
    assert referenced <= declared
