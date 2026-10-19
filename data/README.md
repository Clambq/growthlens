# Public data inputs

Raw data is deliberately excluded from Git. The repository records contracts, provenance,
download instructions, and hashes produced on the user's machine.

## Olist commerce case

- Source: [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
- Scope: nine related CSV files covering anonymized marketplace orders from 2016–2018.
- Retrieval with an authenticated Kaggle CLI:

```powershell
kaggle datasets download -d olistbr/brazilian-ecommerce -p data/raw/olist --unzip
.\.venv\Scripts\python.exe scripts/verify_inputs.py olist
```

Kaggle credentials are personal secrets and must remain outside this repository. If the CLI is
not available, download the archive manually from the source page and extract exactly the nine
contracted files into `data/raw/olist/`.

## Hillstrom randomized experiment case

- Original publisher: Kevin Hillstrom, MineThatData E-Mail Analytics Challenge (2008).
- Direct public CSV: `http://www.minethatdata.com/Kevin_Hillstrom_MineThatData_E-MailAnalytics_DataMiningChallenge_2008.03.20.csv`
- Scope: 64,000 customers assigned to men's email, women's email, or no-email control.

```powershell
.\.venv\Scripts\python.exe scripts/download_hillstrom.py
.\.venv\Scripts\python.exe scripts/verify_inputs.py hillstrom
```

The download command validates the expected header before moving the file into place. Both
verification commands emit byte sizes and SHA-256 hashes so a run can be traced to exact inputs.
