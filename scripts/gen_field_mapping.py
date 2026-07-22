"""生成 docs/field-mapping.csv 字段对应表。

从 src.schemas.financial.REQUIREMENT_ALIGNMENT + SUPPLEMENTARY_FIELDS
与 src.data.interfaces.TUSHARE_INTERFACES 自动生成 CSV，保证与代码同步。

用法：uv run python scripts/gen_field_mapping.py
"""

from __future__ import annotations

import csv
from pathlib import Path

from src.data.interfaces import TUSHARE_INTERFACES
from src.schemas.financial import COMPUTED, REQUIREMENT_ALIGNMENT, SUPPLEMENTARY_FIELDS, UNAVAILABLE

OUTPUT = Path(__file__).resolve().parent.parent / "docs" / "field-mapping.csv"


def _interface_info(endpoint: str) -> tuple[str, str, str]:
    """返回 (vip接口名, 文档URL, 积分要求)；非接口端点返回 ('—', '—', '—')。"""
    if endpoint in (COMPUTED, UNAVAILABLE):
        return "—", "—", "—"
    iface = TUSHARE_INTERFACES[endpoint]
    return iface.vip_api_name, iface.doc_url, str(iface.min_points)


def main() -> None:
    rows: list[list[str]] = []
    idx = 0

    # 55 需求字段
    for a in REQUIREMENT_ALIGNMENT:
        idx += 1
        api, url, pts = _interface_info(a.endpoint)
        field_str = "/".join(a.tushare_field) if isinstance(a.tushare_field, tuple) else (a.tushare_field or "—")
        rows.append([str(idx), a.requirement, field_str, a.chinese_name, api, url, pts, a.match, "特征工程", a.note])

    # 补充字段
    for sf in SUPPLEMENTARY_FIELDS:
        idx += 1
        api, url, pts = _interface_info(sf.endpoint)
        rows.append(
            [
                str(idx),
                "（补充）",
                sf.tushare_field,
                sf.chinese_name,
                api,
                url,
                pts,
                "supplementary",
                sf.purpose,
                "",
            ]
        )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    # newline="" + lineterminator="\n"：CSV 写入用 LF 行尾，对齐 .gitattributes 的 eol=lf，
    # 同时避免 csv 模块默认的 \r\n 触发 git 规范化告警。
    with OUTPUT.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(
            [
                "序号",
                "BRD需求字段",
                "Tushare真实字段名",
                "字段中文翻译",
                "来源接口(vip优先)",
                "接口文档URL",
                "积分要求",
                "对齐类型",
                "用途",
                "备注",
            ]
        )
        w.writerows(rows)

    print(f"已生成 {OUTPUT}（{len(rows)} 行）")


if __name__ == "__main__":
    main()
