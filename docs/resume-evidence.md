# Resume evidence ledger

Use this file to draft resume bullets only after the referenced automated evidence is green.
GrowthLens is a **personal public-data project**, not employment experience.

## Verified scope

| Claim | Evidence |
| --- | --- |
| Modeled 98,207 commercial orders | `observed_results.commerce.orders.value` |
| Reconciled R$13.49M merchandise value | `observed_results.commerce.merchandise_value.value` |
| Measured 91.89% overall on-time delivery | summed numerator/denominator in `mart_daily_kpis` and verified artifact |
| Analyzed 64,000 randomized customers | experiment assignment marts; 21,306 + 21,307 + 21,387 |
| Men's email +0.68 pp conversion | 95% CI [0.50, 0.86], Holm-adjusted p < 0.001 |
| Women's email +0.31 pp conversion | 95% CI [0.15, 0.47], Holm-adjusted p < 0.001 |
| Prevented BI identifier leakage | `tests/test_powerbi_exports.py` |
| Validated warehouse models | public-data dbt build: 101/101 pass |
| Validated code and contracts | full pytest and Ruff gates |

Source of truth: `artifacts/verified_metrics.json`. Do not round, annualize, or add business impact
without a labeled assumption and a reproducible calculation.

## Chinese resume bullets

**GrowthLens 电商经营监控与实验决策平台｜个人项目**

- 基于 Olist 九表公开数据搭建可审计分析链路，使用 SQL/dbt 建模订单、商品、支付与评价数据；通过订单粒度预聚合及对账测试消除多表一对多放大，稳定复现 98,207 笔商业订单与 R$13.49M 商品金额。
- 构建日度经营指标、客户 Cohort/RFM、卖家优先级与履约诊断模型，以分子/分母口径计算整体准时交付率 91.89%，并用滚动 Median/MAD 实现异常监控与维度归因；明确将履约-评分结果限定为相关性证据。
- 针对 64,000 名随机用户完成样本比例、重复分配与协变量平衡检查，按预注册口径估计两组邮件相对控制组的转化绝对提升：+0.68pp（95% CI 0.50-0.86）与 +0.31pp（0.15-0.47），并采用 Holm 校正控制多重比较。
- 设计五页 Power BI 决策看板及可版本控制的 PBIP/TMDL 语义模型，建立隐私安全导出、指标 JSON、CI 与 65+ 项 Python/集成测试和 101 项 dbt 检查，使核心结果可从源文件哈希追溯至可视化。

## Short version for a one-page resume

- 使用 SQL/dbt/Python 构建电商经营与实验分析平台，通过订单粒度预聚合解决多表 fan-out，完成 98,207 笔订单、R$13.49M 商品金额及履约/客户/卖家指标建模，并以 101 项 dbt 检查保障口径。
- 对 64,000 人随机实验实施 SRM、置信区间与 Holm 多重校正，验证两组邮件转化绝对提升 +0.68pp 与 +0.31pp；输出可追溯指标制品与五页 Power BI 决策看板。

## Interview boundary

You may say you designed, implemented, tested, and reproduced the project. Do not say the dashboard
was deployed at Olist, used by a business team, generated revenue, reduced delays, or changed a
production decision. Those outcomes are not present in the public evidence.

## Publication

GitHub URL: added only after the local/remote safety audit passes and the SHA is verified.
