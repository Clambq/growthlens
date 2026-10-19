"""Download the public Hillstrom experiment data from its named source."""

from __future__ import annotations

import argparse
import shutil
import tempfile
import urllib.request
from pathlib import Path

from growthlens.data_contracts import HILLSTROM_CONTRACT, verify_dataset

HILLSTROM_SOURCE_URL = (
    "http://www.minethatdata.com/"
    "Kevin_Hillstrom_MineThatData_E-MailAnalytics_DataMiningChallenge_2008.03.20.csv"
)


def download(destination: Path, *, overwrite: bool = False) -> Path:
    """Download to a temporary file, validate it, and then move it into place."""

    destination = Path(destination)
    if destination.exists() and not overwrite:
        raise FileExistsError(f"destination already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)

    request = urllib.request.Request(
        HILLSTROM_SOURCE_URL,
        headers={"User-Agent": "GrowthLens/0.1 (+public analytics portfolio)"},
    )
    with tempfile.TemporaryDirectory(dir=destination.parent) as temporary_directory:
        temporary_path = Path(temporary_directory) / HILLSTROM_CONTRACT.files[0].name
        with (
            urllib.request.urlopen(request, timeout=60) as response,
            temporary_path.open("wb") as output,
        ):
            shutil.copyfileobj(response, output)
        report = verify_dataset(temporary_path.parent, HILLSTROM_CONTRACT)
        if not report.ok:
            errors = "; ".join(report.files[0].errors)
            raise ValueError(f"downloaded Hillstrom file failed verification: {errors}")
        temporary_path.replace(destination)
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/raw/hillstrom/hillstrom.csv"),
    )
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    print(download(args.output, overwrite=args.overwrite))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
