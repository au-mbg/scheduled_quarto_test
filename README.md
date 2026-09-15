# Scheduled Quarto documents demo

This repository demonstrates date-based publication of student and instructor
versions of a Quarto website. It combines
[`qmd-lab/scheduled-docs`](https://github.com/qmd-lab/scheduled-docs) with the
[`quarto-teaching-tools`](https://github.com/au-mbg/quarto-teaching-tools)
solution filters. An hourly GitHub Actions workflow renders both profiles and
deploys the combined result to GitHub Pages.

## Local setup

[Install Pixi](https://pixi.sh/latest/installation/) and run:

```bash
pixi run render student
pixi run render instructor
pixi run render-all
```

The student site is written to `_site/`; the instructor site is written to
`_site/instructor/`. `render-all` builds them sequentially in that order. Serve
the combined output to inspect the same draft behavior used for deployment:

```bash
pixi run serve
```

For authoring, use `pixi run preview student` or `pixi run preview instructor`.
Quarto intentionally makes drafts visible during previews, so preview mode does
**not** demonstrate what visitors see on the published site.

The supported instructor commands go through Pixi because a repository-owned
Python script temporarily selects the instructor calendar. A plain
`quarto render` remains safe and defaults to the student profile and student
calendar.

## Student and instructor content

The profile files set `teaching.show-solutions` explicitly. Shared source can
then contain instructor-only solution callouts:

```markdown
::: {.callout-solution}
Worked answer shown only in the instructor site.
:::
```

It can also contain paired alternatives:

```markdown
::: {teaching="exercise"}
Student scaffolding.
:::

::: {teaching="solution"}
Completed instructor material.
:::
```

The profile switch in the navigation links the public student root to the
public `/instructor/` subsite. This separation is a publishing convenience, not
authentication or access control. Do not put confidential answer material in
this public demonstration.

## Release calendar

[`_schedule.yml`](_schedule.yml) is the student release calendar and
[`_schedule-instructor.yml`](_schedule-instructor.yml) is the instructor
calendar. Each entry has an `href` and an ISO `YYYY-MM-DD` date. The demo uses
UTC and evaluates dates at midnight:

```yaml
scheduled-docs:
  draft-after: "system-time"
  timezone: "+00:00"
  docs:
    - href: pages/example.qmd
      date: "2026-09-15"
```

Normally `draft-after` should remain `"system-time"` in both calendars. A
document dated after the applicable comparison date is treated as a draft. An
explicit `draft: false` publishes a future document, while `draft: true`
withholds a past document.

The upstream extensions are vendored without modifications. The selector in
`scripts/render_profile.py` temporarily substitutes the instructor calendar as
`_schedule.yml`, runs Quarto, and restores the exact student file even when the
render fails. It also serializes renders and recovers a student-calendar backup
left by an interrupted process.

### Reproduce another point in time

To simulate the site on a particular date:

1. Temporarily replace `draft-after: "system-time"` in the calendar being tested
   with an ISO date such as `draft-after: "2026-09-14"`.
2. Run `pixi run render student` or `pixi run render instructor`, followed by
   `pixi run serve` if desired.
3. Restore `draft-after: "system-time"` before committing.

## Automated publication

The single workflow in [`.github/workflows/publish.yml`](.github/workflows/publish.yml)
runs on pushes to `main`, manual dispatches, and hourly at minute 17 UTC. It
renders both profiles from the current default branch and deploys the combined
`_site/` directory with GitHub Pages.

GitHub scheduled workflows are not exact timers: a run can be delayed during
high load, and public repositories with no activity for 60 days can have their
schedules disabled. The hourly cadence therefore means a newly eligible page
normally appears within roughly an hour, rather than exactly at midnight.

To enable deployment, configure the repository under **Settings → Pages** to
use **GitHub Actions** as its source. A manual workflow run is useful for the
first deployment and for checking the complete pipeline.

## Demo cases

| Page | Student behavior | Instructor behavior |
|---|---|---|
| Already released | Past date; published | Past date; published with teaching-tool examples |
| Scheduled release | Released 2026-09-15 UTC | Released 2026-09-16 UTC |
| Manually published | Far-future date with `draft: false` | Far-future date with `draft: false` |
| Manually withheld | Past date with `draft: true` | Past date with `draft: true` |

`scheduled-docs` 0.6.0, `callout-solution` 1.0.0, and `strip-solution` 1.1.0
are vendored so local and CI renders use the same implementations.
