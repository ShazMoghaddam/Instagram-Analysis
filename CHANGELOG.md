# Changelog

All notable changes to this project are listed here. Versions are dated by month, like `v2026.11`.

## v2026.11 · November 2026

A full rebuild, from a single notebook into a tested, reproducible audit.

### Fixed

- The first version said Reels and videos engage more and that some categories win more followers. Both gaps are the
  size chance produces, and the report now says so with tests
- The linear regression predicted the engagement rate from the columns it's calculated from. It's replaced by honest
  models that only use what's known before posting, trained on earlier posts and tested on later ones
- Averages were thrown by 262 posts with rates over 100%. Comparisons now use medians and rank-based tests
- The analysis didn't check where the data came from. It now sets out five signs that the dataset was generated

### Added

- A findings report with seven findings, written from the data by `findings/build.py`
- Seven charts and three headline tiles, all drawn with [bezel-charts](https://pypi.org/project/bezel-charts/)
- A check on how many "significant" results chance alone produces, with a shuffle test and a correction for many tests
- Tests, an automatic check on every pull request, Dependabot and a security policy
- Social preview image in `assets/social-preview.png`

### Changed

- New folder structure: `data/`, `findings/`, `notebooks/`, `charts/` and `tests/`
- README rewritten around the findings
- Notebook rewritten and moved to `notebooks/instagram_analysis.ipynb`
- Data moved to `data/instagram_analytics.csv`, unchanged

## December 2025

- First version: one notebook and a README
