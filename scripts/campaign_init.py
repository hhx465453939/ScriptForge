#!/usr/bin/env python3
"""campaign_init.py — 运营物料包脚手架 / 校验器。

用法：
    # 生成物料包骨架（10 项）
    python scripts/campaign_init.py --slug demo --obj-type repo --metric stars
    # 预览将生成什么，不写盘
    python scripts/campaign_init.py --slug demo --obj-type repo --metric stars --dry-run
    # 校验已有物料包缺什么
    python scripts/campaign_init.py --check campaigns/demo_20261115

设计纪律：
    1. 只生成空壳 + 待填标记（TBD / UNKNOWN），**绝不写入假数据**
    2. 幂等：已有文件不覆盖，需 --force 才覆盖
    3. 缺件判定见 assets/campaign-package.md §2（10 项）
    4. 自带日志 sink（scripts/campaign_init.log），不依赖宿主重定向
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import date

# --- 冻结清单（与 assets/campaign-package.md §2 对齐）---
REQUIRED_FILES = [
    "00-brief.md",
    "01-recon.md",
    "02-positioning.md",
    "03-backlog.md",
    "05-assets/image-prompts.md",
    "05-assets/copy-blocks.md",
    "06-schedule.md",
    "07-ledger.md",
    "08-review.md",
]
REQUIRED_DIRS = ["04-scripts", "05-assets"]
SCRIPT_DIR = "04-scripts"
TEMPLATE_NAME = "_TEMPLATE.md"

VALID_OBJ = ("repo", "content", "product", "personal")
VALID_MODE = ("copilot", "navigate", "autopilot")


def _tpl_brief(slug: str, obj: str, metric: str, mode: str, today: str) -> str:
    return f"""---
campaign: {slug}
obj_type: {obj}
primary_metric: {metric}
secondary_metrics: [UNKNOWN]
window: {{start: {today}, end: TBD}}
baseline: BASELINE_MISSING
judge: "primary >= baseline.p80"
mode: {mode}
resources: {{人: TBD, 预算: TBD, 产能: TBD}}
constraints: [不代发, 不刷量, 不使用绝对化用语]
---

## 一、这个战役要赢什么
TBD —— 一句话说清「赢 {metric}」具体指什么

## 二、为什么是现在
TBD —— 外部时机 + 内部准备度

## 三、基线现状
baseline = BASELINE_MISSING

> 本次定位为「基线采集战役」：目标是产出 n≥10 有效样本，而不是「爆」。
> 见 references/metrics-taxonomy.md §7。

## 四、不做什么
- TBD
"""


def _tpl_recon() -> str:
    return """# 侦察报告（S1）

> 门控 G1：每条数据必须带 source_level（L1/L2/L3），未知写 UNKNOWN，禁止「据说」。

## 一、受众

| 结论 | 证据 | source_level |
|---|---|---|
| TBD | TBD | L2 |

## 二、竞品

| 竞品/标杆 | 内容形态 | 结构特征 | 互动中位数 | source_level |
|---|---|---|---|---|
| TBD | | | | |

## 三、热点与概念（近 30 天）

| 概念/事件 | 与我们相关性 | 可借势角度 | 时效窗口 | source_level |
|---|---|---|---|---|
| TBD | | | | |

## 四、侦察结论

1. 机会在：TBD
2. 不要碰：TBD
3. 最缺的证据：TBD
"""


def _tpl_positioning() -> str:
    return """# 定位与差异化（S2）

## 一、我们是谁（一句话）
TBD

## 二、我们不是谁（主动放弃）
TBD

## 三、差异点（≤3 条，每条可验证）

| 编号 | 差异点 | 竞品缺失证据 | 我方证据 | 可验证方式 |
|---|---|---|---|---|
| D1 | TBD | TBD | TBD | TBD |

## 四、不做什么
- TBD

## 五、差异化量化（可选）
与竞品语言分布 JS 散度 = TBD
"""


def _tpl_backlog() -> str:
    return """# 选题池与排序（S3）

## 评分口径
`score = 0.35*需求强度 + 0.25*(1-竞争密度) + 0.20*可产性 + 0.20*指标契合`

## 候选池（≥12 条）

| # | 选题 | 形态 | 需求强度 | 竞争密度 | 可产性 | 指标契合 | 总分 | 排序 |
|---|---|---|---|---|---|---|---|---|
| 1 | TBD | graphic | 0 | 0 | 0 | 0 | 0 | 0 |

## 本周 Top-N（N = resources.产能）
1. TBD
"""


def _tpl_script() -> str:
    return """---
script_id: TBD
genre: TBD
model: TBD
backlog_ref: TBD
---

## 一、文案全文
TBD

## 二、量化评分卡

> 必须来自 `python scripts/viral_score.py --file <稿> --json` 的真实输出，不许手写。

| 综合分 | 分区 | 95% CI |
|---|---|---|
| TBD | TBD | TBD |

| 维度 | 分数 |
|---|---|
| 钩子力 | TBD |
| 信息密度 | TBD |
| 节奏冲击 | TBD |
| 情绪驱动 | TBD |
| 说服转化 | TBD |
| 差异化 | TBD |
| 可复制性 | TBD |

短板：TBD

## 三、迭代记录

| 轮次 | 改动 | 综合分 | 变化 |
|---|---|---|---|
| 1 | TBD | TBD | TBD |

## 四、平台适配

| 平台 | 标题 | 标签 | 备注 |
|---|---|---|---|
| TBD | | | |
"""


def _tpl_img() -> str:
    return f"""# 文生图提示词

> 字段冻结见 `assets/prompt-spec.md`：13 字段缺一不合格。
> 格式：每条一个 yaml 代码块。

```yaml
id: img-01
subject: TBD
scene: TBD
composition: TBD（必须含留白说明）
lighting: TBD
style: TBD
palette: TBD
lens: TBD
negative: 无文字水印，无变形
platform: TBD
model: 通用图像模型 / UNKNOWN
params: {{aspect_ratio: "3:4", seed: 0}}
usage: TBD
```
"""


def _tpl_copy() -> str:
    return """# 可直接粘贴文案块

## douyin
- 标题：
- 正文/口播：
- 话题标签：
- 字幕要点（3–5 条）：
- 评论区引导：

## xiaohongshu
- 标题（12–18 字）：
- 正文（分段）：
- 标签组（4–8 个）：
- 评论区引导：

## x
- 正文（≤280 字）：
- 配图建议：
"""


def _tpl_schedule() -> str:
    return """# 发布排期（S6）

> 变体纪律：同一选题的多个变体**只改一个变量**，否则回填无法归因。

| 日期 | 渠道 | 物料文件 | 变体（只改一个变量） | 预期 | 实际发布 |
|---|---|---|---|---|---|
| TBD | TBD | TBD | TBD | TBD | 待发 |
"""


def _tpl_ledger() -> str:
    return """# 数据回填（S7）与假设台账

> 字段字典见 `references/metrics-taxonomy.md` §4；纪律见 `assets/publish-ledger.md`。
> 红线：source_level 为 L3 时不得用于「爆/不爆」判定。

## 一、回填表

| row_id | asset_file | platform | published_at | primary | secondary | window | source | baseline_at_publish | hyp | notes |
|---|---|---|---|---|---|---|---|---|---|---|
| L001 | TBD | TBD | TBD | UNKNOWN | UNKNOWN | TBD | UNKNOWN | UNKNOWN | H1 | — |

## 二、假设台账

| hyp_id | 假设句 | 变量（只改这个） | 对照 row_id | 结果 row_id | 结论 | 证据强度 |
|---|---|---|---|---|---|---|
| H1 | 若 <改动>，则 <主指标> 会 <方向>，因为 <机制> | TBD | L001 | TBD | 证据不足 | 弱 |

> 结论只允许三值：支持 / 被否证 / 证据不足。禁止把「证据不足」写成「支持」。
"""


def _tpl_review() -> str:
    return """# 复盘与校准（S8）

## 一、判定结果

| row_id | primary | baseline.p80 | 分位 | 结论 |
|---|---|---|---|---|
| TBD | UNKNOWN | UNKNOWN | UNKNOWN | 样本不足 |

## 二、假设验证

| hyp_id | 结论 | 证据强度 | 说明 |
|---|---|---|---|
| H1 | 证据不足 | 弱 | TBD |

## 三、基线重估

- 新 baseline：{p50: UNKNOWN, p80: UNKNOWN, n: 0}

## 四、下一轮动作

1. 更新 `00-brief.md` 的 baseline
2. 把「被否证的假设」写进下一轮 S2 注意事项
3. 把「超预期的结构」补进 `references/script-models.md` 已验证品类
"""


def _templates(slug: str, obj: str, metric: str, mode: str, today: str) -> dict:
    return {
        "00-brief.md": _tpl_brief(slug, obj, metric, mode, today),
        "01-recon.md": _tpl_recon(),
        "02-positioning.md": _tpl_positioning(),
        "03-backlog.md": _tpl_backlog(),
        f"{SCRIPT_DIR}/{TEMPLATE_NAME}": _tpl_script(),
        "05-assets/image-prompts.md": _tpl_img(),
        "05-assets/copy-blocks.md": _tpl_copy(),
        "06-schedule.md": _tpl_schedule(),
        "07-ledger.md": _tpl_ledger(),
        "08-review.md": _tpl_review(),
    }


def check_package(pkg_dir: str) -> list:
    """返回缺件列表；空列表 = 合格。"""
    missing = []
    for rel in REQUIRED_FILES:
        if not os.path.isfile(os.path.join(pkg_dir, rel)):
            missing.append(rel)
    for d in REQUIRED_DIRS:
        if not os.path.isdir(os.path.join(pkg_dir, d)):
            missing.append(d + "/")
    scripts_dir = os.path.join(pkg_dir, SCRIPT_DIR)
    if os.path.isdir(scripts_dir):
        real = [
            f for f in os.listdir(scripts_dir)
            if f.endswith(".md") and f != TEMPLATE_NAME
        ]
        if not real:
            missing.append(f"{SCRIPT_DIR}/ (需 ≥1 份真实文案，_TEMPLATE.md 不算)")
    return missing


def setup_log() -> str:
    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "campaign_init.log")
    logging.basicConfig(
        filename=log_path, level=logging.INFO, filemode="a", force=True,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    return log_path


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="运营物料包脚手架 / 校验器")
    p.add_argument("--slug", help="campaign 短名（如 scriptforge）")
    p.add_argument("--obj-type", default="repo", help="repo | content | product | personal")
    p.add_argument("--metric", help="主指标（如 stars / views / sales / followers）")
    p.add_argument("--mode", default="copilot", help="copilot | navigate | autopilot")
    p.add_argument("--root", default="campaigns", help="物料包根目录（默认 campaigns）")
    p.add_argument("--date", default=None, help="日期戳 YYYYMMDD，默认今天")
    p.add_argument("--dry-run", action="store_true", help="只打印将生成什么，不写盘")
    p.add_argument("--force", action="store_true", help="覆盖已存在文件")
    p.add_argument("--check", metavar="DIR", help="校验已有物料包缺件")
    args = p.parse_args(argv)

    log_path = setup_log()

    # 校验模式
    if args.check:
        if not os.path.isdir(args.check):
            print(f"错误：目录不存在 {args.check}", file=sys.stderr)
            return 2
        missing = check_package(args.check)
        logging.info("check dir=%s missing=%d %s", args.check, len(missing), missing)
        if missing:
            print(f"✗ 物料包不合格，缺 {len(missing)} 项：")
            for m in missing:
                print(f"  - {m}")
            print(f"\n[日志] {log_path}", file=sys.stderr)
            return 1
        print("✓ 物料包合格（10 项齐全）")
        print(f"[日志] {log_path}", file=sys.stderr)
        return 0

    # 生成模式
    if not args.slug or not args.metric:
        print("错误：生成模式需要 --slug 与 --metric", file=sys.stderr)
        return 2
    if args.obj_type not in VALID_OBJ:
        print(f"错误：--obj-type 必须是 {VALID_OBJ}", file=sys.stderr)
        return 2
    if args.mode not in VALID_MODE:
        print(f"错误：--mode 必须是 {VALID_MODE}", file=sys.stderr)
        return 2

    stamp = args.date or date.today().strftime("%Y%m%d")
    pkg_name = f"{args.slug}_{stamp}"
    pkg_dir = os.path.join(args.root, pkg_name)
    tpls = _templates(args.slug, args.obj_type, args.metric, args.mode,
                      date.today().isoformat())

    if args.dry_run:
        print(f"[dry-run] 将生成 {pkg_dir}/")
        for rel in tpls:
            print(f"  + {rel}")
        print(f"\n共 {len(tpls)} 个文件；缺件判定需 ≥10 项（见 assets/campaign-package.md §2）")
        return 0

    os.makedirs(os.path.join(pkg_dir, SCRIPT_DIR), exist_ok=True)
    os.makedirs(os.path.join(pkg_dir, "05-assets", "html"), exist_ok=True)

    written, skipped = [], []
    for rel, content in tpls.items():
        path = os.path.join(pkg_dir, rel)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        if os.path.exists(path) and not args.force:
            skipped.append(rel)
            continue
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        written.append(rel)

    logging.info("init slug=%s obj=%s metric=%s mode=%s pkg=%s written=%d skipped=%d",
                 args.slug, args.obj_type, args.metric, args.mode, pkg_dir,
                 len(written), len(skipped))

    print(f"✓ 物料包已生成：{pkg_dir}")
    for rel in written:
        print(f"  + {rel}")
    if skipped:
        print(f"  跳过（已存在，需 --force 覆盖）：{len(skipped)} 个")

    missing = check_package(pkg_dir)
    if missing:
        print(f"\n注意：仍有 {len(missing)} 项待补：")
        for m in missing:
            print(f"  - {m}")
        print("（_TEMPLATE.md 不计入真实文案，需另建 04-scripts/<genre>-01.md）")

    print(f"\n下一步：按 references/ops-loop.md 从 S0 开始填 00-brief.md")
    print(f"[日志] {log_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
