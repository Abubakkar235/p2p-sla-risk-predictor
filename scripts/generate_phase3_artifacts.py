from __future__ import annotations

import html
import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
NOTEBOOKS = ROOT / "notebooks"
REPORTS = ROOT / "reports"
FIGS = REPORTS / "figures"
SEED = 42
VENDOR_MIN_CASES = 200

np.random.seed(SEED)
NOTEBOOKS.mkdir(exist_ok=True)
REPORTS.mkdir(exist_ok=True)
FIGS.mkdir(exist_ok=True)


def e(value: object) -> str:
    return html.escape(str(value), quote=True)


def fmt(value: object) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, (float, np.floating)):
        return f"{value:.2f}"
    if isinstance(value, (int, np.integer)):
        return f"{value}"
    return str(value)


def md_table(df: pd.DataFrame, rows: int | None = None) -> str:
    view = df.head(rows).copy() if rows else df.copy()
    cols = list(view.columns)
    body = [[fmt(v) for v in row] for row in view.to_numpy()]
    return "\n".join(
        ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
        + ["| " + " | ".join(row) + " |" for row in body]
    )


def bar_svg(
    path: Path,
    labels,
    values,
    title: str,
    x_label: str = "",
    color: str = "#1f77b4",
    value_fmt: str = "{:.1f}",
    width: int = 920,
    height: int = 460,
) -> None:
    labels = [str(x) for x in labels]
    values = [0.0 if pd.isna(x) else float(x) for x in values]
    ml, mr, mt, mb = 260, 42, 58, 44
    ph, pw = height - mt - mb, width - ml - mr
    row_h = ph / max(len(labels), 1)
    max_v = max(max(values or [1.0]), 1.0)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fff"/>',
        f'<text x="{width/2}" y="28" text-anchor="middle" font-family="Arial" font-size="18" font-weight="700">{e(title)}</text>',
        f'<line x1="{ml}" y1="{mt}" x2="{ml}" y2="{height-mb}" stroke="#444"/>',
        f'<line x1="{ml}" y1="{height-mb}" x2="{width-mr}" y2="{height-mb}" stroke="#444"/>',
    ]
    for i, (label, value) in enumerate(zip(labels, values)):
        y = mt + i * row_h + row_h * 0.18
        bh = max(row_h * 0.55, 8)
        bw = value / max_v * pw
        shown = label if len(label) <= 42 else label[:39] + "..."
        parts.append(
            f'<text x="{ml-10}" y="{y+bh*.72}" text-anchor="end" font-family="Arial" font-size="11" fill="#333">{e(shown)}</text>'
        )
        parts.append(f'<rect x="{ml}" y="{y}" width="{bw:.2f}" height="{bh:.2f}" fill="{color}" opacity="0.86"/>')
        parts.append(
            f'<text x="{ml+bw+6}" y="{y+bh*.72}" font-family="Arial" font-size="11" fill="#222">{e(value_fmt.format(value))}</text>'
        )
    parts.append(f'<text x="{ml+pw/2}" y="{height-10}" text-anchor="middle" font-family="Arial" font-size="12">{e(x_label)}</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def grouped_svg(path: Path, labels, series: dict[str, pd.Series], title: str) -> None:
    palette = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]
    labels = [str(x) for x in labels]
    names = list(series)
    vals = {k: [float(x) for x in v] for k, v in series.items()}
    width, height = 920, 460
    ml, mr, mt, mb = 230, 60, 70, 48
    ph, pw = height - mt - mb, width - ml - mr
    row_h = ph / max(len(labels), 1)
    max_v = max([max(v) for v in vals.values()] or [1.0])
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fff"/>',
        f'<text x="{width/2}" y="28" text-anchor="middle" font-family="Arial" font-size="18" font-weight="700">{e(title)}</text>',
    ]
    for j, name in enumerate(names):
        x = ml + j * 210
        parts.append(f'<rect x="{x}" y="45" width="13" height="13" fill="{palette[j]}"/>')
        parts.append(f'<text x="{x+18}" y="56" font-family="Arial" font-size="12">{e(name)}</text>')
    for i, label in enumerate(labels):
        y0 = mt + i * row_h
        parts.append(f'<text x="{ml-10}" y="{y0+row_h*.62}" text-anchor="end" font-family="Arial" font-size="11">{e(label)}</text>')
        for j, name in enumerate(names):
            y = y0 + row_h * (0.18 + j * 0.32)
            bh = row_h * 0.28
            bw = vals[name][i] / max(max_v, 1.0) * pw
            parts.append(f'<rect x="{ml}" y="{y:.2f}" width="{bw:.2f}" height="{bh:.2f}" fill="{palette[j]}" opacity="0.86"/>')
            parts.append(f'<text x="{ml+bw+5}" y="{y+bh*.78:.2f}" font-family="Arial" font-size="10">{vals[name][i]:.1f}</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def process_svg(path: Path, edges: pd.DataFrame) -> None:
    coords = {
        "Purchase Request": (80, 170),
        "Budget Review": (260, 70),
        "Manager Approval": (300, 170),
        "Purchase Order": (500, 170),
        "Vendor Confirmation": (710, 170),
        "Goods Receipt": (710, 330),
        "Invoice Verification": (500, 330),
        "Payment": (300, 330),
    }
    max_f = edges["frequency"].max()
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="960" height="430" viewBox="0 0 960 430">',
        '<rect width="100%" height="100%" fill="#fff"/>',
        '<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,6 L9,3 z" fill="#555"/></marker></defs>',
        '<text x="480" y="28" text-anchor="middle" font-family="Arial" font-size="18" font-weight="700">Directly-Follows Process Map by Transition Frequency</text>',
    ]
    for _, row in edges.sort_values("frequency").iterrows():
        a, b, f = row["activity"], row["next_activity"], row["frequency"]
        x1, y1 = coords[a]
        x2, y2 = coords[b]
        sw = 1.5 + 7 * f / max_f
        if a == b:
            parts.append(
                f'<path d="M{x1+45},{y1-22} C{x1+110},{y1-85} {x1+160},{y1-10} {x1+48},{y1+8}" fill="none" stroke="#d62728" stroke-width="{sw:.2f}" opacity="0.62" marker-end="url(#arrow)"/>'
            )
            tx, ty = x1 + 100, y1 - 42
        else:
            parts.append(
                f'<line x1="{x1+58}" y1="{y1}" x2="{x2-58}" y2="{y2}" stroke="#555" stroke-width="{sw:.2f}" opacity="0.62" marker-end="url(#arrow)"/>'
            )
            tx, ty = (x1 + x2) / 2, (y1 + y2) / 2 - 8
        parts.append(f'<text x="{tx}" y="{ty}" text-anchor="middle" font-family="Arial" font-size="10">{int(f):,}</text>')
    for name, (x, y) in coords.items():
        parts.append(f'<rect x="{x-66}" y="{y-22}" width="132" height="44" rx="5" fill="#f7f9fb" stroke="#2f5d7c"/>')
        parts.append(f'<text x="{x}" y="{y+4}" text-anchor="middle" font-family="Arial" font-size="11">{e(name)}</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def load_and_analyze():
    events = pd.read_csv(RAW / "p2p_event_log.csv")
    cases = pd.read_csv(RAW / "p2p_case_summary.csv")
    events["timestamp_dt"] = pd.to_datetime(events["timestamp"], errors="coerce")
    cases["start_dt"] = pd.to_datetime(cases["start_time"], errors="coerce")
    cases["end_dt"] = pd.to_datetime(cases["end_time"], errors="coerce")

    es = events.sort_values(["case_id", "timestamp_dt", "event_id"]).copy()
    es["next_activity"] = es.groupby("case_id")["activity"].shift(-1)
    es["next_timestamp"] = es.groupby("case_id")["timestamp_dt"].shift(-1)
    es["elapsed_hours_to_next"] = (es["next_timestamp"] - es["timestamp_dt"]).dt.total_seconds() / 3600
    es["prev_activity"] = es.groupby("case_id")["activity"].shift(1)
    es["prev_timestamp"] = es.groupby("case_id")["timestamp_dt"].shift(1)
    es["hours_since_prev"] = (es["timestamp_dt"] - es["prev_timestamp"]).dt.total_seconds() / 3600

    seqs = es.groupby("case_id")["activity"].agg(tuple)
    vc = seqs.value_counts()
    rank = {seq: i for i, seq in enumerate(vc.index, 1)}
    case_vars = seqs.rename("sequence").reset_index()
    case_vars["variant_rank"] = case_vars["sequence"].map(rank)
    case_vars["activity_sequence"] = case_vars["sequence"].apply(lambda s: " -> ".join(s))
    case_vars = case_vars.merge(cases[["case_id", "sla_breached", "duration_days", "duration_hours", "priority", "category", "vendor_id"]], on="case_id")

    variants = (
        case_vars.groupby(["variant_rank", "activity_sequence"])
        .agg(
            cases=("case_id", "count"),
            sla_breaches=("sla_breached", "sum"),
            sla_breach_rate=("sla_breached", "mean"),
            avg_duration_days=("duration_days", "mean"),
            median_duration_days=("duration_days", "median"),
        )
        .reset_index()
        .sort_values("cases", ascending=False)
    )
    variants["case_pct"] = variants["cases"] / len(cases) * 100
    variants = variants[["variant_rank", "cases", "case_pct", "sla_breaches", "sla_breach_rate", "avg_duration_days", "median_duration_days", "activity_sequence"]]

    transitions = (
        es.dropna(subset=["next_activity"])
        .groupby(["activity", "next_activity"])
        .agg(
            occurrences=("case_id", "count"),
            avg_elapsed_hours=("elapsed_hours_to_next", "mean"),
            median_elapsed_hours=("elapsed_hours_to_next", "median"),
            p95_elapsed_hours=("elapsed_hours_to_next", lambda s: s.quantile(0.95)),
        )
        .reset_index()
    )
    transitions["from_to"] = transitions["activity"] + " -> " + transitions["next_activity"]
    transitions = transitions.sort_values("avg_elapsed_hours", ascending=False)

    activity = (
        es.groupby("activity")
        .agg(
            frequency=("case_id", "count"),
            avg_hours_since_prev=("hours_since_prev", "mean"),
            median_hours_since_prev=("hours_since_prev", "median"),
            p95_hours_since_prev=("hours_since_prev", lambda s: s.dropna().quantile(0.95) if s.notna().any() else np.nan),
        )
        .reset_index()
        .sort_values("avg_hours_since_prev", ascending=False, na_position="last")
    )

    repeat_flags = seqs.apply(lambda s: len(s) != len(set(s))).rename("has_rework").reset_index()
    rework_cases = cases.merge(repeat_flags, on="case_id")
    rework = (
        rework_cases.groupby("has_rework")
        .agg(
            cases=("case_id", "count"),
            avg_duration_days=("duration_days", "mean"),
            median_duration_days=("duration_days", "median"),
            sla_breaches=("sla_breached", "sum"),
            sla_breach_rate=("sla_breached", "mean"),
        )
        .reset_index()
    )
    rework["case_pct"] = rework["cases"] / len(cases) * 100

    repeat_case_counter, extra_counter = Counter(), Counter()
    for sequence in seqs:
        counts = Counter(sequence)
        for act, n in counts.items():
            if n > 1:
                repeat_case_counter[act] += 1
                extra_counter[act] += n - 1
    repeats = pd.DataFrame(
        {
            "activity": list(repeat_case_counter),
            "cases_with_repeat": list(repeat_case_counter.values()),
            "extra_repetitions": [extra_counter[a] for a in repeat_case_counter],
        }
    ).sort_values("cases_with_repeat", ascending=False)

    po_vc = es[(es["activity"] == "Purchase Order") & (es["next_activity"] == "Vendor Confirmation")]
    vendor_conf = (
        po_vc.groupby("vendor_id")
        .agg(
            vendor_confirmation_cases=("case_id", "nunique"),
            avg_vendor_confirmation_hours=("elapsed_hours_to_next", "mean"),
            median_vendor_confirmation_hours=("elapsed_hours_to_next", "median"),
            p95_vendor_confirmation_hours=("elapsed_hours_to_next", lambda s: s.quantile(0.95)),
        )
        .reset_index()
    )
    vendor_sla = (
        cases.groupby("vendor_id")
        .agg(
            total_cases=("case_id", "count"),
            sla_breaches=("sla_breached", "sum"),
            sla_breach_rate=("sla_breached", "mean"),
            avg_duration_days=("duration_days", "mean"),
            median_duration_days=("duration_days", "median"),
        )
        .reset_index()
    )
    vendors = vendor_sla.merge(vendor_conf, on="vendor_id", how="left")
    vendors["sample_size_flag"] = np.where(vendors["total_cases"] >= VENDOR_MIN_CASES, "adequate_sample", "small_sample")
    vendors["vendor_confirmation_zscore"] = (
        vendors["avg_vendor_confirmation_hours"] - vendors["avg_vendor_confirmation_hours"].mean()
    ) / vendors["avg_vendor_confirmation_hours"].std(ddof=0)
    vendor_response = vendors[vendors["total_cases"] >= VENDOR_MIN_CASES].sort_values("avg_vendor_confirmation_hours", ascending=False)
    vendor_sla_top = vendors[vendors["total_cases"] >= VENDOR_MIN_CASES].sort_values("sla_breach_rate", ascending=False)

    priority = (
        cases.groupby("priority")
        .agg(
            cases=("case_id", "count"),
            avg_duration_days=("duration_days", "mean"),
            median_duration_days=("duration_days", "median"),
            p95_duration_days=("duration_days", lambda s: s.quantile(0.95)),
            sla_breaches=("sla_breached", "sum"),
            sla_breach_rate=("sla_breached", "mean"),
        )
        .reset_index()
        .sort_values("avg_duration_days", ascending=False)
    )
    category = (
        cases.groupby("category")
        .agg(
            cases=("case_id", "count"),
            avg_duration_days=("duration_days", "mean"),
            median_duration_days=("duration_days", "median"),
            p95_duration_days=("duration_days", lambda s: s.quantile(0.95)),
            sla_breaches=("sla_breached", "sum"),
            sla_breach_rate=("sla_breached", "mean"),
        )
        .reset_index()
        .sort_values("avg_duration_days", ascending=False)
    )
    edges = es.dropna(subset=["next_activity"]).groupby(["activity", "next_activity"]).size().reset_index(name="frequency").sort_values("frequency", ascending=False)
    return events, cases, es, variants, transitions, activity, rework, repeats, vendors, vendor_response, vendor_sla_top, priority, category, edges


def build_figures(variants, transitions, rework, vendors, vendor_response, category, edges):
    process_svg(FIGS / "process_transition_frequency.svg", edges)
    bar_svg(
        FIGS / "top_process_variants.svg",
        [f"Variant {int(r.variant_rank)}" for r in variants.head(10).itertuples()],
        variants.head(10)["case_pct"],
        "Top Process Variants by Case Share",
        "Percent of cases",
        value_fmt="{:.2f}%",
    )
    bar_svg(
        FIGS / "transition_duration_chart.svg",
        transitions.head(10)["from_to"],
        transitions.head(10)["avg_elapsed_hours"],
        "Slowest Transitions by Average Elapsed Hours",
        "Average elapsed hours",
        color="#d62728",
        value_fmt="{:.1f} h",
    )
    ordered = rework.sort_values("has_rework")
    grouped_svg(
        FIGS / "rework_analysis.svg",
        ["No rework", "Rework"],
        {"Avg duration days": ordered["avg_duration_days"], "SLA breach rate %": ordered["sla_breach_rate"] * 100},
        "Rework Impact on Duration and SLA Breach Rate",
    )
    bar_svg(
        FIGS / "sla_breach_comparison.svg",
        category["category"],
        category["sla_breach_rate"] * 100,
        "SLA Breach Rate by Category",
        "SLA breach rate (%)",
        color="#ff7f0e",
        value_fmt="{:.1f}%",
    )
    grouped_svg(
        FIGS / "vendor_performance.svg",
        vendor_response.head(10)["vendor_id"],
        {
            "Avg PO to Vendor Confirmation hours": vendor_response.head(10)["avg_vendor_confirmation_hours"],
            "SLA breach rate %": vendor_response.head(10)["sla_breach_rate"] * 100,
        },
        "Vendor Confirmation Timing and SLA Rate - Adequate Samples",
    )


def build_report(events, cases, variants, transitions, activity, rework, repeats, vendors, vendor_response, vendor_sla_top, priority, category, edges):
    top_variant, second_variant, slowest = variants.iloc[0], variants.iloc[1], transitions.iloc[0]
    yes = rework[rework["has_rework"]].iloc[0]
    no = rework[~rework["has_rework"]].iloc[0]
    vendor_corr = vendors["avg_vendor_confirmation_hours"].corr(vendors["sla_breach_rate"])
    report = f"""# Process Mining Report - Phase 3

## Scope

This report uses the raw synthetic P2P datasets in `data/raw/` and does not modify them. No machine-learning model was trained. PM4Py is not installed in the current runtime, so the process map and process-mining metrics were computed with a reproducible pandas-based directly-follows analysis.

## Key Findings

- The dominant happy-path variant covers {top_variant.case_pct:.2f}% of cases and has an SLA breach rate of {top_variant.sla_breach_rate * 100:.2f}%.
- The second-largest variant includes Budget Review, covers {second_variant.case_pct:.2f}% of cases, and has a higher SLA breach rate of {second_variant.sla_breach_rate * 100:.2f}%.
- The slowest average transition is `{slowest.from_to}` at {slowest.avg_elapsed_hours:.1f} hours on average.
- Rework affects {int(yes.cases):,} cases ({yes.case_pct:.2f}%) and is associated with higher average duration ({yes.avg_duration_days:.2f} vs {no.avg_duration_days:.2f} days) and higher SLA breach rate ({yes.sla_breach_rate * 100:.2f}% vs {no.sla_breach_rate * 100:.2f}%).
- Vendor Confirmation timing differs materially by vendor. Among vendors with at least {VENDOR_MIN_CASES} cases, V031 has the highest average Purchase Order to Vendor Confirmation elapsed time.

## Process Map and Transition Frequency

![Process transition frequency](figures/process_transition_frequency.svg)

{md_table(edges)}

## Process Variants

Observed variants: **{len(variants)}**.

Top 10 variants by case count:

{md_table(variants.head(10))}

![Top process variants](figures/top_process_variants.svg)

Variants with Budget Review and repeated activities generally show higher SLA breach rates than the happy path. This is correlation, not proof that the additional steps independently cause breaches.

## Bottlenecks and Transition Timing

Timing is measured as elapsed time from one event timestamp to the next event timestamp within the same case. These values approximate waiting time between activities, not exact hands-on processing time.

{md_table(transitions[["from_to", "occurrences", "avg_elapsed_hours", "median_elapsed_hours", "p95_elapsed_hours"]])}

![Transition duration chart](figures/transition_duration_chart.svg)

The two largest average delays are `Purchase Order -> Vendor Confirmation` and `Vendor Confirmation -> Goods Receipt`, making supplier response and goods receipt timing the strongest process bottleneck candidates.

## Activity-Level Performance

{md_table(activity)}

`Goods Receipt` and `Vendor Confirmation` have the highest average elapsed time since the previous activity. `Purchase Request` has no previous-activity timing because it is the first logged activity.

## Rework Findings

{md_table(rework)}

Repeated activities by activity:

{md_table(repeats)}

![Rework analysis](figures/rework_analysis.svg)

Rework is concentrated in Invoice Verification, Manager Approval, and Vendor Confirmation. Rework cases have longer durations and higher SLA breach rates, so rework indicators should be considered for later prediction and monitoring.

## Vendor Findings

Vendor comparisons use an adequate-sample threshold of at least {VENDOR_MIN_CASES} total cases. In this dataset all 50 vendors meet that threshold, but the threshold is retained so future analyses avoid overinterpreting small samples.

Top vendors by slowest Purchase Order to Vendor Confirmation response:

{md_table(vendor_response[["vendor_id", "total_cases", "avg_vendor_confirmation_hours", "median_vendor_confirmation_hours", "p95_vendor_confirmation_hours", "sla_breach_rate", "vendor_confirmation_zscore"]].head(10))}

Top vendors by SLA breach rate:

{md_table(vendor_sla_top[["vendor_id", "total_cases", "sla_breaches", "sla_breach_rate", "avg_duration_days", "avg_vendor_confirmation_hours"]].head(10))}

![Vendor performance](figures/vendor_performance.svg)

Average Vendor Confirmation response time and vendor SLA breach rate have a high vendor-level correlation in this dataset ({vendor_corr:.2f}). This is useful as a diagnostic signal, but it should not be interpreted as causal without controlled analysis.

## SLA Findings by Priority and Category

### Priority

{md_table(priority)}

### Category

{md_table(category)}

![SLA breach comparison](figures/sla_breach_comparison.svg)

Low-priority cases have the longest average duration and the highest priority-level breach rate. Services and Maintenance have the highest category-level breach rates.

## Business Interpretation

The process appears mostly standardized around a seven-step happy path, but meaningful operational variation is introduced by Budget Review and by rework loops. The strongest timing pressure appears around vendor-facing and downstream receiving steps. Cases that require repeated approvals, vendor confirmations, or invoice checks are associated with longer cycle times and higher SLA breach rates.

## Data Limitations

- The event log has one timestamp per activity, so transition timing represents elapsed waiting time between events, not exact activity processing time.
- The data is synthetic, so operational interpretations should be framed as portfolio-project insights rather than real enterprise conclusions.
- All event statuses are `Completed`, so status has no analytical variation in the current event log.
- Vendor findings are observational. High vendor response time and SLA breach rate are correlated here, but causality is not established.
- Case-level duration and SLA outcome fields should be treated carefully later because they can leak target information into predictive models.

## Recommendations for Feature Engineering

- Variant rank or encoded activity sequence family available up to the prediction point.
- Directly-follows transition counts and elapsed-time features observed so far.
- Presence of Budget Review.
- Rework flags and repeat counts by activity, especially Invoice Verification, Manager Approval, and Vendor Confirmation.
- Vendor Confirmation elapsed time or vendor historical response features, computed using only prior cases or training-fold history.
- Vendor historical SLA breach rate with sample-size smoothing to avoid unstable estimates.
- Priority, category, department mix, purchase amount, and vendor id encodings.
- Early-cycle elapsed time features, such as time from Purchase Request to Manager Approval or Purchase Order.
- Bottleneck exposure indicators for slow transitions, especially Purchase Order to Vendor Confirmation and Vendor Confirmation to Goods Receipt.
"""
    (REPORTS / "process_mining_report.md").write_text(report, encoding="utf-8")


def build_notebook() -> None:
    cells = []

    def md(text: str) -> None:
        cells.append({"cell_type": "markdown", "metadata": {}, "source": text.strip().splitlines(True)})

    def code(text: str) -> None:
        cells.append({"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": text.strip().splitlines(True)})

    md("# Phase 3 - Process Mining\n\nThis notebook performs process-mining analysis on the synthetic P2P event log and case summary. It does not modify files under `data/raw/` and does not train machine-learning models.")
    code("""from pathlib import Path
from collections import Counter
import html
import importlib.util

import numpy as np
import pandas as pd

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
pd.set_option("display.max_columns", 120)
pd.set_option("display.max_colwidth", 220)

PROJECT_ROOT = Path.cwd() if (Path.cwd() / "data" / "raw").exists() else Path.cwd().parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
REPORT_DIR = PROJECT_ROOT / "reports"
FIG_DIR = REPORT_DIR / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)
EVENT_LOG_PATH = RAW_DIR / "p2p_event_log.csv"
CASE_SUMMARY_PATH = RAW_DIR / "p2p_case_summary.csv" """)
    md("## 1. Load Raw Event Log and Case Summary\n\nThe raw CSVs are loaded read-only. Derived figures are written under `reports/figures/`.")
    code("""events = pd.read_csv(EVENT_LOG_PATH)
cases = pd.read_csv(CASE_SUMMARY_PATH)
events["timestamp_dt"] = pd.to_datetime(events["timestamp"], errors="coerce")
cases["start_dt"] = pd.to_datetime(cases["start_time"], errors="coerce")
cases["end_dt"] = pd.to_datetime(cases["end_time"], errors="coerce")

pd.DataFrame([
    {"dataset": "p2p_event_log.csv", "rows": len(events), "columns": events.drop(columns=["timestamp_dt"]).shape[1], "path_exists": EVENT_LOG_PATH.exists()},
    {"dataset": "p2p_case_summary.csv", "rows": len(cases), "columns": cases.drop(columns=["start_dt", "end_dt"]).shape[1], "path_exists": CASE_SUMMARY_PATH.exists()},
])""")
    md("## 2. PM4Py Availability\n\nPM4Py is optional here. If unavailable, the notebook uses a pandas directly-follows process map.")
    code('pd.DataFrame({"package": ["pm4py"], "available": [importlib.util.find_spec("pm4py") is not None]})')
    md("## 3. Prepare Ordered Event Log")
    code("""events_sorted = events.sort_values(["case_id", "timestamp_dt", "event_id"]).copy()
events_sorted["next_activity"] = events_sorted.groupby("case_id")["activity"].shift(-1)
events_sorted["next_timestamp"] = events_sorted.groupby("case_id")["timestamp_dt"].shift(-1)
events_sorted["elapsed_hours_to_next"] = (events_sorted["next_timestamp"] - events_sorted["timestamp_dt"]).dt.total_seconds() / 3600
events_sorted["prev_activity"] = events_sorted.groupby("case_id")["activity"].shift(1)
events_sorted["prev_timestamp"] = events_sorted.groupby("case_id")["timestamp_dt"].shift(1)
events_sorted["hours_since_prev"] = (events_sorted["timestamp_dt"] - events_sorted["prev_timestamp"]).dt.total_seconds() / 3600
events_sorted.head()""")
    md("## 4. Process Map and Transition Frequency")
    code("""process_edges = (
    events_sorted.dropna(subset=["next_activity"])
    .groupby(["activity", "next_activity"])
    .size()
    .reset_index(name="frequency")
    .sort_values("frequency", ascending=False)
)
process_edges""")
    code("""def esc(value):
    return html.escape(str(value), quote=True)

def write_bar_svg(path, labels, values, title, x_label="", color="#1f77b4", value_fmt="{:.1f}", width=920, height=460):
    labels = [str(x) for x in labels]
    values = [0.0 if pd.isna(x) else float(x) for x in values]
    ml, mr, mt, mb = 260, 42, 58, 44
    ph, pw = height - mt - mb, width - ml - mr
    row_h = ph / max(len(labels), 1)
    max_v = max(max(values or [1.0]), 1.0)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">', '<rect width="100%" height="100%" fill="#fff"/>']
    parts.append(f'<text x="{width/2}" y="28" text-anchor="middle" font-family="Arial" font-size="18" font-weight="700">{esc(title)}</text>')
    for i, (label, value) in enumerate(zip(labels, values)):
        y = mt + i * row_h + row_h * 0.18
        bh = max(row_h * 0.55, 8)
        bw = value / max_v * pw
        shown = label if len(label) <= 42 else label[:39] + "..."
        parts.append(f'<text x="{ml-10}" y="{y+bh*.72}" text-anchor="end" font-family="Arial" font-size="11">{esc(shown)}</text>')
        parts.append(f'<rect x="{ml}" y="{y}" width="{bw:.2f}" height="{bh:.2f}" fill="{color}" opacity="0.86"/>')
        parts.append(f'<text x="{ml+bw+6}" y="{y+bh*.72}" font-family="Arial" font-size="11">{esc(value_fmt.format(value))}</text>')
    parts.append(f'<text x="{ml+pw/2}" y="{height-10}" text-anchor="middle" font-family="Arial" font-size="12">{esc(x_label)}</text></svg>')
    Path(path).write_text("\\n".join(parts), encoding="utf-8")

def write_grouped_bar_svg(path, labels, series, title):
    palette = ["#1f77b4", "#ff7f0e", "#2ca02c"]
    width, height = 920, 460
    ml, mr, mt, mb = 230, 60, 70, 48
    ph, pw = height - mt - mb, width - ml - mr
    labels = [str(x) for x in labels]
    vals = {k: [float(x) for x in v] for k, v in series.items()}
    row_h = ph / max(len(labels), 1)
    max_v = max([max(v) for v in vals.values()] or [1.0])
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">', '<rect width="100%" height="100%" fill="#fff"/>']
    parts.append(f'<text x="{width/2}" y="28" text-anchor="middle" font-family="Arial" font-size="18" font-weight="700">{esc(title)}</text>')
    for j, name in enumerate(vals):
        x = ml + j * 210
        parts.append(f'<rect x="{x}" y="45" width="13" height="13" fill="{palette[j]}"/><text x="{x+18}" y="56" font-family="Arial" font-size="12">{esc(name)}</text>')
    for i, label in enumerate(labels):
        y0 = mt + i * row_h
        parts.append(f'<text x="{ml-10}" y="{y0+row_h*.62}" text-anchor="end" font-family="Arial" font-size="11">{esc(label)}</text>')
        for j, name in enumerate(vals):
            y = y0 + row_h * (0.18 + j * 0.32)
            bh = row_h * 0.28
            bw = vals[name][i] / max(max_v, 1.0) * pw
            parts.append(f'<rect x="{ml}" y="{y:.2f}" width="{bw:.2f}" height="{bh:.2f}" fill="{palette[j]}" opacity="0.86"/><text x="{ml+bw+5}" y="{y+bh*.78:.2f}" font-family="Arial" font-size="10">{vals[name][i]:.1f}</text>')
    parts.append("</svg>")
    Path(path).write_text("\\n".join(parts), encoding="utf-8")

def write_process_map_svg(path, edges):
    coords = {"Purchase Request": (80, 170), "Budget Review": (260, 70), "Manager Approval": (300, 170), "Purchase Order": (500, 170), "Vendor Confirmation": (710, 170), "Goods Receipt": (710, 330), "Invoice Verification": (500, 330), "Payment": (300, 330)}
    max_f = edges["frequency"].max()
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="960" height="430" viewBox="0 0 960 430">', '<rect width="100%" height="100%" fill="#fff"/>', '<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,6 L9,3 z" fill="#555"/></marker></defs>', '<text x="480" y="28" text-anchor="middle" font-family="Arial" font-size="18" font-weight="700">Directly-Follows Process Map by Transition Frequency</text>']
    for _, row in edges.sort_values("frequency").iterrows():
        a, b, f = row["activity"], row["next_activity"], row["frequency"]
        x1, y1 = coords[a]; x2, y2 = coords[b]
        sw = 1.5 + 7 * f / max_f
        if a == b:
            parts.append(f'<path d="M{x1+45},{y1-22} C{x1+110},{y1-85} {x1+160},{y1-10} {x1+48},{y1+8}" fill="none" stroke="#d62728" stroke-width="{sw:.2f}" opacity="0.62" marker-end="url(#arrow)"/>')
            tx, ty = x1 + 100, y1 - 42
        else:
            parts.append(f'<line x1="{x1+58}" y1="{y1}" x2="{x2-58}" y2="{y2}" stroke="#555" stroke-width="{sw:.2f}" opacity="0.62" marker-end="url(#arrow)"/>')
            tx, ty = (x1 + x2) / 2, (y1 + y2) / 2 - 8
        parts.append(f'<text x="{tx}" y="{ty}" text-anchor="middle" font-family="Arial" font-size="10">{int(f):,}</text>')
    for name, (x, y) in coords.items():
        parts.append(f'<rect x="{x-66}" y="{y-22}" width="132" height="44" rx="5" fill="#f7f9fb" stroke="#2f5d7c"/><text x="{x}" y="{y+4}" text-anchor="middle" font-family="Arial" font-size="11">{esc(name)}</text>')
    parts.append("</svg>")
    Path(path).write_text("\\n".join(parts), encoding="utf-8")

write_process_map_svg(FIG_DIR / "process_transition_frequency.svg", process_edges)
FIG_DIR / "process_transition_frequency.svg" """)
    md("![Process transition frequency](../reports/figures/process_transition_frequency.svg)")
    md("## 5. Process Variants and SLA Breach Rates")
    code("""case_sequences = events_sorted.groupby("case_id")["activity"].agg(tuple)
variant_counts = case_sequences.value_counts()
variant_rank = {sequence: rank for rank, sequence in enumerate(variant_counts.index, start=1)}
case_variants = case_sequences.rename("sequence").reset_index()
case_variants["variant_rank"] = case_variants["sequence"].map(variant_rank)
case_variants["activity_sequence"] = case_variants["sequence"].apply(lambda sequence: " -> ".join(sequence))
case_variants = case_variants.merge(cases[["case_id", "sla_breached", "duration_days", "duration_hours", "priority", "category", "vendor_id"]], on="case_id")
variant_summary = (
    case_variants.groupby(["variant_rank", "activity_sequence"])
    .agg(cases=("case_id", "count"), sla_breaches=("sla_breached", "sum"), sla_breach_rate=("sla_breached", "mean"), avg_duration_days=("duration_days", "mean"), median_duration_days=("duration_days", "median"))
    .reset_index()
    .sort_values("cases", ascending=False)
)
variant_summary["case_pct"] = (variant_summary["cases"] / len(cases) * 100).round(2)
variant_summary["sla_breach_rate_pct"] = (variant_summary["sla_breach_rate"] * 100).round(2)
variant_summary[["variant_rank", "cases", "case_pct", "sla_breaches", "sla_breach_rate_pct", "avg_duration_days", "median_duration_days", "activity_sequence"]].head(10)""")
    code("""write_bar_svg(FIG_DIR / "top_process_variants.svg", [f"Variant {int(row.variant_rank)}" for row in variant_summary.head(10).itertuples()], variant_summary.head(10)["case_pct"], "Top Process Variants by Case Share", "Percent of cases", value_fmt="{:.2f}%")
FIG_DIR / "top_process_variants.svg" """)
    md("![Top process variants](../reports/figures/top_process_variants.svg)")
    md("## 6. Transition Timing")
    code("""transition_summary = (
    events_sorted.dropna(subset=["next_activity"])
    .groupby(["activity", "next_activity"])
    .agg(occurrences=("case_id", "count"), avg_elapsed_hours=("elapsed_hours_to_next", "mean"), median_elapsed_hours=("elapsed_hours_to_next", "median"), p95_elapsed_hours=("elapsed_hours_to_next", lambda series: series.quantile(0.95)))
    .reset_index()
)
transition_summary["from_to"] = transition_summary["activity"] + " -> " + transition_summary["next_activity"]
transition_summary = transition_summary.sort_values("avg_elapsed_hours", ascending=False)
transition_summary[["from_to", "occurrences", "avg_elapsed_hours", "median_elapsed_hours", "p95_elapsed_hours"]].round(2)""")
    code("""write_bar_svg(FIG_DIR / "transition_duration_chart.svg", transition_summary.head(10)["from_to"], transition_summary.head(10)["avg_elapsed_hours"], "Slowest Transitions by Average Elapsed Hours", "Average elapsed hours", color="#d62728", value_fmt="{:.1f} h")
FIG_DIR / "transition_duration_chart.svg" """)
    md("![Transition duration chart](../reports/figures/transition_duration_chart.svg)")
    md("## 7. Activity-Level Performance")
    code("""activity_performance = (
    events_sorted.groupby("activity")
    .agg(frequency=("case_id", "count"), avg_hours_since_prev=("hours_since_prev", "mean"), median_hours_since_prev=("hours_since_prev", "median"), p95_hours_since_prev=("hours_since_prev", lambda series: series.dropna().quantile(0.95) if series.notna().any() else np.nan))
    .reset_index()
    .sort_values("avg_hours_since_prev", ascending=False, na_position="last")
)
activity_performance.round(2)""")
    md("## 8. Rework Analysis")
    code("""repeat_case_flags = case_sequences.apply(lambda sequence: len(sequence) != len(set(sequence))).rename("has_rework").reset_index()
rework_cases = cases.merge(repeat_case_flags, on="case_id")
rework_summary = (
    rework_cases.groupby("has_rework")
    .agg(cases=("case_id", "count"), avg_duration_days=("duration_days", "mean"), median_duration_days=("duration_days", "median"), sla_breaches=("sla_breached", "sum"), sla_breach_rate=("sla_breached", "mean"))
    .reset_index()
)
rework_summary["case_pct"] = (rework_summary["cases"] / len(cases) * 100).round(2)
rework_summary["sla_breach_rate_pct"] = (rework_summary["sla_breach_rate"] * 100).round(2)
rework_summary""")
    code("""repeat_case_counter = Counter()
extra_repeat_counter = Counter()
for sequence in case_sequences:
    counts = Counter(sequence)
    for activity, count in counts.items():
        if count > 1:
            repeat_case_counter[activity] += 1
            extra_repeat_counter[activity] += count - 1
repeat_activity_summary = pd.DataFrame({"activity": list(repeat_case_counter.keys()), "cases_with_repeat": list(repeat_case_counter.values()), "extra_repetitions": [extra_repeat_counter[activity] for activity in repeat_case_counter]}).sort_values("cases_with_repeat", ascending=False)
repeat_activity_summary""")
    code("""ordered_rework = rework_summary.sort_values("has_rework")
write_grouped_bar_svg(FIG_DIR / "rework_analysis.svg", ["No rework", "Rework"], {"Avg duration days": ordered_rework["avg_duration_days"], "SLA breach rate %": ordered_rework["sla_breach_rate"] * 100}, "Rework Impact on Duration and SLA Breach Rate")
FIG_DIR / "rework_analysis.svg" """)
    md("![Rework analysis](../reports/figures/rework_analysis.svg)")
    md("## 9. Vendor Analysis")
    code("""purchase_to_vendor = events_sorted[(events_sorted["activity"] == "Purchase Order") & (events_sorted["next_activity"] == "Vendor Confirmation")].copy()
vendor_confirmation = (
    purchase_to_vendor.groupby("vendor_id")
    .agg(vendor_confirmation_cases=("case_id", "nunique"), avg_vendor_confirmation_hours=("elapsed_hours_to_next", "mean"), median_vendor_confirmation_hours=("elapsed_hours_to_next", "median"), p95_vendor_confirmation_hours=("elapsed_hours_to_next", lambda series: series.quantile(0.95)))
    .reset_index()
)
vendor_sla = (
    cases.groupby("vendor_id")
    .agg(total_cases=("case_id", "count"), sla_breaches=("sla_breached", "sum"), sla_breach_rate=("sla_breached", "mean"), avg_duration_days=("duration_days", "mean"), median_duration_days=("duration_days", "median"))
    .reset_index()
)
adequate_vendor_threshold = 200
vendor_performance = vendor_sla.merge(vendor_confirmation, on="vendor_id", how="left")
vendor_performance["sample_size_flag"] = np.where(vendor_performance["total_cases"] >= adequate_vendor_threshold, "adequate_sample", "small_sample")
vendor_performance["vendor_confirmation_zscore"] = (vendor_performance["avg_vendor_confirmation_hours"] - vendor_performance["avg_vendor_confirmation_hours"].mean()) / vendor_performance["avg_vendor_confirmation_hours"].std(ddof=0)
vendor_response_top = vendor_performance[vendor_performance["total_cases"] >= adequate_vendor_threshold].sort_values("avg_vendor_confirmation_hours", ascending=False)
vendor_response_top.head(10).round(2)""")
    code("""vendor_sla_top = vendor_performance[vendor_performance["total_cases"] >= adequate_vendor_threshold].sort_values("sla_breach_rate", ascending=False)
vendor_sla_top.head(10).round(2)""")
    code('pd.DataFrame({"metric": ["vendor_response_vs_sla_breach_rate_correlation"], "value": [vendor_performance["avg_vendor_confirmation_hours"].corr(vendor_performance["sla_breach_rate"])]})')
    code("""write_grouped_bar_svg(FIG_DIR / "vendor_performance.svg", vendor_response_top.head(10)["vendor_id"], {"Avg PO to Vendor Confirmation hours": vendor_response_top.head(10)["avg_vendor_confirmation_hours"], "SLA breach rate %": vendor_response_top.head(10)["sla_breach_rate"] * 100}, "Vendor Confirmation Timing and SLA Rate - Adequate Samples")
FIG_DIR / "vendor_performance.svg" """)
    md("![Vendor performance](../reports/figures/vendor_performance.svg)")
    md("## 10. Priority and Category Analysis")
    code("""priority_summary = (
    cases.groupby("priority")
    .agg(cases=("case_id", "count"), avg_duration_days=("duration_days", "mean"), median_duration_days=("duration_days", "median"), p95_duration_days=("duration_days", lambda series: series.quantile(0.95)), sla_breaches=("sla_breached", "sum"), sla_breach_rate=("sla_breached", "mean"))
    .reset_index()
    .sort_values("avg_duration_days", ascending=False)
)
priority_summary["sla_breach_rate_pct"] = (priority_summary["sla_breach_rate"] * 100).round(2)
priority_summary.round(2)""")
    code("""category_summary = (
    cases.groupby("category")
    .agg(cases=("case_id", "count"), avg_duration_days=("duration_days", "mean"), median_duration_days=("duration_days", "median"), p95_duration_days=("duration_days", lambda series: series.quantile(0.95)), sla_breaches=("sla_breached", "sum"), sla_breach_rate=("sla_breached", "mean"))
    .reset_index()
    .sort_values("avg_duration_days", ascending=False)
)
category_summary["sla_breach_rate_pct"] = (category_summary["sla_breach_rate"] * 100).round(2)
category_summary.round(2)""")
    code("""write_bar_svg(FIG_DIR / "sla_breach_comparison.svg", category_summary["category"], category_summary["sla_breach_rate"] * 100, "SLA Breach Rate by Category", "SLA breach rate (%)", color="#ff7f0e", value_fmt="{:.1f}%")
FIG_DIR / "sla_breach_comparison.svg" """)
    md("![SLA breach comparison](../reports/figures/sla_breach_comparison.svg)")
    md("## 11. Feature Engineering Candidates for Later SLA-Breach Prediction\n\nNo model is trained here. These are candidate feature families to evaluate later with leakage controls.")
    code("""pd.DataFrame({
    "feature_family": ["variant_family", "directly_follows_counts", "elapsed_transition_times", "budget_review_flag", "rework_flags", "activity_repeat_counts", "vendor_response_history", "vendor_sla_history_smoothed", "priority_category_purchase_amount", "early_cycle_elapsed_time", "bottleneck_exposure_flags"],
    "why_consider": ["Major variants show different SLA breach rates.", "Transition structure captures process path deviations.", "Slow transitions are associated with longer cycle time.", "Budget Review variants show elevated SLA breach rates.", "Rework cases have higher duration and breach rates.", "Repeated Invoice Verification, Manager Approval, and Vendor Confirmation are concentrated rework signals.", "Vendor Confirmation response varies substantially by vendor.", "Historical vendor behavior may be predictive if computed without leakage.", "Priority and category are associated with different durations and breach rates.", "Early elapsed time may indicate emerging delay risk.", "Exposure to slow PO-to-vendor or vendor-to-receipt gaps may flag risk."],
    "leakage_note": ["Use only sequence known at prediction time.", "Use only completed transitions available at prediction time.", "Do not use future transition durations.", "Safe only after Budget Review is observed or known.", "Safe only for repeats observed before prediction.", "Use counts observed before prediction.", "Compute from prior cases or training folds only.", "Smooth and compute out-of-fold to avoid target leakage.", "Usually safe if known at case start.", "Define a fixed prediction checkpoint.", "Avoid using full-case duration or post-outcome information."],
})""")
    nb = {
        "cells": cells,
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3.12"}},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    (NOTEBOOKS / "02_process_mining.ipynb").write_text(json.dumps(nb, indent=2), encoding="utf-8")


def main() -> None:
    data = load_and_analyze()
    events, cases, es, variants, transitions, activity, rework, repeats, vendors, vendor_response, vendor_sla_top, priority, category, edges = data
    build_figures(variants, transitions, rework, vendors, vendor_response, category, edges)
    build_report(events, cases, variants, transitions, activity, rework, repeats, vendors, vendor_response, vendor_sla_top, priority, category, edges)
    build_notebook()
    print("created", NOTEBOOKS / "02_process_mining.ipynb")
    print("created", REPORTS / "process_mining_report.md")
    print("figures", len(list(FIGS.glob("*.svg"))))


if __name__ == "__main__":
    main()
