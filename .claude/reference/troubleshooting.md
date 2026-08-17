# Troubleshooting Guide

Common issues when working with the Galaxy Stats ETL pipeline.

---

## Issue: Report renders with no CSS/styling

**Symptoms:** HTML page loads but looks unstyled, plain text

**Cause:** Template has double braces `{{` instead of single `{` in CSS/JS sections

**Fix:** Check `render_report.py` template uses single braces for CSS/JS

**Verification:** View page source and check `<style>` section has valid CSS

---

## Issue: "File not found" error when parsing

**Symptoms:** Error message about HTML file not found

**Cause:** Incorrect HTML path - Makefile runs commands from `etl/` directory

**Fix:** Use `HTML_FILE=context/2026-03.html` NOT `HTML_FILE=etl/context/2026-03.html`

---

## Issue: Placeholders like `{EVENT_NAME}` not replaced in output

**Symptoms:** Template variables appear as literal `{EVENT_NAME}` in rendered HTML

**Cause:** The `.replace()` line in `render_report.py` has wrong brace escaping

**Fix:** Should be `f"{{{key}}}"` (triple braces) NOT `f"{{key}}"` (double)

---

## Issue: Cluster names don't make sense

**Symptoms:** Auto-generated archetype names are nonsensical or irrelevant

**Cause:** Auto-generated labels are based on most frequent card in each cluster

**Fix:** Manually edit cluster labels in `etl/dist/events/<event-id>/analysis.json` and re-render

---

## Issue: Wrong event data showing in report

**Symptoms:** Report shows data from a different event or previous run

**Cause:** Stale `analysis.json` from previous run

**Fix:** Delete `etl/dist/events/<event-id>/analysis.json` and re-run `make etl-analyze`

---

## Issue: Archetype overrides not being applied to player decks

**Symptoms:** Player decks show auto-generated cluster names instead of archetype names from config

**Cause:** Using `make report-auto` or skipping the finalize step

**Fix:** Use `make etl-finalize-with-overrides EVENT_ID=<event-id>` to apply config
