# API Endpoints

## Health
- `GET /health`

## Research
- `POST /api/v1/research` - submit query, run planner/search/scrape/validate/summarize pipeline
- `GET /api/v1/research` - list historical research runs
- `GET /api/v1/research/{run_id}` - retrieve one run with citations and ranked sources

## Sources
- `GET /api/v1/sources?limit=25` - list validated sources from stored research runs

## Memory
- `POST /api/v1/memory`
- `GET /api/v1/memory`
