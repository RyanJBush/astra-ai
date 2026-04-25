# Astra AI Demo Script (Portfolio Walkthrough)

## Audience
Hiring managers, technical recruiters, and engineering interview panels.

## Duration
8–12 minutes.

## Narrative arc
1. **Problem framing**: “Astra AI automates multi-source research with traceable evidence.”
2. **Run a live query**: show configurable controls and launch.
3. **Trust and evidence**: review findings, confidence rationale, contradictions, and source metadata.
4. **Operational credibility**: show timeline, metrics, and report export.
5. **Engineering quality**: mention tests, CI, and reproducible local setup.

## Suggested prompt
> Compare major cloud providers on 2026 enterprise AI governance offerings.

## Live steps
1. Open Dashboard and show prior sessions/history.
2. Open Research Query:
   - choose the suggested prompt
   - optionally set recency and allow/deny domains
3. Submit and open Research Results.
4. Highlight:
   - confidence badges + rationale
   - evidence table filtering
   - contradiction severity tags
   - execution timeline with latency markers
5. Open Source Viewer from citations:
   - inspect source author/published/retrieved metadata
6. Export Markdown + JSON reports.

## Talking points (technical depth)
- Pipeline stages: planning → searching → extracting → validating → synthesizing.
- Trust signals:
  - evidence coverage thresholds
  - unsupported-claim tracking
  - contradiction severity
  - provenance metadata (`schema_version`, `pipeline_version`, `generated_at`)
- Governance:
  - PII redaction
  - compliance endpoint
  - audit logs by workspace

## Backup plan if network retrieval is noisy
- Use a previously completed run from Dashboard.
- Continue walkthrough using stored report, timeline, and source viewer.

## Close
“Astra AI is designed as a portfolio-grade autonomous research analyst: runnable locally, transparent in reasoning, and demonstrable end-to-end.”
