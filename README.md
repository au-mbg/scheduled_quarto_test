# Scheduled Quarto documents demo

This repository demonstrates date-based publication of pages in a Quarto
website using [`qmd-lab/scheduled-docs`](https://github.com/qmd-lab/scheduled-docs).
The extension decides which pages are drafts each time Quarto renders the site;
an hourly GitHub Actions workflow supplies the repeated renders and deploys the
result to GitHub Pages.

## Local setup

[Install Pixi](https://pixi.sh/latest/installation/) and run:

```bash
pixi run render
```

The rendered site is written to `_site/`. Serve that directory to inspect the
same draft behavior used for deployment:

```bash
pixi run serve
```

For authoring, use `pixi run preview`. Quarto intentionally makes drafts visible
during previews, so preview mode does **not** demonstrate what visitors see on
the published site.

## Release calendar

[`_schedule.yml`](_schedule.yml) is the public release calendar. Each entry has
an `href` and an ISO `YYYY-MM-DD` date. The demo uses UTC and evaluates dates at
midnight:

```yaml
scheduled-docs:
  draft-after: "system-time"
  timezone: "+00:00"
  docs:
    - href: pages/example.qmd
      date: "2026-09-15"
```

Normally `draft-after` should remain `"system-time"`. A document dated after
the comparison date is treated as a draft. An explicit `draft: false` publishes
a future document, while `draft: true` withholds a past document.

### Reproduce another point in time

To simulate the site on a particular date:

1. Temporarily replace `draft-after: "system-time"` with an ISO date such as
   `draft-after: "2026-09-14"`.
2. Run `pixi run render`, followed by `pixi run serve` if desired.
3. Restore `draft-after: "system-time"` before committing.

## Automated publication

The single workflow in [`.github/workflows/publish.yml`](.github/workflows/publish.yml)
runs on pushes to `main`, manual dispatches, and hourly at minute 17 UTC. It
renders the current default branch and deploys `_site/` with GitHub Pages.

GitHub scheduled workflows are not exact timers: a run can be delayed during
high load, and public repositories with no activity for 60 days can have their
schedules disabled. The hourly cadence therefore means a newly eligible page
normally appears within roughly an hour, rather than exactly at midnight.

To enable deployment, configure the repository under **Settings → Pages** to
use **GitHub Actions** as its source. A manual workflow run is useful for the
first deployment and for checking the complete pipeline.

## Demo cases

| Page | Schedule behavior |
|---|---|
| Already released | Past date; published normally |
| Scheduled release | Released automatically on 2026-09-15 UTC |
| Manually published | Far-future date overridden with `draft: false` |
| Manually withheld | Past date overridden with `draft: true` |

The extension is vendored at version 0.6.0 so local and CI renders use the same
implementation.
