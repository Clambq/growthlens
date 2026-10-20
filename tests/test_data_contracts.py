from pathlib import Path

from growthlens.data_contracts import (
    OLIST_CONTRACT,
    DatasetContract,
    FileContract,
    verify_dataset,
)


def _contract(*required_columns: str) -> DatasetContract:
    return DatasetContract(
        name="fixture",
        files=(
            FileContract(
                name="input.csv",
                required_columns=frozenset(required_columns),
                encoding="utf-8",
            ),
        ),
    )


def test_valid_utf8_csv_records_header_size_and_sha256(tmp_path: Path) -> None:
    csv_path = tmp_path / "input.csv"
    csv_path.write_bytes(b"customer_id,value\nc-1,10\n")

    report = verify_dataset(tmp_path, _contract("customer_id", "value"))

    assert report.ok is True
    assert report.files[0].columns == ("customer_id", "value")
    assert report.files[0].size_bytes == 25
    assert report.files[0].sha256 == (
        "b3811983ac76926d00a73674a3cde14e88b8ce59749fe870b86d8efae04474ef"
    )
    assert report.files[0].errors == ()


def test_missing_file_is_reported(tmp_path: Path) -> None:
    report = verify_dataset(tmp_path, _contract("customer_id"))

    assert report.ok is False
    assert report.files[0].errors == ("missing file: input.csv",)


def test_missing_required_column_is_reported(tmp_path: Path) -> None:
    (tmp_path / "input.csv").write_text("customer_id\nc-1\n", encoding="utf-8")

    report = verify_dataset(tmp_path, _contract("customer_id", "value"))

    assert report.ok is False
    assert report.files[0].errors == ("missing required columns: value",)


def test_duplicate_header_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "input.csv").write_text("customer_id,customer_id\nc-1,c-1\n", encoding="utf-8")

    report = verify_dataset(tmp_path, _contract("customer_id"))

    assert report.ok is False
    assert report.files[0].errors == ("duplicate header columns: customer_id",)


def test_malformed_encoding_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "input.csv").write_bytes(b"\xff\xfe,customer_id\n")

    report = verify_dataset(tmp_path, _contract("customer_id"))

    assert report.ok is False
    assert report.files[0].errors[0].startswith("cannot decode as utf-8:")


def test_path_with_chinese_characters_is_supported(tmp_path: Path) -> None:
    root = tmp_path / "公开数据" / "输入"
    root.mkdir(parents=True)
    (root / "input.csv").write_text("customer_id\nc-1\n", encoding="utf-8")

    report = verify_dataset(root, _contract("customer_id"))

    assert report.ok is True
    assert report.files[0].path == root / "input.csv"


def test_olist_contract_declares_the_official_nine_file_manifest() -> None:
    assert {file.name for file in OLIST_CONTRACT.files} == {
        "olist_customers_dataset.csv",
        "olist_geolocation_dataset.csv",
        "olist_order_items_dataset.csv",
        "olist_order_payments_dataset.csv",
        "olist_order_reviews_dataset.csv",
        "olist_orders_dataset.csv",
        "olist_products_dataset.csv",
        "olist_sellers_dataset.csv",
        "product_category_name_translation.csv",
    }
    assert len(OLIST_CONTRACT.files) == 9
    assert all(file.required_columns for file in OLIST_CONTRACT.files)


def test_olist_translation_contract_accepts_official_utf8_bom(tmp_path: Path) -> None:
    contract = next(
        file
        for file in OLIST_CONTRACT.files
        if file.name == "product_category_name_translation.csv"
    )
    (tmp_path / contract.name).write_bytes(
        "product_category_name,product_category_name_english\nbeleza_saude,health_beauty\n".encode(
            "utf-8-sig"
        )
    )

    report = verify_dataset(tmp_path, DatasetContract("translation", (contract,)))

    assert report.ok is True
    assert report.files[0].columns[0] == "product_category_name"
