# Live Crawl Abandoned — Phase A Plan B

- **Target**: https://www.courtauction.go.kr (대한민국 법원경매정보)
- **Probed**: 2026-04-22
- **Decision**: synthetic fixtures in place of live crawl.

## Probe findings

- `GET /robots.txt` → HTTP 404, 29030-byte HTML error page ("시스템안내"). No
  robots.txt is served, so no explicit Disallow applies. The error wrapper is a
  separate signal that non-app paths are rewritten to an error page.
- `GET /` → HTTP 200, 847 bytes. Body contains only `window.location.href = "/pgj/index.on"`.
- `GET /pgj/index.on` → HTTP 200, 2642 bytes. A WebSquare shell: empty `<body>`,
  all UI is rendered by the WebSquare bootloader (`/pgj/websquare/javascript.wq?q=/bootloader`)
  which pulls `PGJ111M01.xml` and injects content. Search results and detail pages
  do not exist as static HTML.

## Why live crawl is out of Phase A scope

1. **WebSquare SPA** — page transitions don't change the URL. Search/pagination/
   detail navigation go through an XPlatform-style XHR submodel returning XML
   re-rendered in place.
2. **Playwright needed, but insufficient on its own** — automating the WebSquare
   widget tree (selector stability, click-through to detail, modal guards) is a
   multi-day reverse-engineering task, not a Phase A deliverable.
3. **Session / anti-bot** — the first request already sets `WMONID`, `JSESSIONID`,
   and `cortAuctnLgnMbr`; repeated automated sessions are likely to trip
   IP-level throttling or redirect into the 시스템안내 page we already observed.
4. **No wrapper fallback** — the spec forbids swapping to a mirror site.

## Plan B — synthetic fixtures

- `scripts/seed_fixtures.py` hand-authors **6 detail** + **2 list** HTML fixtures
  with matching expected JSON oracles. Coverage:
  - `use_type` ∈ {아파트, 다세대, 토지, 근린생활시설}
  - `failed_count` ∈ {0, 1, 2, 3}
  - one `area_m2 = null` case
- HTML uses realistic selectors (`.case-title`, `.auction-date`, `.appraisal-price`,
  `a.detail-link`, …) so Phase B's BS4 parser is exercised the way it would be
  against a real rendered DOM.
- `fixtures/MANIFEST.json` records `mode = "synthetic"` and references this file.

## Path forward

The correct production data source for this project is the **공공데이터포털 법원경매정보 Open API**
(data.go.kr). It's a JSON/XML REST API with a documented schema, no JS rendering,
and explicit terms of use. Swap `crawler/live.py` for an HTTPX-based API client
in a follow-up phase. At that point the synthetic fixtures stay as parser
regression tests, and new live fixtures can be added alongside.
