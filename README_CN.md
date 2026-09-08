[English](README.md) · [项目选择](ECOSYSTEM.md) · [本次验证](publication/VALIDATION_2026-09-08.md)

# 明值经济 LUCIDECON 2.0

这是普通个体和小团队的本地机会检验与贡献记账工具，不是就业预测器、人的价值排行榜、投资顾问或支付系统。

## 最快使用
解压完整 ZIP，双击 `lucidecon.html`，选择案例并修改预算、现金目标、可用时间和需求下界。所有默认案例均为合成数据。页面可切换中英文、导入完整 JSON、导出输入/评估并打印。它不会联网或自动保存；完整账本和分配请使用 Python。

安装 Python 3.10 或以上后，在解压目录运行：
```
python lucidecon.pyz demo --output outputs/first_run
python lucidecon.pyz init --output my_case.json
python lucidecon.pyz assess my_case.json --output outputs/personal_01
python lucidecon.pyz replay outputs/personal_01
python lucidecon.pyz verify outputs/personal_01/ledger.jsonl
```
Windows 可用 `py -3` 代替 `python`，或双击 `run_demo.bat`。macOS/Linux 可用 `python3`。每次使用新输出目录，避免覆盖前次记录。

金额统一用分（整数），预算不要包含必需生活和照护储备。评估日期与期限必须显式填入。旧模板的同意期限不会自动延期。把数据来源改成 USER_SUBMITTED 也不等于资料真实；本地程序无法独立验证提交者或评审者身份。

## 结果如何看
“声明情景内稳健”只表示所有列出的情景下界达标，不代表真实市场已验证；“有边界试点”表示仍有可检验的空间；“证据不足”不是无路；“当前无路”只在这组目标、期限、预算、候选和输入假设中有效。每个机会都独立使用整份预算，不能把多个结果直接相加形成投资组合。

系统保留需求、客户入口、交付和任务能力的独立证据要求。它不从 DIKWP 角色推断人的完整能力、人格或价值，不替你辞职、贷款、转账或扩大公开身份。

## 交付目录
`reports/` 为重建后的中文与英文 Word/Markdown 报告；`src/` 是新版完整源码；`tests/` 是自动测试；`examples/` 是合成模板；`outputs/reference/` 是可重算结果；`legacy/v1_source/` 保留从旧可执行包恢复的源码，仅供版本审查。

详细命令、公式、制度假设、隐私与部署边界见英文 README、MIGRATION.md、docs/ 与报告。文件为本地明文，请只分享必要的最小化回执。`tools/verify_release.py` 核对发行文件的大小与 SHA-256，但校验清单本身不是第三方签名。
