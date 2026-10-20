# GrowthLens 电商经营分析与营销实验决策平台设计

> **交付范围修订（2026-10-19）：** 当前执行环境没有 Power BI Desktop。最终仓库因此交付
> 7 张经过测试的 BI 导出表、模型粒度与关系规范、DAX、主题、五页 PDF/PNG 成品预览和
> `dashboard_contract.json`，不把手写空壳文件冒充 Desktop 生成的 PBIP/PBIX。本文后续提到
> PBIP/PBIX 的验收项由这份可核验实施蓝图替代；若在有 Power BI Desktop 的环境继续制作，
> 再按 `powerbi/README.md` 生成真正可刷新的 PBIP/PBIX。

## 1 项目目的

GrowthLens 是一个面向数据分析岗位作品集的端到端项目。它通过两个相互独立、来源透明的公开数据案例，展示业务数据分析师从数据接入、质量校验和指标建模，到异常诊断、实验评估、可视化汇报和业务建议的完整工作链路。

项目需要补齐候选人现有简历中尚未充分展示的能力：SQL 多表分析、业务指标体系、数据质量、经营监控、Power BI、A/B 测试、统计推断以及面向非技术人员的结论表达。项目不以堆叠机器学习模型为目标，也不把公开数据分析结果包装成真实任职公司的业务成果。

## 2 目标受众与成功标准

### 2.1 目标受众

- 互联网、电商、招聘平台和金融科技公司的数据分析实习与校招岗位；
- 偏实验与增长的数据科学或产品分析岗位；
- 需要验证 SQL、Python、统计分析、BI 和业务沟通能力的面试官。

### 2.2 成功标准

项目完成时必须满足以下条件：

1. 新环境能够按 README 从公开来源获取数据并复现核心结果；
2. PostgreSQL 中存在清晰的原始层、暂存层和分析集市层，表粒度与主键均有文档；
3. dbt 构建与数据质量测试全部通过，关键指标有唯一口径；
4. 经营分析至少覆盖收入、客户、履约、商家和数据质量五类问题；
5. 实验分析包含随机分组校验、效应估计、置信区间、多重比较和异质性分析；
6. Power BI 看板能够从管理层总览下钻到可执行问题；
7. 仓库包含一页决策备忘录、看板截图、数据字典、指标字典和复现说明；
8. 所有简历数字均由版本化代码生成，并能追溯到查询或统计输出；
9. 不宣称公开数据分析带来了真实业务上线或真实收入提升。

## 3 范围与非目标

### 3.1 项目范围

GrowthLens 包含两个案例模块：

- **经营分析模块**：使用 Olist 巴西电商匿名数据，完成多表建模、指标监控、客户与履约分析；
- **实验决策模块**：使用 Hillstrom 邮件营销随机实验，完成实验有效性检查、增量效果评估和定向策略分析。

两个数据集只共享分析平台、代码规范和展示框架，不进行用户级拼接，也不宣称来自同一家公司。

### 3.2 非目标

- 不建设实时流处理系统；
- 不训练大语言模型或 Agent；
- 不以预测准确率竞赛为中心；
- 不伪造页面浏览、点击、曝光或利润字段；
- 不把 Olist 的订单状态时间戳称为点击转化漏斗；
- 不把观察性相关关系表述为因果关系；
- 不在首版同时实现 Power BI、Tableau、Superset 和 Streamlit。

## 4 数据来源与事实边界

### 4.1 Olist 电商数据

来源为 Olist 发布的 Brazilian E-Commerce Public Dataset。数据包含约十万笔匿名订单以及客户、订单项、支付、商品、商家、评价、地理位置和品类翻译等关联表，时间范围为 2016 至 2018 年。

官方页面：<https://www.kaggle.com/olistbr/brazilian-ecommerce/home/>

使用约束：

- 原始文件不提交到 Git 仓库；
- README 提供 Kaggle 手动下载和可选 CLI 下载方式；
- 数据规模以实际下载版本和加载审计结果为准；
- 收入、订单、客户和履约指标都明确记录过滤条件与表粒度；
- 评价分数与延迟之间只报告关联；如做调整分析，仍明确其观察性性质。

### 4.2 Hillstrom 邮件实验数据

来源为 Kevin Hillstrom 发布的 MineThatData E-Mail Analytics and Data Mining Challenge。64,000 名近 12 个月有购买记录的客户被随机分配至男装邮件、女装邮件或不发邮件三组，并在随后两周观察访问、转化和消费。

原始说明：<https://blog.minethatdata.com/2008/03/minethatdata-e-mail-analytics-and-data.html>

使用约束：

- 明确实验年份、观察窗口和适用人群；
- 不将历史实验结果解释为当前营销环境的外部有效性结论；
- 收入或预算情景必须标记为基于假设的估算，不写成已实现收益；
- 原始数据下载方式、校验和与字段字典必须纳入仓库。

## 5 用户故事与核心问题

### 5.1 经营负责人

经营负责人需要快速判断收入、订单、客单价、复购、履约和满意度是否出现异常，并能下钻到时间、地区、品类和商家，找到主要贡献因素和可执行动作。

### 5.2 运营负责人

运营负责人需要识别延迟交付、低评分和低复购集中在哪些商家、品类和地区，并获得带证据的优先处理清单。

### 5.3 增长与实验负责人

增长负责人需要确认实验分流是否有效、邮件是否带来增量访问、转化和消费，以及哪些客户群体值得进入后续定向实验。

### 5.4 数据负责人

数据负责人需要确认指标定义一致、表关系可靠、数据异常可追溯，并能重复生成同一份报告。

## 6 系统架构

```text
公开原始数据
  Olist CSV                         Hillstrom CSV
       |                                  |
       +------------ 获取与校验 ---------+
                          |
                    PostgreSQL raw
                          |
                 dbt staging / tests
                          |
          +---------------+----------------+
          |                                |
   commerce marts                    experiment marts
          |                                |
   SQL 指标与异常表                 Python 统计分析
          |                                |
          +---------------+----------------+
                          |
              Power BI + 决策备忘录
                          |
                 README 与简历证据
```

### 6.1 技术栈

- 数据库：PostgreSQL；
- 环境：Docker Compose；
- 转换与测试：dbt Core 与 PostgreSQL 适配器；
- 数据分析：Python、pandas、NumPy、SciPy、statsmodels、scikit-learn；
- 可视化：Power BI Desktop；
- 探索与解释：Jupyter Notebook，但正式指标由 SQL 模型或可调用 Python 模块生成；
- 测试：dbt tests、pytest；
- 版本管理：Git 与 GitHub Actions；
- 文档：Markdown、Mermaid 或等价的可版本化图表。

### 6.2 仓库结构

```text
growthlens/
  README.md
  LICENSE
  .env.example
  docker-compose.yml
  pyproject.toml
  Makefile
  data/
    README.md
    raw/.gitkeep
    interim/.gitkeep
    exports/.gitkeep
  scripts/
    download_hillstrom.py
    verify_inputs.py
    load_raw.py
  dbt/
    dbt_project.yml
    models/
      staging/
      intermediate/
      marts/commerce/
      marts/experiments/
    tests/
    seeds/
  src/growthlens/
    config.py
    quality.py
    monitoring.py
    experimentation.py
    reporting.py
  notebooks/
    01_commerce_eda.ipynb
    02_root_cause_analysis.ipynb
    03_experiment_validation.ipynb
    04_experiment_effects.ipynb
  sql/
    ad_hoc/
    validation/
  powerbi/
    GrowthLens.pbix
    model.md
    measures.md
    screenshots/
  reports/
    executive_decision_memo.md
    experiment_readout.md
    metric_catalog.md
    data_dictionary.md
    limitations.md
  tests/
    test_experimentation.py
    test_monitoring.py
    test_reporting.py
  artifacts/
    verified_metrics.json
    run_manifest.json
```

原始数据和可能较大的中间文件通过 `.gitignore` 排除。`verified_metrics.json` 只保存由流水线生成且允许公开的汇总指标，作为 README、报告和简历的事实来源。

## 7 数据模型

### 7.1 原始层

Olist 每个 CSV 对应一个原始表，保留源字段并添加：

- `_loaded_at`
- `_source_file`
- `_row_hash`
- `_run_id`

Hillstrom 原始表保留全部原始字段，并增加相同的审计列。

### 7.2 暂存层

暂存层负责：

- 统一蛇形字段名与数据类型；
- 去除完全重复行；
- 标准化时间戳和分类值；
- 生成明确的异常标记，不静默删除业务异常；
- 保留源主键与加载审计字段。

### 7.3 经营分析集市

核心模型包括：

- `fct_orders`：一行一订单；
- `fct_order_items`：一行一订单项；
- `fct_payments`：一行一支付记录；
- `fct_reviews`：一行一评价；
- `dim_customers`：按 `customer_unique_id` 识别跨订单客户；
- `dim_sellers`：一行一商家；
- `dim_products`：一行一商品；
- `dim_dates`：连续日期维度；
- `mart_daily_kpis`：一行一天的核心经营指标；
- `mart_customer_cohorts`：客户首购月份与后续活跃；
- `mart_seller_scorecard`：商家履约、收入和评分；
- `mart_delivery_diagnostics`：延迟订单及其业务维度；
- `mart_data_quality`：每次运行的质量统计。

### 7.4 实验分析集市

核心模型包括：

- `dim_experiment_customers`：实验前客户属性；
- `fct_experiment_assignments`：随机分组；
- `fct_experiment_outcomes`：访问、转化和消费结果；
- `mart_experiment_summary`：各实验组样本量和指标；
- `mart_experiment_segments`：预先定义的客户分群结果；
- `mart_experiment_quality`：SRM 与协变量平衡输入。

将单表拆为维度与事实表是为了展示可复用的数据建模和指标语义，不改变原始记录，也不制造新的业务事件。

## 8 指标定义

指标定义必须集中维护在 `reports/metric_catalog.md`，并在 dbt 模型和 Power BI 度量中保持一致。

### 8.1 经营指标

- **商品交易额**：符合纳入状态的订单项 `price` 之和；
- **运费**：符合纳入状态的订单项 `freight_value` 之和；
- **订单数**：符合纳入状态的不同 `order_id` 数；
- **客单价**：商品交易额除以订单数；
- **客户数**：不同 `customer_unique_id` 数；
- **复购客户率**：拥有至少两笔纳入订单的客户数除以客户数；
- **准时送达率**：实际送达时间不晚于预计送达时间的已送达订单占比；
- **延迟天数**：实际送达时间减预计送达时间，提前送达保留负值；
- **平均评价分**：有效评价记录的 `review_score` 均值；
- **商家延迟率**：商家已送达订单中延迟订单占比。

订单状态纳入规则需要在首次数据审计后冻结，并以测试保护。商品交易额和含运费支付额分开命名，避免把两者都称为 GMV。

### 8.2 实验指标

- **主要指标**：转化率；
- **次要指标**：访问率、客均消费、购买者客单消费；
- **实验质量指标**：样本分配偏差、协变量标准化差异、缺失率；
- **效应指标**：绝对提升、相对提升、均值差和置信区间；
- **决策指标**：每次触达的增量消费，以及显式成本假设下的增量净值。

购买者客单消费属于转化后的条件指标，必须说明选择偏差，不能替代全体样本的客均消费。

## 9 分析设计

### 9.1 经营监控

- 按日和周构建收入、订单、客单价、客户、准时率和评价指标；
- 使用滚动中位数与 MAD 或经验证的稳健标准分数标记异常；
- 异常规则的窗口、最小样本量和阈值写入配置；
- 通过时间、地区、品类和商家进行贡献度拆解；
- 对已知历史数据注入少量测试异常，仅用于验证检测逻辑，不作为业务发现。

### 9.2 客户分析

- 基于 `customer_unique_id` 计算首购、最近购买、购买次数和消费额；
- 建立月度 Cohort 和复购曲线；
- 使用规则透明的 RFM 分群；
- 分析客户价值、地区、品类与履约体验之间的关系；
- 如复购稀疏，则将低复购本身作为数据结论，不强行训练流失模型。

### 9.3 履约与满意度分析

- 分解购买、审批、交付承运和客户签收的时间间隔；
- 比较不同延迟区间的评价分布；
- 使用回归或分层比较调整可观测混杂因素；
- 将结果表述为调整后的关联，不直接宣称延迟造成低评分；
- 生成商家与地区优先处理清单，并说明优先级规则。

### 9.4 实验有效性

- 以公开说明中的三等分设计为预期分配执行卡方 SRM 检查；
- 对实验前协变量计算标准化均值差；
- 检查缺失、重复客户和组间污染；
- 在读取结果前冻结主要指标、比较组和多重比较方案；
- 报告统计显著性、实际效应和不确定性。

### 9.5 实验效应

- 转化率与访问率使用两比例差及置信区间；
- 消费高度零膨胀，使用全样本均值差并以 bootstrap 交叉验证区间；
- 三组比较使用 Holm 方法控制家族错误率；
- 使用历史消费等实验前变量进行 CUPED 或回归调整，并与未调整估计比较；
- 预先选择少量有业务解释的分群，使用交互项检验异质性；
- uplift 模型仅作为扩展，必须使用独立验证、Qini 或 uplift 曲线，并与简单规则基线比较；
- 定向策略只作为离线政策模拟，不声称已经上线。

## 10 Power BI 信息架构

### 10.1 管理层总览

- 商品交易额、订单、客户、客单价、复购率、准时率；
- 时间趋势和异常标记；
- 当前最重要的三个问题与建议。

### 10.2 收入与客户增长

- 收入与订单趋势；
- 品类、地区和客户分群；
- Cohort 与复购；
- RFM 分布和客户价值集中度。

### 10.3 履约与商家运营

- 各阶段时长；
- 延迟率与评分；
- 地区与商家优先级矩阵；
- 可下钻的异常订单统计。

### 10.4 实验决策

- 实验样本、质量检查与功效；
- 三组主要指标和置信区间；
- 细分人群效果；
- 基于明确假设的预算或触达情景。

### 10.5 数据质量

- 加载行数、缺失、重复、关系失败和异常时间戳；
- dbt 测试状态；
- 数据刷新时间和运行编号。

所有页面使用一致的筛选器和度量命名。图表必须回答业务问题，避免为了丰富页面而加入无决策价值的装饰图。

## 11 决策输出

项目不以 Notebook 结尾，而是交付两类业务材料：

1. **经营决策备忘录**：说明最重要的经营问题、证据、可能原因、建议动作和限制；
2. **实验结果报告**：说明实验有效性、效应大小、是否建议采用某方案、下一次实验设计和外部有效性限制。

每条建议必须链接到生成它的 SQL、图表或统计结果。分析发现和建议分开写，避免把推测当成事实。

## 12 错误处理与可追溯性

- 下载缺失、校验和变化或字段漂移时立即失败，并给出修复提示；
- 原始表加载采用幂等策略，同一运行不得重复插入；
- 每次运行生成唯一 `run_id`，记录文件、行数、时间和代码版本；
- 数据质量失败阻止分析集市和看板导出继续更新；
- 统计分析固定随机种子并记录包版本；
- Power BI 使用稳定的视图或导出表，避免直接连接不稳定的原始表；
- 任何手工步骤都写入 README，并尽量提供可验证输出。

## 13 测试与验收

### 13.1 数据测试

- 主键唯一且非空；
- 外键关系有效；
- 枚举状态在已知集合内；
- 金额、评分和关键时长满足合理范围；
- 客户、订单和订单项粒度不会因多表连接发生扇出；
- 每次加载的行数和源文件一致。

### 13.2 指标测试

- 用小型固定样本验证订单数、交易额、客单价和复购率；
- 对 Power BI DAX 与 SQL 结果进行抽样对账；
- 验证取消订单、重复支付和多订单项不会造成重复计算；
- 对看板中的核心卡片保存机器可读基准值。

### 13.3 统计测试

- 在已知合成数据上验证 SRM、效应估计和置信区间；
- 零效应数据不得频繁产生假阳性；
- 已知正效应数据应在样本量足够时被检出；
- bootstrap 在固定种子下可重复；
- 多重比较校正与参考实现一致；
- CUPED 调整不得使用实验后变量。

### 13.4 展示验收

- 看板所有页面无溢出、无截断和无失效筛选器；
- GitHub README 在未安装 Power BI 时仍能通过截图和文字理解；
- 一条命令或一组明确命令可重建数据库、模型和报告；
- Windows 环境下的路径和编码经验证；
- 简历引用的每个数字都存在于 `verified_metrics.json`。

## 14 原创性与参考边界

项目可以借鉴成熟开源项目的工程原则：

- dbt Jaffle Shop 的分层建模、测试与指标语义；
- Plotly Dash Sample Apps 的交互式信息组织；
- Apache Superset 的数据集中心和指标层思想；
- CausalML 与 DoWhy 的处理效应、稳健性和异质性分析方法。

不得复制其他求职者仓库的 README、结论、图表、代码结构或简历措辞。所有业务问题、指标口径、查询、图表和报告均需根据本项目重新设计，并在依赖和参考文档中给出来源。

## 15 风险与缓解

| 风险 | 影响 | 缓解措施 |
| --- | --- | --- |
| Olist 被大量作品使用 | 项目辨识度下降 | 聚焦指标治理、异常归因、履约决策和可测试管道，不止做通用销售看板 |
| 两个数据源不属于同一企业 | 容易造成误解 | 明确为同一分析平台的两个独立公开案例，禁止跨数据集拼接 |
| Power BI 二进制不利于代码审查 | GitHub 可见性弱 | 提供模型、DAX、截图、PDF 和 SQL 对账结果 |
| Hillstrom 数据较旧 | 外部有效性有限 | 把它定位为统计方法基准，并明确时间和人群限制 |
| 统计方法过度复杂 | 偏离数据分析岗位 | 基础实验结论优先，uplift 与因果扩展放在附加模块 |
| 指标过多 | 看板失焦 | 每页围绕一个决策问题，核心指标保持有限 |
| 数据下载或许可变化 | 无法复现 | 保存来源、下载说明、文件名、校验和和许可备注 |

## 16 简历事实契约

项目尚未运行前，不预写任何效果数字。完成后简历可使用以下类型的事实：

- 实际加载的数据行数、表数和测试数；
- 实际建立的指标、分析集市和看板页面数；
- 真实计算的经营指标、实验效应与置信区间；
- 实际发现的数据质量问题和修复规则；
- 在公开数据上的离线策略模拟结果，且明确为估算或模拟。

不得使用以下表述：

- “推动公司收入提升”；
- “上线后转化率提升”；
- “为管理层创造某金额收益”；
- “负责真实公司核心业务”；
- 任何无法由仓库代码、公开数据或用户真实经历支持的职责和成果。

最终简历条目应使用“构建、分析、识别、评估、提出、验证”等可核验动词，并把公开数据、离线分析和真实工作经历严格区分。

## 17 高层实施阶段

1. 环境、数据获取与加载审计；
2. Olist 分层数据模型和数据质量测试；
3. 经营指标、客户分析和异常诊断；
4. Hillstrom 实验有效性与效应分析；
5. Power BI 数据模型、DAX 和五页看板；
6. 决策备忘录、README、复现验证和简历事实提取。

具体文件、任务依赖、验证命令和提交边界将在实施计划中展开。

## 18 参考项目与资料

- Olist 数据集：<https://www.kaggle.com/olistbr/brazilian-ecommerce/home/>
- Hillstrom 实验说明：<https://blog.minethatdata.com/2008/03/minethatdata-e-mail-analytics-and-data.html>
- dbt Jaffle Shop：<https://github.com/dbt-labs/jaffle-shop>
- Plotly Dash Sample Apps：<https://github.com/plotly/dash-sample-apps>
- Apache Superset：<https://github.com/apache/superset>
- Uber CausalML：<https://github.com/uber/causalml>
- DoWhy：<https://github.com/py-why/dowhy>
- Criteo Uplift 数据集，仅作为后续规模压力测试候选：<https://ailab.criteo.com/criteo-uplift-prediction-dataset/>
