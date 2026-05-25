"""
Statistical significance tests for the Royal Spin A/B experiment.

Tests:
  1. Welch t-test on per-player ARPU (unequal variances assumed)
  2. Two-proportion Z-test on payer conversion rate

Prints a summary table with p-values, 95% confidence intervals, and
Cohen's d (ARPU) / Cohen's h (conversion rate) as effect size measures.

Usage: python stats_test.py
"""

import math
import sqlite3

import numpy as np
from scipy import stats

import config


def load_data(conn: sqlite3.Connection):
    # Per-player revenue (including $0 for non-payers) within experiment groups
    rows = conn.execute("""
        SELECT p.experiment_group,
               COALESCE(SUM(t.amount_usd), 0) AS revenue
        FROM players p
        LEFT JOIN transactions t ON t.player_id = p.player_id
        WHERE p.experiment_group IN ('Control', 'Treatment')
        GROUP BY p.player_id, p.experiment_group
    """).fetchall()

    ctrl_rev = np.array([r[1] for r in rows if r[0] == "Control"],  dtype=float)
    trt_rev  = np.array([r[1] for r in rows if r[0] == "Treatment"], dtype=float)

    # Payer counts per group for the Z-test
    conv = {
        r[0]: (r[1], r[2])
        for r in conn.execute("""
            SELECT p.experiment_group,
                   COUNT(DISTINCT t.player_id) AS payers,
                   COUNT(DISTINCT p.player_id) AS total
            FROM players p
            LEFT JOIN transactions t ON t.player_id = p.player_id
            WHERE p.experiment_group IN ('Control', 'Treatment')
            GROUP BY p.experiment_group
        """).fetchall()
    }

    return ctrl_rev, trt_rev, conv


def cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    pooled_std = math.sqrt((a.std(ddof=1)**2 + b.std(ddof=1)**2) / 2)
    return (b.mean() - a.mean()) / pooled_std if pooled_std else 0.0


def cohens_h(p1: float, p2: float) -> float:
    return 2 * math.asin(math.sqrt(p2)) - 2 * math.asin(math.sqrt(p1))


def arpu_test(ctrl: np.ndarray, trt: np.ndarray) -> dict:
    t_stat, p_val = stats.ttest_ind(ctrl, trt, equal_var=False)

    # 95% CI on the difference in means
    diff = trt.mean() - ctrl.mean()
    se   = math.sqrt(ctrl.var(ddof=1) / len(ctrl) + trt.var(ddof=1) / len(trt))
    df   = (ctrl.var(ddof=1)/len(ctrl) + trt.var(ddof=1)/len(trt))**2 / (
           (ctrl.var(ddof=1)/len(ctrl))**2/(len(ctrl)-1) +
           (trt.var(ddof=1)/len(trt))**2/(len(trt)-1))
    t_crit = stats.t.ppf(0.975, df)
    ci_lo, ci_hi = diff - t_crit * se, diff + t_crit * se

    return {
        "metric":    "ARPU",
        "control":   f"${ctrl.mean():.2f}",
        "treatment": f"${trt.mean():.2f}",
        "diff":      f"+${diff:.2f}",
        "ci_95":     f"(${ci_lo:+.2f}, ${ci_hi:+.2f})",
        "p_value":   p_val,
        "effect":    f"d = {cohens_d(ctrl, trt):.3f}",
        "n_ctrl":    len(ctrl),
        "n_trt":     len(trt),
    }


def conversion_test(conv: dict) -> dict:
    ctrl_payers = conv["Control"][0]
    ctrl_total  = conv["Control"][1]
    trt_payers  = conv["Treatment"][0]
    trt_total   = conv["Treatment"][1]

    p_ctrl = ctrl_payers / ctrl_total
    p_trt  = trt_payers  / trt_total
    diff   = p_trt - p_ctrl

    # Pooled Z-test
    p_pool = (ctrl_payers + trt_payers) / (ctrl_total + trt_total)
    se     = math.sqrt(p_pool * (1 - p_pool) * (1/ctrl_total + 1/trt_total))
    z_stat = diff / se if se else 0.0
    p_val  = 2 * (1 - stats.norm.cdf(abs(z_stat)))

    # 95% CI on difference in proportions (unpooled SE)
    se_ci  = math.sqrt(p_ctrl*(1-p_ctrl)/ctrl_total + p_trt*(1-p_trt)/trt_total)
    ci_lo  = diff - 1.96 * se_ci
    ci_hi  = diff + 1.96 * se_ci

    return {
        "metric":    "Conversion rate",
        "control":   f"{p_ctrl*100:.2f}%",
        "treatment": f"{p_trt*100:.2f}%",
        "diff":      f"{diff*100:+.2f}pp",
        "ci_95":     f"({ci_lo*100:+.2f}pp, {ci_hi*100:+.2f}pp)",
        "p_value":   p_val,
        "effect":    f"h = {cohens_h(p_ctrl, p_trt):.3f}",
        "n_ctrl":    ctrl_total,
        "n_trt":     trt_total,
    }


def interpret(p: float, effect: str) -> str:
    sig = "significant" if p < 0.05 else "not significant"
    mag = effect.split("=")[1].strip()
    val = abs(float(mag))
    # Cohen's d thresholds: 0.2 small, 0.5 medium, 0.8 large
    # Cohen's h thresholds: 0.2 small, 0.5 medium, 0.8 large (same scale)
    size = "large" if val >= 0.8 else ("medium" if val >= 0.5 else ("small" if val >= 0.2 else "negligible"))
    return f"{sig.capitalize()}, {size} effect"


def print_results(results: list[dict]) -> None:
    print("\n" + "="*70)
    print("  Royal Spin A/B Test — Statistical Significance")
    print("="*70)
    for r in results:
        sig_str = "[SIGNIFICANT]" if r["p_value"] < 0.05 else "[not significant]"
        print(f"\n  {r['metric']}")
        print(f"    Control:    {r['control']}  (n={r['n_ctrl']:,})")
        print(f"    Treatment:  {r['treatment']}  (n={r['n_trt']:,})")
        print(f"    Difference: {r['diff']}  95% CI: {r['ci_95']}")
        print(f"    p-value:    {r['p_value']:.4f}   {sig_str}")
        interp = r.get("_interp") or interpret(r["p_value"], r["effect"])
        print(f"    Effect size: {r['effect']}  =>  {interp}")
    print("\n" + "="*70 + "\n")


def mannwhitney_test(ctrl: np.ndarray, trt: np.ndarray) -> dict:
    stat, p_val = stats.mannwhitneyu(ctrl, trt, alternative="two-sided")
    # Rank-biserial correlation as effect size (r = 1 - 2U / n1*n2)
    n1, n2 = len(ctrl), len(trt)
    r = 1 - (2 * stat) / (n1 * n2)
    size = "large" if abs(r) >= 0.5 else ("medium" if abs(r) >= 0.3 else ("small" if abs(r) >= 0.1 else "negligible"))
    sig = "Significant" if p_val < 0.05 else "Not significant"
    return {
        "metric":    "ARPU (Mann-Whitney U)",
        "control":   f"median ${np.median(ctrl):.2f}",
        "treatment": f"median ${np.median(trt):.2f}",
        "diff":      f"U={stat:,.0f}",
        "ci_95":     "n/a (rank-based)",
        "p_value":   p_val,
        "effect":    f"r = {r:.3f}",
        "n_ctrl":    n1,
        "n_trt":     n2,
        "_interp":   f"{sig}, {size} effect",
    }


def get_results(conn: sqlite3.Connection) -> list[dict]:
    ctrl_rev, trt_rev, conv = load_data(conn)
    return [
        arpu_test(ctrl_rev, trt_rev),
        mannwhitney_test(ctrl_rev, trt_rev),
        conversion_test(conv),
    ]


def main() -> None:
    conn = sqlite3.connect(config.DB_PATH)
    results = get_results(conn)
    conn.close()
    print_results(results)


if __name__ == "__main__":
    main()
