"""
Application Funnel — Applications & Shortlisting (Task 4)
------------------------------------------------------------
Tracks each APPLICATION (not just each candidate) through the
post-apply review pipeline: Applied -> Screened -> Shortlisted ->
Interview Scheduled -> Selected.

Swap load_data() for a real DB query / API call when ready.
"""

import pandas as pd
import matplotlib.pyplot as plt

FUNNEL_STAGES = ["Applied", "Screened", "Shortlisted", "Interview Scheduled", "Selected"]


def load_data(path: str = "application_funnel_dataset.csv") -> pd.DataFrame:
    """Load event-level application data. One row = one application
    reaching one stage."""
    df = pd.read_csv(path, parse_dates=["event_date"])
    return df


def build_funnel(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse event-level data into per-company application-stage counts.

    Counts DISTINCT application_id per stage per company (an application
    'reaches' a stage if it has a row at that stage or beyond).
    """
    stage_rank = {s: i for i, s in enumerate(FUNNEL_STAGES)}
    df["stage_rank"] = df["stage"].map(stage_rank)

    furthest = (
        df.dropna(subset=["stage_rank"])
        .sort_values("stage_rank")
        .groupby(["company_id", "company_name", "application_id"])
        .agg(max_rank=("stage_rank", "max"))
        .reset_index()
    )

    rows = []
    for company_id, grp in furthest.groupby("company_id"):
        company_name = grp["company_name"].iloc[0]
        for stage, rank in stage_rank.items():
            count = (grp["max_rank"] >= rank).sum()
            rows.append({"company_id": company_id, "company_name": company_name,
                          "stage": stage, "count": count})

    funnel = pd.DataFrame(rows)
    funnel["stage"] = pd.Categorical(funnel["stage"], categories=FUNNEL_STAGES, ordered=True)
    funnel = funnel.sort_values(["company_id", "stage"])

    funnel["conv_vs_prev_%"] = (
        funnel.groupby("company_id")["count"].pct_change().fillna(0) * 100 + 100
    ).round(1)
    funnel.loc[funnel["stage"] == FUNNEL_STAGES[0], "conv_vs_prev_%"] = 100.0

    funnel["conv_vs_top_%"] = funnel.groupby("company_id")["count"].transform(
        lambda s: (s / s.iloc[0] * 100).round(1)
    )

    return funnel.reset_index(drop=True)


def plot_funnel(funnel: pd.DataFrame, out_path: str = "application_funnel.png"):
    companies = funnel["company_name"].unique()
    fig, axes = plt.subplots(1, len(companies), figsize=(6 * len(companies), 5), squeeze=False)

    for ax, company in zip(axes[0], companies):
        sub = funnel[funnel["company_name"] == company]
        ax.barh(sub["stage"].astype(str), sub["count"], color="#DD8452")
        ax.invert_yaxis()
        ax.set_title(f"{company} — Application Funnel")
        ax.set_xlabel("Applications")
        for i, (count, pct) in enumerate(zip(sub["count"], sub["conv_vs_top_%"])):
            ax.text(count, i, f"  {count} ({pct}%)", va="center")

    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    print(f"Saved chart to {out_path}")


if __name__ == "__main__":
    data = load_data("application_funnel_dataset.csv")
    funnel = build_funnel(data)
    print(funnel.to_string(index=False))
    funnel.to_csv("application_funnel_output.csv", index=False)
    plot_funnel(funnel)
