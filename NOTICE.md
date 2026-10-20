# Notices and data attribution

## Project scope

GrowthLens is an independent personal portfolio project. It is not affiliated with, endorsed by,
or deployed at Olist, MineThatData, Kaggle, Microsoft, or any employer. The analysis describes
public historical datasets and must not be represented as production business impact.

## Olist Brazilian E-Commerce Public Dataset

- Publisher: Olist
- Source: <https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce>
- Dataset license listed by the source: Creative Commons Attribution-NonCommercial-ShareAlike 4.0
  International (CC BY-NC-SA 4.0)
- Scope used here: nine anonymized commerce CSV files covering orders, customers, items, products,
  sellers, payments, reviews, geolocation, and category translation.

The raw data is not redistributed by this repository. Users must obtain it from the original source
and comply with the current source terms. The project's MIT license applies to project code only;
it does not replace or broaden the dataset license.

## Hillstrom MineThatData E-Mail Analytics Challenge

- Publisher: Kevin Hillstrom / MineThatData
- Original challenge data:
  <http://www.minethatdata.com/Kevin_Hillstrom_MineThatData_E-MailAnalytics_DataMiningChallenge_2008.03.20.csv>
- Scope used here: 64,000 anonymized customer records from a three-arm email experiment.

The original page does not provide an explicit software-style license in the downloaded CSV. This
repository therefore does not redistribute the raw file. Users must review and follow the original
publisher's terms before reuse.

## Generated outputs

`artifacts/verified_metrics.json`, the dashboard screenshots, and the dashboard PDF are analytical
derivatives generated from the cited public datasets. They contain aggregate values and
pseudonymous seller keys, not raw customer or order identifiers. Commercial reuse remains subject
to the underlying dataset terms.

## Third-party software

Python, PostgreSQL, DuckDB, dbt, pandas, NumPy, SciPy, statsmodels, scikit-learn, SQLAlchemy,
ReportLab, Jupyter, Power BI, and GitHub Actions are trademarks or projects of their respective
owners and are used under their own licenses.
