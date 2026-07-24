"""校验 data/test/YYMMDD.csv 的报告期是否为 Tushare 最新。

对每只股独立重查 income_vip(max end_date)，与 CSV 记录值逐一比对；
并按 today 推算预期最新报告期，确保 end_date 不陈旧。
独立重查不读缓存，直接对质 Tushare。用法：
  uv run python scripts/verify_latest.py [--csv PATH]
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import sys
from pathlib import Path
from typing import Any

# 自举项目根到 sys.path，便于 `uv run python scripts/verify_latest.py` 直接运行
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import tushare as ts  # noqa: E402

from src.config import get_settings  # noqa: E402
from src.schemas.financial import ALL_OUTPUT_COLUMNS  # noqa: E402
from src.utils.period import expected_latest_period  # noqa: E402


def _max_field(records: list[dict], field: str) -> str | None:
    """取记录列表中 field 最大值；无则 None。"""
    dated = [r[field] for r in records if r.get(field)]
    return max(dated) if dated else None


def cross_check_latest(pro: Any, ts_code: str) -> str | None:
    """独立重查 Tushare，返回 income 最新 end_date。"""
    inc = pro.query("income_vip", ts_code=ts_code, fields="ts_code,end_date").to_dict(
        "records"
    )
    return _max_field(inc, "end_date")


def read_csv_rows(csv_path: Path) -> list[dict[str, str | None]]:
    """读特征 CSV，按 ALL_OUTPUT_COLUMNS 位置提取 ts_code/end_date。"""
    text = csv_path.read_text(encoding="utf-8-sig")
    rows = list(csv.reader(text.splitlines()))
    if not rows:
        return []
    idx = {c: i for i, c in enumerate(ALL_OUTPUT_COLUMNS)}
    out: list[dict[str, str | None]] = []
    for r in rows[1:]:
        if not r or not r[0].strip():
            continue
        cells = [c.strip() for c in r]
        out.append(
            {
                "ts_code": cells[idx["ts_code"]],
                "end_date": cells[idx["end_date"]] or None,
            }
        )
    return out


def verify_csv(
    pro: Any, csv_path: Path, today: _dt.date | None = None
) -> list[dict[str, Any]]:
    """校验 CSV 每行：end_date==Tushare最新 且 ≥ 预期报告期。"""
    today = today or _dt.date.today()
    expected = expected_latest_period(today)
    rows = read_csv_rows(csv_path)
    results: list[dict[str, Any]] = []
    for row in rows:
        tushare_end = cross_check_latest(pro, row["ts_code"])
        csv_end = row["end_date"]
        results.append(
            {
                "ts_code": row["ts_code"],
                "csv_end_date": csv_end,
                "tushare_end_date": tushare_end,
                "expected_min": expected,
                "ok_end": csv_end is not None and csv_end == tushare_end,
                "ok_fresh": csv_end is not None and csv_end >= expected,
            }
        )
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="校验冒烟 CSV 数据是否为 Tushare 最新")
    parser.add_argument(
        "--csv",
        type=Path,
        default=None,
        help="特征 CSV 路径；默认取 data/test 下最新的 YYMMDD.csv",
    )
    args = parser.parse_args()

    csv_path = args.csv
    if csv_path is None:
        test_dir = get_settings().data_root / "test"
        csvs = sorted(test_dir.glob("[0-9]" * 6 + ".csv"))
        if not csvs:
            raise SystemExit(f"未在 {test_dir} 找到 YYMMDD.csv，请用 --csv 指定")
        csv_path = csvs[-1]

    settings = get_settings()
    token = settings.tushare_token.strip()
    if not token:
        raise SystemExit("未配置 TUSHARE_TOKEN，请在 .env 填入")
    ts.set_token(token)
    pro = ts.pro_api()

    # Windows 控制台默认 GBK，重定向为 utf-8 以输出 emoji
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, ValueError):
        pass

    today = _dt.date.today()
    print(f"校验文件: {csv_path}")
    print(f"今天    : {today}  预期最新报告期 ≥ {expected_latest_period(today)}")
    print(f"{'ts_code':<14}{'CSV end_date':<14}{'Tushare':<14}结果")
    results = verify_csv(pro, csv_path, today)
    all_ok = True
    for r in results:
        ok = r["ok_end"] and r["ok_fresh"]
        all_ok = all_ok and ok
        flag = "✅" if ok else "❌"
        print(
            f"{r['ts_code']:<14}{(r['csv_end_date'] or '-'):<14}{(r['tushare_end_date'] or '-'):<14}{flag}"
        )
        if not ok:
            fresh_msg = (
                "OK" if r["ok_fresh"] else f"{r['csv_end_date']} < {r['expected_min']}"
            )
            print(f"    end {'==' if r['ok_end'] else '!='} | fresh {fresh_msg}")
    print(f"\n{'全部通过' if all_ok else '存在不一致，请检查'} ({len(results)} 股)")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
