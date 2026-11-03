"""Checks that the data is sound and the findings hold up. Run from the repository root with `pytest`."""

import re
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "findings"))

import analysis as an  # noqa: E402
import build  # noqa: E402
import charts  # noqa: E402


def test_data_is_complete():
    posts = an.posts()
    assert len(posts) == 29_999
    assert posts["post_id"].is_unique
    assert not posts.isna().any().any()


def test_engagement_rate_is_interactions_over_impressions():
    assert an.formula()["match"] == 1.0
    post = an.posts().iloc[0]
    assert round(post["interactions"] / post["impressions"] * 100, 2) == post["engagement_rate"]


def test_impossible_rates_are_counted():
    odd = an.impossible()
    posts = an.posts()
    assert odd["over_100"] == (posts["interactions"] > posts["impressions"]).sum()
    assert odd["median"] < odd["mean_without"] < odd["mean"]


def test_impressions_are_never_below_reach():
    posts = an.posts()
    assert (posts["impressions"] >= posts["reach"]).all()


def test_rate_bands_cover_every_post():
    assert an.rate_bands().sum() == len(an.posts())


def test_no_format_or_category_stands_out():
    assert an.group_test("media_type", "engagement_rate") > 0.05
    assert an.group_test("content_category", "followers_gained") > 0.05
    medians = an.by_group("media_type", "engagement_rate")
    assert medians.max() - medians.min() < 0.5


def test_counts_are_unrelated():
    _, _, r = an.strongest_link()
    assert abs(r) < 0.05
    assert abs(an.correlations().loc["reach", "likes"]) < 0.05


def test_every_post_shares_one_clock_time():
    assert an.fingerprints()["clock_times"] == 1


def test_nothing_survives_a_correction_for_many_tests():
    luck = an.chance()
    assert luck["after_correction"] == 0
    assert luck["pairs_after_correction"] == 0
    assert luck["shuffled_as_many"] > 0.05  # The pair hits are within what shuffling produces


def test_honest_models_find_nothing_and_the_circular_one_does():
    model = an.models()
    assert model["circular"] > 0.9
    for scores in model["scores"].values():
        assert max(scores.values()) < 0.02
    assert model["train_size"] + model["test_size"] == len(an.posts())


def test_models_train_on_earlier_posts_than_they_test_on():
    posts = an.posts()
    assert (posts["upload_date"] < an.SPLIT).sum() == an.models()["train_size"]


def test_every_chart_draws_in_the_house_style():
    for name, draw in charts.ALL.items():
        svg = draw()._repr_svg_()
        assert "#1B1424" in svg, name
        width = 210 if name.startswith("tile-") else 640
        assert f'width="{width}"' in svg, name


def test_tiles_are_square():
    for name, draw in charts.ALL.items():
        if name.startswith("tile-"):
            assert 'viewBox="0 0 210 210"' in draw()._repr_svg_(), name


def test_report_has_no_unfilled_placeholders():
    text = build.report(build.facts())
    assert not re.search(r"\{[a-z_]+\}", text)
    assert "nan" not in text.lower().split()


def test_readme_links_to_charts_that_exist():
    readme = (ROOT / "README.md").read_text(encoding="utf-8") + (ROOT / "findings" / "README.md").read_text(encoding="utf-8")
    for path in re.findall(r"charts/([a-z-]+\.svg)", readme):
        assert (ROOT / "charts" / path).exists(), path


@pytest.mark.parametrize("group", list(an.GROUPS))
def test_groups_are_balanced(group):
    shares = an.posts()[group].value_counts(normalize=True)
    assert shares.max() - shares.min() < 0.02
