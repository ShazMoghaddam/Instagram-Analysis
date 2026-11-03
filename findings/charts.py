"""Every chart in the project, drawn with bezel-charts (https://pypi.org/project/bezel-charts/).

Each function returns a chart, which shows up in a notebook and saves as an SVG.
"""

from __future__ import annotations

import pandas as pd

import bezel_charts as bc

try:
    from . import analysis as an
except ImportError:
    import analysis as an

# One look for the whole repo: dark, frameless, on an aubergine background
LOOK = {"theme": "dark", "frame": "none", "corners": 16, "background": "#1B1424"}
WIDE = {**LOOK, "width": 640}
TILE = {**LOOK, "width": 210, "height": 170}  # 170 of plot gives a 210px square tile

# Paul Tol's vibrant palette, which stays distinct with every common kind of colour blindness
MAGENTA, BLUE, ORANGE, CYAN = "#EE3377", "#0077BB", "#EE7733", "#33BBEE"
QUIET = "#6B5F80"  # Context bars, 3:1 against the background

FORMATS = ["Photo", "Carousel", "Reel", "Video"]


def rate_bands():
    bands = an.rate_bands()
    return bc.bars(
        bands,
        heading="Posts by engagement rate. A rate over 100% means more interactions than views",
        stat="none", show_values=True, height=220, color=[QUIET] * (len(bands) - 1) + [MAGENTA], highlight="none", **WIDE,
    )


def formats():
    mean = an.by_group("media_type", "engagement_rate", "mean").loc[FORMATS]
    median = an.by_group("media_type", "engagement_rate").loc[FORMATS]
    return bc.bars(
        pd.DataFrame({"Average, as the first version used": mean.round(1), "Median, the typical post": median.round(1)}),
        heading="Engagement rate by format",
        stat="none", show_values=True, suffix="%", decimals=1, height=230, color=[BLUE, MAGENTA], **WIDE,
    )


def categories():
    followers = an.by_group("content_category", "followers_gained", "mean").round(0)
    return bc.bars(
        followers,
        heading="Average followers gained per post, by category. Posts gained 0 to 1,000",
        horizontal=True, stat="none", show_values=True, decimals=0, color=MAGENTA, highlight="none",
        goal=1000, goal_label="Most any post gained", **WIDE,
    )


def reach_and_likes():
    sample = an.posts().sample(800, random_state=an.SEED)
    return bc.scatter(
        pd.DataFrame({"Reach (thousands)": sample["reach"] / 1000, "Likes (thousands)": sample["likes"] / 1000}),
        x="Reach (thousands)", y="Likes (thousands)",
        heading="Reach against likes, 800 posts at random. Real posts would rise to the right",
        trend=True, color=MAGENTA, height=300, decimals=0, **WIDE,
    )


def likes_spread():
    tenths = an.likes_by_tenth()
    return bc.bars(
        tenths,
        heading="Posts in each tenth of the likes range. Real likes bunch up near zero",
        stat="none", show_values=True, height=220, color=MAGENTA, highlight="none", **WIDE,
    )


def chance():
    c = an.chance()
    return bc.bars(
        pd.DataFrame(
            {
                "Found": [c["hits"], c["pair_hits"], c["after_correction"] + c["pairs_after_correction"]],
                "Expected by chance alone": [round(c["expected"], 1), round(c["pair_expected"], 1), 0.1],  # At most 0.05 per corrected family, two families
            },
            index=[f"{c['tests']} group comparisons", f"{c['pairs']} category pairs", "After correcting for many tests"],
        ),
        heading="Comparisons that looked significant (p under 0.05)",
        stat="none", show_values=True, decimals=1, height=220, color=[MAGENTA, BLUE], **WIDE,
    )


def model_scores():
    r2 = an.models()["r2"].clip(lower=0)
    return bc.bars(
        r2,
        heading="How much each model explains on unseen posts (R²)",
        horizontal=True, stat="none", show_values=True, decimals=2, goal=1, goal_label="Perfect",
        color=[BLUE, BLUE, MAGENTA, MAGENTA, MAGENTA, MAGENTA], highlight="none", **WIDE,
    )


# Headline tiles ------------------------------------------------------------------------------------

def tile_formula():
    return bc.gauge(
        round(an.formula()["match"] * 100, 1), label="rates are a formula", heading="Engagement rate", suffix="%",
        color=MAGENTA, **TILE,
    )


def tile_reach():
    sample = an.posts().sample(300, random_state=an.SEED)
    return bc.scatter(
        x=(sample["reach"] / 1000).tolist(), y=(sample["likes"] / 1000).tolist(),
        heading="Reach vs likes", trend=True, color=MAGENTA, decimals=0, **TILE,
    )


def tile_predictable():
    scores = an.models()["scores"]["engagement_rate"]
    best = max(max(scores.values()), 0)
    return bc.gauge(
        round(best * 100, 1), label="explained before posting", heading="Best honest model", suffix="%",
        color=ORANGE, **TILE,
    )


ALL = {
    "rate-bands": rate_bands,
    "formats": formats,
    "categories": categories,
    "reach-and-likes": reach_and_likes,
    "likes-spread": likes_spread,
    "chance": chance,
    "model-scores": model_scores,
    "tile-formula": tile_formula,
    "tile-reach": tile_reach,
    "tile-predictable": tile_predictable,
}
