"""Dataset contracts that fail before untrusted public files enter the database."""

from __future__ import annotations

import csv
import hashlib
import io
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class FileContract:
    """Expected filename, header fields, and text encoding for one CSV."""

    name: str
    required_columns: frozenset[str]
    encoding: str = "utf-8"


@dataclass(frozen=True, slots=True)
class DatasetContract:
    """Named collection of source files that must arrive together."""

    name: str
    files: tuple[FileContract, ...]


@dataclass(frozen=True, slots=True)
class FileCheck:
    """Deterministic verification evidence for one source file."""

    name: str
    path: Path
    ok: bool
    size_bytes: int | None
    sha256: str | None
    columns: tuple[str, ...]
    errors: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class VerificationReport:
    """Aggregated verification result for a dataset contract."""

    dataset: str
    root: Path
    files: tuple[FileCheck, ...]

    @property
    def ok(self) -> bool:
        return all(file.ok for file in self.files)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify_file(root: Path, contract: FileContract) -> FileCheck:
    path = root / contract.name
    if not path.is_file():
        return FileCheck(
            name=contract.name,
            path=path,
            ok=False,
            size_bytes=None,
            sha256=None,
            columns=(),
            errors=(f"missing file: {contract.name}",),
        )

    size_bytes = path.stat().st_size
    sha256 = _sha256(path)
    try:
        with path.open("rb") as handle:
            header_bytes = handle.readline()
        header_text = header_bytes.decode(contract.encoding)
    except UnicodeDecodeError as error:
        return FileCheck(
            name=contract.name,
            path=path,
            ok=False,
            size_bytes=size_bytes,
            sha256=sha256,
            columns=(),
            errors=(f"cannot decode as {contract.encoding}: {error}",),
        )

    try:
        columns = tuple(next(csv.reader(io.StringIO(header_text)), ()))
    except csv.Error as error:
        return FileCheck(
            name=contract.name,
            path=path,
            ok=False,
            size_bytes=size_bytes,
            sha256=sha256,
            columns=(),
            errors=(f"invalid CSV header: {error}",),
        )

    errors: list[str] = []
    duplicates = sorted({column for column in columns if columns.count(column) > 1})
    if duplicates:
        errors.append(f"duplicate header columns: {', '.join(duplicates)}")
    missing = sorted(contract.required_columns.difference(columns))
    if missing:
        errors.append(f"missing required columns: {', '.join(missing)}")
    if not columns:
        errors.append("empty CSV header")

    return FileCheck(
        name=contract.name,
        path=path,
        ok=not errors,
        size_bytes=size_bytes,
        sha256=sha256,
        columns=columns,
        errors=tuple(errors),
    )


def verify_dataset(root: Path, contract: DatasetContract) -> VerificationReport:
    """Verify every contracted CSV without loading data rows into memory."""

    normalized_root = Path(root)
    return VerificationReport(
        dataset=contract.name,
        root=normalized_root,
        files=tuple(_verify_file(normalized_root, file) for file in contract.files),
    )


OLIST_CONTRACT = DatasetContract(
    name="olist",
    files=(
        FileContract(
            "olist_customers_dataset.csv",
            frozenset(
                {
                    "customer_id",
                    "customer_unique_id",
                    "customer_zip_code_prefix",
                    "customer_city",
                    "customer_state",
                }
            ),
        ),
        FileContract(
            "olist_geolocation_dataset.csv",
            frozenset(
                {
                    "geolocation_zip_code_prefix",
                    "geolocation_lat",
                    "geolocation_lng",
                    "geolocation_city",
                    "geolocation_state",
                }
            ),
        ),
        FileContract(
            "olist_order_items_dataset.csv",
            frozenset(
                {
                    "order_id",
                    "order_item_id",
                    "product_id",
                    "seller_id",
                    "shipping_limit_date",
                    "price",
                    "freight_value",
                }
            ),
        ),
        FileContract(
            "olist_order_payments_dataset.csv",
            frozenset(
                {
                    "order_id",
                    "payment_sequential",
                    "payment_type",
                    "payment_installments",
                    "payment_value",
                }
            ),
        ),
        FileContract(
            "olist_order_reviews_dataset.csv",
            frozenset(
                {
                    "review_id",
                    "order_id",
                    "review_score",
                    "review_creation_date",
                    "review_answer_timestamp",
                }
            ),
        ),
        FileContract(
            "olist_orders_dataset.csv",
            frozenset(
                {
                    "order_id",
                    "customer_id",
                    "order_status",
                    "order_purchase_timestamp",
                    "order_estimated_delivery_date",
                }
            ),
        ),
        FileContract(
            "olist_products_dataset.csv",
            frozenset({"product_id", "product_category_name"}),
        ),
        FileContract(
            "olist_sellers_dataset.csv",
            frozenset({"seller_id", "seller_zip_code_prefix", "seller_city", "seller_state"}),
        ),
        FileContract(
            "product_category_name_translation.csv",
            frozenset({"product_category_name", "product_category_name_english"}),
            encoding="utf-8-sig",
        ),
    ),
)

HILLSTROM_CONTRACT = DatasetContract(
    name="hillstrom",
    files=(
        FileContract(
            "hillstrom.csv",
            frozenset(
                {
                    "recency",
                    "history_segment",
                    "history",
                    "mens",
                    "womens",
                    "zip_code",
                    "newbie",
                    "channel",
                    "segment",
                    "visit",
                    "conversion",
                    "spend",
                }
            ),
        ),
    ),
)
