# Project Instructions for Agent

## Project Root
/home/James/Documents/HarnessTutorial/

## Key Files
- `InitialDescription.md` — Full project specification and formulas
- `BIKE_SKILLS.md` — Rolling resistance and aerodynamic profiles
- `index.html` — Target single-file application (will be created)
- `.kilo/skill/cycling-physics/SKILL.md` — Physics validation rules with test cases
- `mcp_filesystem.py` — Python MCP server for file operations
- `mcp_fetch.py` — Python MCP server for HTTP fetching

## MCP Servers Available
- **filesystem** (Python) — Read/write project files. Use for all file operations.
- **fetch** (Python) — Fetch external resources (Leaflet CDN, OSRM routing API docs).

## Deployment Target
- The final app is hosted on **GitHub Pages** at `https://<username>.github.io/<repository>/`.
- HTTPS is REQUIRED — `navigator.geolocation` (GPS) only works on secure origins (HTTPS or localhost).
- All resource URLs (Leaflet CSS/JS, tile servers, OSRM API) must use `https://` — no mixed-content warnings.
- The single-file `index.html` is pushed to a GitHub repository and served via Pages.
- The app must function when accessed from a mobile phone's browser via the GitHub Pages URL, using the phone's real GPS.

## Build Rules
1. ALL output must go into a single file: `index.html`.
2. The file must be mobile-responsive (viewport meta, touch-friendly, flexible layout).
3. Use Leaflet.js (loaded from CDN via `unpkg.com` or `cdnjs` with `https://`).
4. Use OSRM demo API (`https://router.project-osrm.org/`) for route queries.
5. All telemetry calculations run client-side in JavaScript.
6. GPS is real device GPS via `navigator.geolocation.watchPosition()` with simulated fallback.
7. Implement gradient-colored polylines and a climb alert panel.
8. Include an inset mini-map showing the full route overview.
9. Do NOT use any build tools, bundlers, or npm dependencies beyond CDN scripts.
10. When deployed to GitHub Pages, the app loads under a subpath (e.g., `/<repo>/`). Leaflet tile URLs and OSRM fetch URLs must NOT be relative to the deployment path — use absolute `https://` URLs.

## Physics Implementation Requirements
- Power must be calculated using the full formula from the cycling physics skill.
- The implementation must pass all 3 test cases in the skill file (±2% tolerance).
- Gradient must be color-mapped onto route segments using a diverging color scale.
- Climb alert must trigger when gradient > 5% and show distance remaining, min balance speed, and min balance power.
- Telemetry display must update at 1 Hz.