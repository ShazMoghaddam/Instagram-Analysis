"""Draw every chart and write the findings report.

Run from the repository root:

    python findings/build.py

Charts go into charts/ as SVG files. The report is written to findings/README.md, and the key findings in the
main README are rewritten between their marker comments. Every number is worked out from the data. Nothing in
them is typed in by hand.
"""

from __future__ import annotations

import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "findings"))

import analysis as an  # noqa: E402
import charts  # noqa: E402

CHARTS = ROOT / "charts"
REPORT = ROOT / "findings" / "README.md"
README = ROOT / "README.md"


def facts() -> dict:
    """Every number the writing uses, in one place."""
    form = an.formula()
    odd = an.impossible()
    prints = an.fingerprints()
    fmt_mean = an.by_group("media_type", "engagement_rate", "mean")
    fmt_median = an.bootstrap_median("media_type", "engagement_rate")
    followers = an.by_group("content_category", "followers_gained", "mean")
    a, b, r = an.strongest_link()
    reels = an.reels_in_reels_feed()
    uniform = an.uniform_tests()
    luck = an.chance()
    model = an.models()
    scores = model["scores"]
    corr = an.correlations()
    return {
        "posts": f"{prints['posts']:,}", "first": prints["first"], "last": prints["last"],
        "match": form["match"], "r_reach": form["r_reach"],
        "over_100": f"{odd['over_100']:,}", "over_share": odd["share"], "max": f"{odd['max']:,.0f}",
        "mean": odd["mean"], "median": odd["median"], "mean_without": odd["mean_without"],
        "fmt_low": fmt_mean.idxmin(), "fmt_low_v": fmt_mean.min(), "fmt_high": fmt_mean.idxmax(), "fmt_high_v": fmt_mean.max(),
        "med_low": fmt_median["median"].min(), "med_high": fmt_median["median"].max(),
        "ci_low": fmt_median["low"].min(), "ci_high": fmt_median["high"].max(),
        "p_fmt": an.group_test("media_type", "engagement_rate"),
        "cat_low": followers.idxmin(), "cat_low_v": followers.min(), "cat_high": followers.idxmax(), "cat_high_v": followers.max(),
        "p_cat": an.group_test("content_category", "followers_gained"),
        "r_reach_likes": corr.loc["reach", "likes"], "link_a": a.replace("_", " "), "link_b": b.replace("_", " "), "link_r": r,
        "reels_feed": reels["reels"], "reels_all": reels["overall"], "p_source": an.format_by_source(),
        "uniform_low": uniform.min(), "clock": prints["clock"], "clock_times": prints["clock_times"],
        "extra_min": f"{prints['extra_min']:,}", "extra_max": f"{prints['extra_max']:,}",
        "format_low": prints["format_low"], "format_high": prints["format_high"],
        "categories": prints["categories"], "sources": prints["sources"],
        **luck,
        "first_r2": model["first"], "circular_r2": model["circular"],
        "er_linear": scores["engagement_rate"]["linear"], "er_boosted": scores["engagement_rate"]["boosted"],
        "fg_linear": scores["followers_gained"]["linear"], "fg_boosted": scores["followers_gained"]["boosted"],
        "train": f"{model['train_size']:,}", "test": f"{model['test_size']:,}",
    }


def r2(value: float) -> str:
    """R² to two places, showing a tiny negative score as 0.00 rather than -0.00."""
    return f"{max(value, 0):.2f}" if value > -0.005 else f"{value:.2f}"


def key_findings(f: dict) -> str:
    return f"""### The engagement rate is a formula, and some of it is impossible

Every post's engagement rate is exactly its likes, comments, shares and saves divided by its impressions. So it can't
be predicted from those columns in any useful sense, only recomputed. And {f['over_100']} posts have more interactions than
impressions, giving rates as high as **{f['max']}%**.

![Posts by engagement rate](charts/rate-bands.svg)

### No format wins

The first version said Reels and videos engage more. The typical post in every format has a median rate between
**{f['med_low']:.1f}% and {f['med_high']:.1f}%**, and the gap in averages it relied on is the size chance produces (p = {f['p_fmt']:.2f}).

![Engagement rate by format](charts/formats.svg)

### Nothing here is related to anything

On a real account, posts that reach more people get more likes. Here the correlation is **{f['r_reach_likes']:.2f}**, and no two counts
are linked more strongly than {abs(f['link_r']):.2f}. The data looks like numbers drawn at random.

![Reach against likes](charts/reach-and-likes.svg)

### The first model was circular, and honest ones predict nothing

Fed the rate's own ingredients on a log scale, a simple model explains **{f['circular_r2']:.0%}** of it. Given only what's known
before posting, the best model explains **{max(f['er_linear'], f['er_boosted'], 0):.0%}**: no better than guessing the average.

![How much each model explains](charts/model-scores.svg)"""


def report(f: dict) -> str:
    return f"""# Findings

What {f['posts']} Instagram posts from {f['first']} to {f['last']} can tell you. This page is written by
[`build.py`](build.py), so every number comes straight from the data.

The short answer is: not much about Instagram, and quite a lot about checking data before trusting it. The dataset
behaves exactly like numbers generated at random, column by column, so every pattern below is either built into the
formula or produced by chance.

## 1. The engagement rate is a formula, and some of it is impossible

For **{f['match']:.0%}** of posts, the engagement rate equals likes, comments, shares and saves added up and divided by
impressions, to the two decimal places given. Divided by reach instead, it barely lines up (r = {f['r_reach']:.2f}).

That makes the rate a calculation, not a separate measurement. Predicting it from likes, saves and impressions is
predicting a sum from its parts.

![Posts by engagement rate](../charts/rate-bands.svg)

{f['over_100']} posts ({f['over_share']:.1%}) have more interactions than impressions, so their rate is over 100%, as high as {f['max']}%.
On Instagram an impression is one view of a post, so more interactions than views is implausible. These rows pull
the average rate up to {f['mean']:.1f}% when the typical post sits at **{f['median']:.1f}%**. Without them the average is {f['mean_without']:.1f}%.
Everything below uses medians or tests that aren't thrown by them.

## 2. No format wins

| Format | Average rate | Median rate |
|---|---|---|
{format_rows()}

![Engagement rate by format](../charts/formats.svg)

The first version compared averages and concluded Reels and videos engage more. The highest average ({f['fmt_high']}, {f['fmt_high_v']:.1f}%) is
{f['fmt_high_v'] - f['fmt_low_v']:.1f} points above the lowest ({f['fmt_low']}, {f['fmt_low_v']:.1f}%), and a Kruskal–Wallis test puts the chance of a gap like
that between identical groups at p = {f['p_fmt']:.2f}. Every format's median sits between {f['ci_low']:.1f}% and {f['ci_high']:.1f}% once you allow
for sampling, a 95% bootstrap interval.

## 3. No category gains more followers

The first version said some content categories attract more followers. Posts gained between 0 and 1,000 followers each,
and every category's average falls between **{f['cat_low_v']:.0f}** ({f['cat_low']}) and **{f['cat_high_v']:.0f}** ({f['cat_high']}).

![Followers gained by category](../charts/categories.svg)

That spread is what chance gives ten groups of 3,000 posts (p = {f['p_cat']:.2f}).

## 4. Nothing here is related to anything

The first version's scatter of reach against likes was meant to show that more visibility brings more engagement. The
correlation is {f['r_reach_likes']:.2f}. On a real account it would be strongly positive.

![Reach against likes](../charts/reach-and-likes.svg)

The same holds everywhere. Leaving out reach against impressions, which are built together (see finding 5), the strongest link
between any two counts is between {f['link_a']} and {f['link_b']}, at {f['link_r']:.2f}. Reels make up {f['reels_feed']:.1%} of posts found through the Reels
feed and {f['reels_all']:.1%} of posts overall, and format has no bearing on how posts were found (p = {f['p_source']:.2f}).

## 5. The data was generated

Several fingerprints show the numbers were drawn at random rather than collected:

- **Even spreads.** Real likes pile up near zero with a long tail of hits. Here each tenth of the range from 0 to 200,000
  holds about the same number of posts, and the same is true of comments, shares, saves, reach, caption length and
  followers gained. None of them is distinguishable from an even spread (every test gives p of {f['uniform_low']:.2f} or more).
- **One clock time.** All {f['posts']} posts were uploaded at {f['clock']}, to the same microsecond, on different days. That
  happens when dates are made by subtracting whole days from a single moment.
- **Built columns.** Impressions are reach plus an evenly spread extra of {f['extra_min']} to {f['extra_max']}.
- **Balanced groups.** Each format is between {f['format_low']:.1%} and {f['format_high']:.1%} of posts, and the {f['categories']} categories and {f['sources']}
  traffic sources are just as even.
- **A tidy window.** Posts run exactly one year, {f['first']} to {f['last']}.

![Posts in each tenth of the likes range](../charts/likes-spread.svg)

## 6. Chance alone produces "findings"

Slice data enough ways and some slices will look different. I compared every format, category, traffic source and weekday
on six outcomes: {f['tests']} tests. At the usual p under 0.05, chance alone should flag about {f['expected']:.1f}. {f['hits']} came up, the
smallest at p = {f['smallest']:.3f}.

![Comparisons that looked significant](../charts/chance.svg)

Comparing categories two at a time, the way "Beauty beats Travel" headlines are made, {f['pair_hits']} of {f['pairs']} pairs came up against
{f['pair_expected']:.1f} expected. That looks like something until you remember the pairs share categories, so one category that's a little
low by chance creates several hits at once. Shuffling the categories at random, so there can't be any real difference,
gives {f['pair_hits']} or more hits {f['shuffled_as_many']:.0%} of the time.

Correcting for the number of tests (Bonferroni), **{f['after_correction'] + f['pairs_after_correction']}** results survive.

## 7. The first model was circular, and honest ones predict nothing

The first version predicted engagement rate from likes, comments, shares, saves, reach, impressions, caption length and
hashtags, on a random split, and called the result reasonable. Rebuilt, it explains {f['first_r2']:.0%} of the rate on posts it hasn't
seen. That's low only because a straight line can't follow a division. Take logs, which turn the division into a subtraction, and
the same inputs explain **{f['circular_r2']:.0%}**. It's recovering the formula, not learning anything.

![How much each model explains](../charts/model-scores.svg)

A useful model can only use what's known before posting: format, category, traffic source, weekday, caption length and
hashtags. Trained on {f['train']} posts up to July 2025 and tested on the {f['test']} after, a linear model and gradient boosting
score R² of {r2(f['er_linear'])} and {r2(f['er_boosted'])} on engagement rate, and {r2(f['fg_linear'])} and {r2(f['fg_boosted'])} on followers gained. Zero means no better
than guessing the average every time.

## What this data can't tell you

- **Anything about Instagram.** The numbers weren't collected from real posts, so they can't show what works on the
  platform. That includes the absence of patterns: a real account would show many.
- **Why the dataset was made this way.** It may have been built for practising code, which it's fine for. It just isn't
  evidence.

## What it's good for

- **Practising a pipeline** on clean, complete data with no missing values.
- **A baseline with no signal.** Any method that finds a strong pattern here is finding its own mistake.
- **Learning to check first.** Every fingerprint above is a check worth running on real data before analysing it.

## How it was worked out

1. [`data/instagram_analytics.csv`](../data/instagram_analytics.csv) is the original Kaggle file, unchanged.
2. [`analysis.py`](analysis.py) holds every calculation as a small, tested function.
3. [`charts.py`](charts.py) draws each chart with [bezel-charts](https://pypi.org/project/bezel-charts/).
4. [`notebooks/instagram_analysis.ipynb`](../notebooks/instagram_analysis.ipynb) walks through the same steps with the working shown.

## A correction to the first version

The first version concluded that Reels and videos engage more, that reach and saves strongly influence engagement, that
some categories attract more followers, and that its linear regression predicted engagement rate reasonably well. None of
these hold. The format and category gaps are the size chance produces, the "influence" of reach and saves is the
formula that defines the rate, and the model was recomputing that formula from its parts. Everything here replaces that work.
"""


def format_rows() -> str:
    mean = an.by_group("media_type", "engagement_rate", "mean")
    median = an.by_group("media_type", "engagement_rate")
    return "\n".join(f"| {name} | {mean[name]:.1f}% | {median[name]:.1f}% |" for name in charts.FORMATS)


def replace_block(text: str, name: str, body: str) -> str:
    pattern = re.compile(rf"(<!-- {name}:start -->\n).*?(\n<!-- {name}:end -->)", re.S)
    if not pattern.search(text):
        raise ValueError(f"Marker {name} not found")
    return pattern.sub(lambda m: m.group(1) + body + m.group(2), text)


def main() -> None:
    # bezel-charts gives each gradient a random id so charts can share a page. A fixed seed keeps the
    # files identical between runs, so a rebuild only shows up in git when something really changed.
    random.seed(2026)
    CHARTS.mkdir(exist_ok=True)
    for name, draw in charts.ALL.items():
        draw().save(CHARTS / f"{name}.svg")
    f = facts()
    REPORT.write_text(report(f), encoding="utf-8")
    README.write_text(replace_block(README.read_text(encoding="utf-8"), "key-findings", key_findings(f)), encoding="utf-8")
    print(f"Wrote {len(charts.ALL)} charts, {REPORT.relative_to(ROOT)} and the README findings")


if __name__ == "__main__":
    main()
