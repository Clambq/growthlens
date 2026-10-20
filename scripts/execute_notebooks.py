"""Execute all portfolio notebooks in clean kernels without rewriting sources."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="growthlens-jupyter-") as runtime:
        runtime_root = Path(runtime)
        os.environ["IPYTHONDIR"] = str(runtime_root / "ipython")
        os.environ["JUPYTER_CONFIG_DIR"] = str(runtime_root / "config")
        os.environ["JUPYTER_DATA_DIR"] = str(runtime_root / "data")
        for path in sorted((ROOT / "notebooks").glob("*.ipynb")):
            notebook = nbformat.read(path, as_version=4)
            NotebookClient(
                notebook,
                timeout=180,
                kernel_name="python3",
                resources={"metadata": {"path": str(ROOT)}},
            ).execute()
            print(f"executed {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
