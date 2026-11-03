"""Every calculation in the project, as small functions that read data/instagram_analytics.csv.

Each function returns plain pandas objects or numbers, so the charts, the report, the notebook and the tests all
share one version of every figure.
"""

from __future__ import annotations

from functools import cache
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split

DATA = Path(__file__).resolve().parent.parent / "data"

COUNTS = ["likes", "comments", "shares", "saves", "reach", "impressions", "followers_gained"]
INTERACTIONS = ["likes", "comments", "shares", "saves"]
GROUPS = {"media_type": "format", "content_category": "category", "traffic_source": "traffic source"}
OUTCOMES = ["engagement_rate", "followers_gained", "reach", "likes", "saves", "shares"]
SPLIT = "2025-08-01"  # Train on posts before August 2025, test on the four months after
SEED = 42


@cache
def posts() -> pd.DataFrame:
    """Every post, with its upload date parsed and its interactions added up."""
    df = pd.read_csv(DATA / "instagram_analytics.csv", parse_dates=["upload_date"])
    df["interactions"] = df[INTERACTIONS].sum(axis=1)
    df["weekday"] = df["upload_date"].dt.day_name()
    df["month"] = df["upload_date"].dt.to_period("M").astype(str)
    return df


# 1. The engagement rate is a formula -------------------------------------------------------------

def formula() -> dict:
    """How closely the engagement rate matches interactions divided by impressions, and by reach."""
    df = posts()
    by_impressions = df["interactions"] / df["impressions"] * 100
    by_reach = df["interactions"] / df["reach"] * 100
    return {
        "match": float(((by_impressions - df["engagement_rate"]).abs() <= 0.005 + 1e-9).mean()),
        "r_impressions": float(np.corrcoef(by_impressions, df["engagement_rate"])[0, 1]),
        "r_reach": float(np.corrcoef(by_reach, df["engagement_rate"])[0, 1]),
    }


def impossible() -> dict:
    """Posts with more interactions than impressions, which gives a rate above 100%."""
    rate = posts()["engagement_rate"]
    return {
        "over_100": int((rate > 100).sum()),
        "share": float((rate > 100).mean()),
        "max": float(rate.max()),
        "mean": float(rate.mean()),
        "median": float(rate.median()),
        "mean_without": float(rate[rate <= 100].mean()),
    }


def rate_bands() -> pd.Series:
    """How many posts fall in each band of engagement rate."""
    bands = pd.cut(
        posts()["engagement_rate"], [0, 5, 10, 20, 50, 100, np.inf],
        labels=["Under 5%", "5–10%", "10–20%", "20–50%", "50–100%", "Over 100%"],
    )
    return bands.value_counts().sort_index()


# 2 and 3. Group comparisons ----------------------------------------------------------------------

def by_group(group: str, outcome: str, how: str = "median") -> pd.Series:
    """The median (or mean) outcome in each group, smallest first."""
    return posts().groupby(group)[outcome].agg(how).sort_values()


def group_test(group: str, outcome: str) -> float:
    """Kruskal–Wallis p-value: could the groups' differences be chance? Robust to the extreme rates."""
    df = posts()
    return float(stats.kruskal(*[rows[outcome] for _, rows in df.groupby(group)]).pvalue)


def bootstrap_median(group: str, outcome: str, draws: int = 1000) -> pd.DataFrame:
    """Each group's median with a 95% bootstrap interval, fixed seed."""
    rng = np.random.default_rng(SEED)
    rows = {}
    for name, values in posts().groupby(group)[outcome]:
        values = values.to_numpy()
        medians = np.median(rng.choice(values, (draws, len(values))), axis=1)
        rows[name] = {"median": np.median(values), "low": np.quantile(medians, 0.025), "high": np.quantile(medians, 0.975)}
    return pd.DataFrame(rows).T.sort_values("median")


def first_version_claims() -> pd.DataFrame:
    """The comparisons the first version charted: mean engagement by format and mean followers by category."""
    fmt = by_group("media_type", "engagement_rate", "mean")
    cat = by_group("content_category", "followers_gained", "mean")
    return pd.DataFrame(
        {
            "comparison": ["Engagement rate by format", "Followers gained by category"],
            "lowest": [fmt.iloc[0], cat.iloc[0]],
            "highest": [fmt.iloc[-1], cat.iloc[-1]],
            "p_value": [group_test("media_type", "engagement_rate"), group_test("content_category", "followers_gained")],
        }
    )


# 4. Nothing is related to anything ---------------------------------------------------------------

def correlations() -> pd.DataFrame:
    """Correlations between the raw counts."""
    return posts()[COUNTS].corr()


def strongest_link() -> tuple[str, str, float]:
    """The strongest correlation between two counts, leaving out reach and impressions, which are built together."""
    table = correlations()
    best = ("", "", 0.0)
    for a, b in combinations(COUNTS, 2):
        if {a, b} == {"reach", "impressions"}:
            continue
        if abs(table.loc[a, b]) > abs(best[2]):
            best = (a, b, float(table.loc[a, b]))
    return best


def format_by_source() -> float:
    """Chi-squared p-value: do formats reach people through different routes? Reels should lean on the Reels feed."""
    df = posts()
    return float(stats.chi2_contingency(pd.crosstab(df["media_type"], df["traffic_source"]))[1])


def reels_in_reels_feed() -> dict:
    df = posts()
    feed = df[df["traffic_source"] == "Reels Feed"]
    return {"reels": float((feed["media_type"] == "Reel").mean()), "overall": float((df["media_type"] == "Reel").mean())}


# 5. Signs the data was generated -----------------------------------------------------------------

def likes_by_tenth() -> pd.Series:
    """Posts in each tenth of the likes range. Real likes pile up near zero; these are spread evenly."""
    likes = posts()["likes"]
    edges = np.linspace(0, 200_000, 11)
    labels = [f"{int(lo / 1000)}–{int(hi / 1000)}k" for lo, hi in zip(edges[:-1], edges[1:])]
    return pd.cut(likes, edges, labels=labels, include_lowest=True).value_counts().sort_index()


def uniform_tests() -> pd.Series:
    """Kolmogorov–Smirnov p-values against an even spread between each column's lowest and highest value.

    A high p-value means the column is consistent with numbers drawn evenly at random.
    """
    df = posts()
    columns = ["likes", "comments", "shares", "saves", "reach", "caption_length", "followers_gained"]
    out = {}
    for column in columns:
        values = df[column]
        scaled = (values - values.min()) / (values.max() - values.min())
        out[column] = stats.kstest(scaled, "uniform").pvalue
    out["impressions minus reach"] = stats.kstest((df["impressions"] - df["reach"]) / 500_000, "uniform").pvalue
    return pd.Series(out)


def fingerprints() -> dict:
    df = posts()
    clock = df["upload_date"].dt.strftime("%H:%M:%S.%f")
    extra = df["impressions"] - df["reach"]
    shares = df["media_type"].value_counts(normalize=True)
    return {
        "posts": len(df),
        "clock_times": int(clock.nunique()),
        "clock": clock.iloc[0][:8],
        "first": df["upload_date"].min().strftime("%-d %B %Y"),
        "last": df["upload_date"].max().strftime("%-d %B %Y"),
        "extra_min": int(extra.min()), "extra_max": int(extra.max()),
        "format_low": float(shares.min()), "format_high": float(shares.max()),
        "categories": int(df["content_category"].nunique()),
        "sources": int(df["traffic_source"].nunique()),
    }


# 6. Chance alone produces "findings" -------------------------------------------------------------

def all_group_tests() -> pd.DataFrame:
    """Every grouping against every outcome, the way a dashboard would slice them."""
    rows = [
        {"group": GROUPS[group], "outcome": outcome, "p_value": group_test(group, outcome)}
        for group in GROUPS for outcome in OUTCOMES
    ]
    rows += [{"group": "weekday", "outcome": outcome, "p_value": group_test("weekday", outcome)} for outcome in OUTCOMES]
    return pd.DataFrame(rows)


def category_pairs() -> pd.DataFrame:
    """Every pair of categories compared on engagement rate, the way 'Beauty beats Travel' headlines are made."""
    df = posts()
    groups = {name: rows["engagement_rate"].to_numpy() for name, rows in df.groupby("content_category")}
    rows = []
    for a, b in combinations(sorted(groups), 2):
        p = stats.mannwhitneyu(groups[a], groups[b]).pvalue
        rows.append({"a": a, "b": b, "p_value": p})
    return pd.DataFrame(rows)


@cache
def shuffled_pair_hits(draws: int = 200) -> np.ndarray:
    """'Significant' category pairs when the categories are shuffled at random, so any difference is pure chance.

    Pairs share categories, so one slightly unusual group can produce several hits at once. Shuffling shows how
    many hits that alone gives.
    """
    df = posts()
    rng = np.random.default_rng(SEED)
    rates = df["engagement_rate"].to_numpy()
    hits = []
    for _ in range(draws):
        labels = rng.permutation(df["content_category"].to_numpy())
        groups = {name: rates[labels == name] for name in np.unique(labels)}
        hits.append(sum(stats.mannwhitneyu(groups[a], groups[b]).pvalue < 0.05 for a, b in combinations(sorted(groups), 2)))
    return np.array(hits)


def chance() -> dict:
    tests = all_group_tests()
    pairs = category_pairs()
    shuffled = shuffled_pair_hits()
    return {
        "shuffled_mean": float(shuffled.mean()),
        "shuffled_as_many": float((shuffled >= (pairs["p_value"] < 0.05).sum()).mean()),
        "tests": len(tests), "hits": int((tests["p_value"] < 0.05).sum()), "expected": len(tests) * 0.05,
        "pairs": len(pairs), "pair_hits": int((pairs["p_value"] < 0.05).sum()), "pair_expected": len(pairs) * 0.05,
        "smallest": float(tests["p_value"].min()),
        # Bonferroni: with many tests, each one has to clear 0.05 divided by the number of tests
        "after_correction": int((tests["p_value"] < 0.05 / len(tests)).sum()),
        "pairs_after_correction": int((pairs["p_value"] < 0.05 / len(pairs)).sum()),
    }


# 7. Models ---------------------------------------------------------------------------------------

FIRST_VERSION_FEATURES = ["likes", "comments", "shares", "saves", "reach", "impressions", "caption_length", "hashtags_count"]
BEFORE_POSTING = ["media_type", "content_category", "traffic_source", "weekday", "caption_length", "hashtags_count"]


def _before_posting(df: pd.DataFrame) -> pd.DataFrame:
    return pd.get_dummies(df[BEFORE_POSTING], columns=["media_type", "content_category", "traffic_source", "weekday"], dtype=float)


@cache
def models() -> dict:
    """The first version's model, rebuilt, against honest models that only use what's known before posting."""
    df = posts()

    # The first version: random split, and the rate's own ingredients as inputs
    X_train, X_test, y_train, y_test = train_test_split(
        df[FIRST_VERSION_FEATURES], df["engagement_rate"], test_size=0.2, random_state=SEED
    )
    first = r2_score(y_test, LinearRegression().fit(X_train, y_train).predict(X_test))

    # The same inputs, but predicting the log of the rate, which the formula makes almost exact
    log_fit = LinearRegression().fit(np.log1p(X_train), np.log(y_train))
    circular = r2_score(np.log(y_test), log_fit.predict(np.log1p(X_test)))

    # Honest: only what's known before posting, trained on earlier posts and tested on later ones
    X = _before_posting(df)
    train, test = df["upload_date"] < SPLIT, df["upload_date"] >= SPLIT
    scores = {}
    for target in ["engagement_rate", "followers_gained"]:
        y = np.log(df[target]) if target == "engagement_rate" else df[target]
        linear = LinearRegression().fit(X[train], y[train])
        boosted = HistGradientBoostingRegressor(random_state=SEED, max_iter=200).fit(X[train], y[train])
        scores[target] = {
            "linear": r2_score(y[test], linear.predict(X[test])),
            "boosted": r2_score(y[test], boosted.predict(X[test])),
        }
    return {
        "first": first, "circular": circular, "scores": scores,
        "train_size": int(train.sum()), "test_size": int(test.sum()),
        "r2": pd.Series(
            {
                "First version, rate's own ingredients": round(first, 3),
                "Same inputs, log scale": round(circular, 3),
                "Before posting: engagement, linear": round(scores["engagement_rate"]["linear"], 3),
                "Before posting: engagement, boosted": round(scores["engagement_rate"]["boosted"], 3),
                "Before posting: followers, linear": round(scores["followers_gained"]["linear"], 3),
                "Before posting: followers, boosted": round(scores["followers_gained"]["boosted"], 3),
            }
        ),
    }


def monthly_median() -> pd.Series:
    """Median engagement rate in each full month."""
    df = posts()
    table = df.groupby("month")["engagement_rate"].median()
    counts = df.groupby("month").size()
    return table[counts > counts.max() * 0.8]  # Drops the part-months at either end
