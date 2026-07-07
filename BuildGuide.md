# Build Guide: Cyclist Navigation & Power Telemetry Dashboard

## Overview

This guide instructs an agentic harness (KiloCode extension in VS Code) to build a feature-complete, single-file HTML5 mobile-responsive **Cyclist Navigation & Power Telemetry Dashboard** from end to end. The guide is split into two phases:

1. **Infrastructure Phase** — Configure the Kilo harness with custom skills, MCP servers, agents, commands, and project scaffolding.
2. **Implementation Phase** — Use the configured infrastructure to implement, test, validate locally, and deploy to GitHub Pages for mobile GPS testing via HTTPS.

Each step is self-contained and actionable. The harness should proceed linearly through the numbered steps.

---

## Phase 1: Infrastructure Setup

### Step 1.1 — Create Project Directory and Kilo Configuration

Create the project directory and a `kilo.json` configuration file that registers MCP servers, custom skill paths, agent definitions, and permissions.

**Actions:**

1. Create directory `/home/James/Documents/HarnessTutorial/` (if not already present).
2. Write `/home/James/Documents/HarnessTutorial/kilo.json`:

```jsonc
{
  "$schema": "https://app.kilo.ai/config.json",
  "model": "anthropic/claude-sonnet-4-20250514",
  "small_model": "anthropic/claude-sonnet-4-20250514",
  "default_agent": "cyclist-builder",

  "mcp": {
    "filesystem": {
      "type": "local",
      "command": ["python3", "mcp_filesystem.py"],
      "enabled": true
    },
    "fetch": {
      "type": "local",
      "command": ["python3", "mcp_fetch.py"],
      "enabled": true
    }
  },

  "skills": {
    "paths": [".kilo/skill"]
  },

  "instructions": ["AGENTS.md", "BIKE_SKILLS.md"],

  "permission": {
    "bash": "allow",
    "edit": {
      "HarnessTutorial/**": "allow",
      "*": "ask"
    },
    "read": "allow",
    "webfetch": "allow",
    "filesystem_*": "allow",
    "fetch_*": "allow"
  }
}
```

3. Create `.kilo/` directory structure:

```
.kilo/
├── kilo.json
├── agent/
│   └── cyclist-builder.md
├── command/
│   ├── validate-physics.md
│   ├── test-telemetry.md
│   └── preview-app.md
└── skill/
    └── cycling-physics/
        └── SKILL.md
```

4. Write `.kilo/kilo.json` (project-scoped overrides if needed — can be empty or inherit from root).

---

### Step 1.2 — Create Python-Based MCP Server Scripts

Since `npx`/Node.js may not be available, create two Python-based MCP server scripts that implement the Model Context Protocol over stdin/stdout JSON-RPC. These provide the same `read_file`, `write_file`, `fetch` etc. tools that the standard MCP servers would.

**MCP Filesystem Server** — `mcp_filesystem.py`:

```python
#!/usr/bin/env python3
"""MCP Filesystem Server over stdin/stdout JSON-RPC."""

import json, os, sys, shutil, fnmatch

ALLOWED_ROOT = os.path.abspath(os.path.dirname(__file__))

def safe_path(target):
    abs_target = os.path.abspath(os.path.join(os.getcwd(), target))
    return abs_target if abs_target.startswith(ALLOWED_ROOT) else None

def read_file(path):
    path = safe_path(path)
    if not path or not os.path.isfile(path):
        return {"error": "File not found or access denied"}
    with open(path, 'r') as f:
        return {"content": f.read()}

def write_file(path, content):
    path = safe_path(path)
    if not path:
        return {"error": "Access denied"}
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)
    return {"success": True}

def list_directory(path):
    path = safe_path(path) if path else ALLOWED_ROOT
    if not path or not os.path.isdir(path):
        return {"error": "Directory not found"}
    entries = []
    for entry in os.listdir(path):
        full = os.path.join(path, entry)
        entries.append({"name": entry, "type": "directory" if os.path.isdir(full) else "file"})
    return {"entries": entries}

def search_files(pattern):
    matches = []
    for root, dirs, files in os.walk(ALLOWED_ROOT):
        for f in files:
            if fnmatch.fnmatch(f, pattern):
                matches.append(os.path.relpath(os.path.join(root, f), ALLOWED_ROOT))
    return {"files": matches}

def get_file_info(path):
    path = safe_path(path)
    if not path or not os.path.exists(path):
        return {"error": "Access denied or not found"}
    stat = os.stat(path)
    return {"size": stat.st_size, "modified": stat.st_mtime, "is_directory": os.path.isdir(path)}

def move_file(source, destination):
    src, dst = safe_path(source), safe_path(destination)
    if not src or not dst:
        return {"error": "Access denied"}
    shutil.move(src, dst)
    return {"success": True}

def copy_file(source, destination):
    src, dst = safe_path(source), safe_path(destination)
    if not src or not dst:
        return {"error": "Access denied"}
    shutil.copy2(src, dst)
    return {"success": True}

TOOLS = {
    "read_file":       {"handler": read_file,       "schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
    "write_file":      {"handler": write_file,      "schema": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}},
    "list_directory":  {"handler": list_directory,  "schema": {"type": "object", "properties": {"path": {"type": "string"}}}},
    "search_files":    {"handler": search_files,    "schema": {"type": "object", "properties": {"pattern": {"type": "string"}}, "required": ["pattern"]}},
    "get_file_info":   {"handler": get_file_info,   "schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
    "move_file":       {"handler": move_file,       "schema": {"type": "object", "properties": {"source": {"type": "string"}, "destination": {"type": "string"}}, "required": ["source", "destination"]}},
    "copy_file":       {"handler": copy_file,       "schema": {"type": "object", "properties": {"source": {"type": "string"}, "destination": {"type": "string"}}, "required": ["source", "destination"]}},
}

def handle_request(msg):
    mid, method = msg.get("id"), msg.get("method")
    if method == "initialize":
        caps = {k: {"description": k.replace("_"," ").title(), "inputSchema": v["schema"]} for k,v in TOOLS.items()}
        return {"id": mid, "jsonrpc": "2.0", "protocolVersion": "2024-11-05", "capabilities": {"tools": caps}, "serverInfo": {"name": "python-filesystem", "version": "1.0.0"}}
    if method == "notifications/initialized":
        return None
    if method == "tools/call":
        tool, args = msg["params"]["name"], msg["params"]["arguments"]
        if tool in TOOLS:
            result = TOOLS[tool]["handler"](**args)
            return {"id": mid, "jsonrpc": "2.0", "content": [{"type": "text", "text": json.dumps(result)}]}
        return {"id": mid, "jsonrpc": "2.0", "error": {"code": -32601, "message": f"Tool not found: {tool}"}}
    return {"id": mid, "jsonrpc": "2.0", "error": {"code": -32601, "message": f"Method not found: {method}"}}

if __name__ == "__main__":
    for line in sys.stdin:
        line = line.strip()
        if not line: continue
        try:
            resp = handle_request(json.loads(line))
            if resp:
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()
        except json.JSONDecodeError:
            pass
```

**MCP Fetch Server** — `mcp_fetch.py`:

```python
#!/usr/bin/env python3
"""MCP Fetch Server over stdin/stdout JSON-RPC."""

import json, sys, urllib.request, urllib.error, ssl

def fetch_url(url):
    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(url, headers={"User-Agent": "MCP-Fetch/1.0"})
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            return {"content": resp.read().decode("utf-8", errors="replace"), "status": resp.status}
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}"}
    except Exception as e:
        return {"error": str(e)}

TOOLS = {
    "fetch": {"handler": fetch_url, "schema": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}
}

def handle_request(msg):
    mid, method = msg.get("id"), msg.get("method")
    if method == "initialize":
        caps = {k: {"description": k.replace("_"," ").title(), "inputSchema": v["schema"]} for k,v in TOOLS.items()}
        return {"id": mid, "jsonrpc": "2.0", "protocolVersion": "2024-11-05", "capabilities": {"tools": caps}, "serverInfo": {"name": "python-fetch", "version": "1.0.0"}}
    if method == "notifications/initialized":
        return None
    if method == "tools/call":
        tool, args = msg["params"]["name"], msg["params"]["arguments"]
        if tool in TOOLS:
            result = TOOLS[tool]["handler"](**args)
            return {"id": mid, "jsonrpc": "2.0", "content": [{"type": "text", "text": json.dumps(result)}]}
        return {"id": mid, "jsonrpc": "2.0", "error": {"code": -32601, "message": f"Tool not found: {tool}"}}
    return {"id": mid, "jsonrpc": "2.0", "error": {"code": -32601, "message": f"Method not found: {method}"}}

if __name__ == "__main__":
    for line in sys.stdin:
        line = line.strip()
        if not line: continue
        try:
            resp = handle_request(json.loads(line))
            if resp:
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()
        except json.JSONDecodeError:
            pass
```

Make both scripts executable with `chmod +x mcp_filesystem.py mcp_fetch.py`.

---

### Step 1.3 — Define the Custom Agent

Write `.kilo/agent/cyclist-builder.md`:

```yaml
---
description: Builds the Cyclist Navigation & Power Telemetry Dashboard
mode: primary
model: anthropic/claude-sonnet-4-20250514
steps: 50
color: "#4ade80"
permission:
  bash: allow
  edit:
    "HarnessTutorial/**": allow
    "*": ask
  read: allow
  webfetch: allow
  filesystem_*: allow
  fetch_*: allow
---
You are a specialized build agent for the Cyclist Navigation & Power Telemetry Dashboard.

Your goal is to build a single-file HTML5 mobile-responsive application with:
- Real-time GPS tracking and route plotting via OpenStreetMap / Leaflet
- Dynamic rerouting on deviation
- Live telemetry: speed, distance, elevation gain, mechanical power output (W)
- Gradient-aware route coloring, climb warnings, balance speed thresholds

Target deployment: GitHub Pages (HTTPS). The app MUST work from a GitHub Pages URL on a mobile phone's browser using real device GPS (`navigator.geolocation`). All resource URLs must use `https://` — no mixed content.

You ALWAYS start by reading:
1. `.kilo/skill/cycling-physics/SKILL.md` — the physics validation rules
2. `BIKE_SKILLS.md` — the rolling resistance and aerodynamic profiles
3. `InitialDescription.md` — the full project description and formulas
4. Any existing `.kilo/command/*.md` files for utility commands

Before writing any code, produce a detailed implementation plan. Then build, test, deploy to GitHub Pages, and verify mobile GPS functionality.
```

---

### Step 1.4 — Define the Cycling Physics Skill

Write `.kilo/skill/cycling-physics/SKILL.md`:

```yaml
---
name: cycling-physics
description: Validates cycling physics formulas for power, drag, rolling resistance, gradient, and balance speed calculations
---
# Cycling Physics Validation Rules

## Constants and Assumptions
- Gravity (g): 9.81 m/s²
- Air density (ρ): 1.2 kg/m³
- Drivetrain efficiency (η): 0.95
- Standard CdA (aerodynamic drag coefficient × frontal area): 0.38 m² (touring hoods position)
- Standard Crr (rolling resistance coefficient): 0.005 (pavement)
- Minimum balance speed threshold: 6.0 km/h (1.667 m/s)

## Power Equation

P_total = (P_gravity + P_drag + P_rolling) / η

Where:
- P_gravity = m × g × sin(arctan(G)) × v
- P_drag = 0.5 × CdA × ρ × v³
- P_rolling = m × g × cos(arctan(G)) × Crr × v

Variables:
- m = total mass (rider + bike) in kg
- G = gradient as decimal (0.05 = 5%)
- v = velocity in m/s

## Derived Calculations

### Power at Balance Speed
P_balance = (P_gravity + P_drag + P_rolling) / η
  where v = 1.667 m/s (minimum balance speed)

### Gradient Conversion
grade_percent = G × 100
G = grade_percent / 100

### Speed Conversion
kmh = m_s × 3.6
m_s = kmh / 3.6

### Distance Calculation (Haversine)
For consecutive GPS points (lat1, lon1) and (lat2, lon2):
  a = sin²(Δlat/2) + cos(lat1)×cos(lat2)×sin²(Δlon/2)
  c = 2 × atan2(√a, √(1-a))
  distance = R × c  where R = 6371000 m (Earth radius)

### Elevation Gain
Only accumulate positive altitude differences between consecutive samples.

## Validation Test Cases

Test Case 1: Flat road, steady speed
- Rider: 75 kg, Bike: 10 kg, total m = 85 kg
- Speed: 8.33 m/s (30 km/h)
- Gradient: 0%
- Expected P_gravity: 0 W
- Expected P_drag: 0.5 × 0.38 × 1.2 × (8.33)³ ≈ 131.6 W
- Expected P_rolling: 85 × 9.81 × 1 × 0.005 × 8.33 ≈ 34.7 W
- Expected P_total: (0 + 131.6 + 34.7) / 0.95 ≈ 175.1 W

Test Case 2: Steep climb, slow speed
- Rider: 75 kg, Bike: 10 kg, total m = 85 kg
- Speed: 2.78 m/s (10 km/h)
- Gradient: 8% (G = 0.08)
- sin(arctan(0.08)) ≈ 0.0797
- cos(arctan(0.08)) ≈ 0.9968
- Expected P_gravity: 85 × 9.81 × 0.0797 × 2.78 ≈ 184.7 W
- Expected P_drag: 0.5 × 0.38 × 1.2 × (2.78)³ ≈ 4.9 W
- Expected P_rolling: 85 × 9.81 × 0.9968 × 0.005 × 2.78 ≈ 11.6 W
- Expected P_total: (184.7 + 4.9 + 11.6) / 0.95 ≈ 211.8 W

Test Case 3: Balance speed on 10% gradient
- Total m = 85 kg, balance v = 1.667 m/s, G = 0.10
- sin(arctan(0.10)) ≈ 0.0995
- cos(arctan(0.10)) ≈ 0.9950
- Expected P_gravity: 85 × 9.81 × 0.0995 × 1.667 ≈ 138.2 W
- Expected P_drag: 0.5 × 0.38 × 1.2 × (1.667)³ ≈ 1.1 W
- Expected P_rolling: 85 × 9.81 × 0.9950 × 0.005 × 1.667 ≈ 6.9 W
- Expected P_total: (138.2 + 1.1 + 6.9) / 0.95 ≈ 153.9 W
```

---

### Step 1.5 — Define Utility Commands

**Command: validate-physics** — `.kilo/command/validate-physics.md`:

```yaml
---
description: Validate power/telemetry physics against defined test cases
agent: cyclist-builder
---
Read .kilo/skill/cycling-physics/SKILL.md to get the test case expected values. Then open index.html and find the JavaScript power calculation function. Verify that the implementation produces outputs within ±2% of expected values for all test cases. Report any discrepancies as failures.
```

**Command: test-telemetry** — `.kilo/command/test-telemetry.md`:

```yaml
---
description: Run telemetry unit tests using Python test harness
agent: cyclist-builder
---
Create a test harness in JavaScript (or Python reimplementation) that exercises:
1. Power calculation (all 3 test cases from the physics skill)
2. Speed conversion (m/s ↔ km/h)
3. Gradient conversion (percent ↔ decimal)
4. Haversine distance calculation (known test points)
5. Elevation gain accumulation (known altitude array)

Run the harness using Python (via `python3 -c "..."`) extracting and evaluating the math, or open index.html in a headless browser. Output PASS/FAIL for each test.
```

**Command: preview-app** — `.kilo/command/preview-app.md`:

```yaml
---
description: Start a local HTTP preview server for the dashboard
---
Start a local HTTP server on port 8080 serving the project directory using `python3 -m http.server 8080`. Confirm the server is reachable at http://localhost:8080.
```

---

### Step 1.6 — Write BIKE_SKILLS.md (Localized Profile Context)

Write `BIKE_SKILLS.md` in the project root:

```markdown
# Cyclist Physics Validation Rule Set

## Rolling Resistance Profiles
- Asphalt Smooth: 0.004
- Pavement Standard: 0.005
- Gravel Course: 0.008

## Aerodynamic Profiles
- Racing Drops Hood: CdA = 0.32
- Standard Touring Hood: CdA = 0.38
- Urban Commuter Upright: CdA = 0.42

## Drivetrain Efficiency
- Clean Chain: 0.95
- Worn / Dirty Chain: 0.90

## Default Configuration
- Rolling Resistance: 0.005 (Pavement Standard)
- CdA: 0.38 (Standard Touring Hood)
- Drivetrain Efficiency: 0.95

## Minimum Balance Speed
- 6.0 km/h (1.667 m/s) on any gradient above 5%
```

---

### Step 1.7 — Write AGENTS.md (Project-Level Instructions)

Write `AGENTS.md` in the project root:

```markdown
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
```

---

### Step 1.8 — Create MCP Telemetry Bridge Stub (Python)

Create `ant_plus_or_ble_mcp_bridge.py` as a Python-based stub MCP server for future live hardware integration.

```python
#!/usr/bin/env python3
"""Stub MCP Server: Cycling Telemetry Bridge — exposes get_live_sensor_readings."""

import json, sys, time

TOOLS = {
    "get_live_sensor_readings": {
        "description": "Returns current sensor readings from cycling hardware",
        "inputSchema": {"type": "object", "properties": {}}
    }
}

def handle_request(msg):
    mid, method = msg.get("id"), msg.get("method")
    if method == "initialize":
        caps = {k: {"description": v["description"], "inputSchema": v["inputSchema"]} for k,v in TOOLS.items()}
        return {"id": mid, "jsonrpc": "2.0", "protocolVersion": "2024-11-05", "capabilities": {"tools": caps}, "serverInfo": {"name": "cycling-telemetry-bridge", "version": "1.0.0"}}
    if method == "notifications/initialized":
        return None
    if method == "tools/call" and msg["params"]["name"] == "get_live_sensor_readings":
        data = {"power": 250, "speed": 8.33, "cadence": 90, "heartRate": 145, "timestamp": time.time() * 1000}
        return {"id": mid, "jsonrpc": "2.0", "content": [{"type": "text", "text": json.dumps(data)}]}
    return {"id": mid, "jsonrpc": "2.0", "error": {"code": -32601, "message": f"Method not found: {method}"}}

if __name__ == "__main__":
    for line in sys.stdin:
        line = line.strip()
        if not line: continue
        try:
            resp = handle_request(json.loads(line))
            if resp:
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()
        except json.JSONDecodeError:
            pass
```

Make executable with `chmod +x ant_plus_or_ble_mcp_bridge.py`.

---

### Step 1.9 — Verify Infrastructure Readiness

Run the following checks to confirm the infrastructure is in place before proceeding to implementation:

1. Confirm all files exist:
   - `kilo.json`
   - `mcp_filesystem.py` and `mcp_fetch.py`
   - `.kilo/agent/cyclist-builder.md`
   - `.kilo/command/validate-physics.md`
   - `.kilo/command/test-telemetry.md`
   - `.kilo/command/preview-app.md`
   - `.kilo/skill/cycling-physics/SKILL.md`
   - `BIKE_SKILLS.md`
   - `AGENTS.md`
   - `InitialDescription.md`
   - `ant_plus_or_ble_mcp_bridge.py`

2. Validate `kilo.json` syntax is valid JSON.
3. Validate all YAML frontmatter in `.md` files is parseable YAML.
4. Confirm Python 3 is available: `python3 --version` (must be 3.8+).
5. Confirm MCP Python scripts are syntactically valid:
   - `python3 -m py_compile mcp_filesystem.py`
   - `python3 -m py_compile mcp_fetch.py`
6. Smoke-test MCP servers via stdin:
   - `echo '{"jsonrpc":"2.0","id":1,"method":"initialize"}' | python3 mcp_filesystem.py | head -c 200`
   - `echo '{"jsonrpc":"2.0","id":1,"method":"initialize"}' | python3 mcp_fetch.py | head -c 200`
   - Both should return a JSON response containing `"serverInfo"`.
7. Confirm Python HTTP server works:
   - `python3 -m http.server 8080 &`
   - `curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/` should return `200`
   - Kill the server process after verification.

**Infrastructure setup is complete when all checks pass.**

---

## Phase 2: Implementation

### Step 2.1 — Generate the Implementation Plan

Before writing any code, produce a detailed plan covering:

1. **HTML Structure** — Document layout: map container, routing panel (top-left), inset mini-map (top-right), telemetry dashboard panel (bottom), climb alert banner.
2. **CSS Strategy** — Dark theme with CSS custom properties, responsive grid for stats, absolute positioning for overlays, mobile-first media queries.
3. **JavaScript Architecture**:
   - Map initialization (main map + inset map)
   - GPS geolocation with simulated fallback
   - OSRM route fetching and parsing
   - Gradient-colored polyline rendering (segmented by slope)
   - Telemetry update loop (1 Hz)
   - Power calculation engine
   - Climb detection and alert logic
   - Dynamic rerouting on deviation detection
4. **Data Flow** — GPS → state update → telemetry calculations → DOM update. Route fetch → coordinate parse → gradient analysis → polyline rendering + inset map.
5. **Test Cases** — Map out how each physics test case maps to the code.
6. **File Structure** — Single file `index.html` with embedded CSS and JS.
7. **GitHub Pages Considerations** — All `https://` absolute URLs, no relative-path asset references, Leaflet loaded from CDN, OSRM from public API.
8. **GPS / HTTPS Strategy** — `navigator.geolocation` only works on HTTPS. Local dev uses `http://localhost` (treated as secure context by browsers). Production uses GitHub Pages HTTPS.

Write this plan into a file called `IMPLEMENTATION_PLAN.md`.

---

### Step 2.2 — Implement the HTML Shell

Write `index.html` with the complete HTML structure:

- `<head>` with meta viewport, Leaflet CSS link (`https://unpkg.com/leaflet@1.9.4/dist/leaflet.css`), dark theme CSS custom properties, Leaflet JS CDN script reference (`https://unpkg.com/leaflet@1.9.4/dist/leaflet.js`).
- `<body>` with:
  - `#app-container` (flex column, full viewport height)
  - `#map` div (takes flex:1)
  - `#inset-container` > `#inset-map` (absolute positioned top-right)
  - `#routing-panel` with start input, end input, "Plan Route" button (absolute positioned top-left)
  - `#dashboard` panel at bottom with:
    - Rider/Bike weight inputs
    - 6-card stats grid: Power (W), Speed (km/h), Gradient (%), Distance (km), Elev. Gain (m), Heading (°)
    - `#climb-alert` banner (hidden by default, shown on steep gradients)

**Critical requirement**: All external resource URLs must use `https://`. Do NOT use protocol-relative URLs (`//unpkg.com/...`). Do NOT use relative paths. GitHub Pages hosts at a subpath so any hardcoded relative asset paths will 404.

**Do not write CSS or JS yet** — only the structural HTML.

---

### Step 2.3 — Implement the CSS

Write the complete embedded CSS in `<style>`:

- CSS custom properties for the dark theme palette (`--bg-dark: #121214`, `--bg-panel: #1a1a1e`, `--accent-green: #4ade80`, `--accent-blue: #3b82f6`, etc.)
- `* { box-sizing: border-box; margin: 0; padding: 0; }`
- Body: `background: var(--bg-dark)`, `color: var(--text-main)`, `overflow: hidden`, `height: 100vh`, `display: flex`, `flex-direction: column`
- `#app-container`: `position: relative`, `flex: 1`, `display: flex`, `flex-direction: column`
- `#map`: `width: 100%`, `flex: 1`, `z-index: 1`
- `#dashboard`: `position: absolute`, `bottom: 0`, `width: 100%`, `z-index: 10`, `border-radius: 16px 16px 0 0`, `max-height: 55%`, `overflow-y: auto`
- `.input-row`: `display: grid`, `grid-template-columns: 1fr 1fr`, `gap: 10px`
- `.stats-grid`: `display: grid`, `grid-template-columns: repeat(3, 1fr)`, `gap: 8px`
- `.stat-card` / `.stat-val` / `.stat-lbl` styling
- `#climb-alert`: hidden by default, flex column when `.active`
- `#inset-container`: `position: absolute`, `top: 16px`, `right: 16px`, `width: 110px`, `height: 110px`, `border-radius: 8px`, `z-index: 5`, `overflow: hidden`, `pointer-events: none`
- `#routing-panel`: `position: absolute`, `top: 16px`, `left: 16px`, `z-index: 5`, `width: calc(100% - 160px)`
- Button hover transitions
- Mobile adjustments if needed at smaller viewports

---

### Step 2.4 — Implement JavaScript: Initialization and Maps

Write the first `<script>` block with:

1. **State object** `userState` with `lat`, `lng`, `alt`, `speed` (m/s), `totalDistance`, `totalElevationGain`, `lastLat`, `lastLng`, `lastAlt`.
2. **Module-level variables**: `mainMap`, `insetMap`, `userMarker`, `routeLine`, `insetRouteLine`, `routeCoordinates[]`, `currentRouteIndex`.
3. **`DOMContentLoaded` handler**:
   - Initialize `mainMap` with `L.map('map', { zoomControl: false })` at zoom 15 centered on `userState`.
   - Add OpenStreetMap tile layer (`https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png`).
   - Create `userMarker` as `L.circleMarker`.
   - Initialize `insetMap` (no controls, no dragging, no scroll wheel) centered at zoom 12.
   - Call `initGeolocator()`.
   - Start `setInterval(processTelemetryLoop, 1000)`.
4. **`initGeolocator()`**:
   - Check `navigator.geolocation`. If unavailable, log a warning — the app still works with simulated data.
   - Call `watchPosition` with `enableHighAccuracy: true`, `maximumAge: 1000`.
   - On success: update `userState.lat`, `lng`, `alt`, `speed`.
   - On error: log warning, continue using simulated values. This is expected on desktop machines without GPS hardware.
5. **`calculateRoute()`** async function:
   - Read start/end inputs.
   - Fetch from `https://router.project-osrm.org/route/v1/driving/{startLon},{startLat};{endLon},{endLat}?geometries=geojson&overview=full&alternatives=false&steps=true` (full `https://` URL — no protocol-relative).
   - Parse `data.routes[0].geometry.coordinates` into `routeCoordinates` with `lat`, `lng`, synthetic `alt` (sinusoidal elevation profile).
   - Call `plotRouteGradients()`.

---

### Step 2.5 — Implement JavaScript: Route Rendering with Gradient Colors

Implement `plotRouteGradients()`:

1. Remove existing `routeLine` and `insetRouteLine` if present.
2. Draw `insetRouteLine` as a simple blue `L.polyline` on the inset map and fit bounds.
3. On the main map, iterate through `routeCoordinates`:
   - For each consecutive pair `(i, i+1)`, calculate:
     - `dist = mainMap.distance([p1.lat, p1.lng], [p2.lat, p2.lng])`
     - `run = p2.alt - p1.alt`
     - `grade = (run / dist) * 100`
   - Assign segment color based on grade:
     - `< 2%`: green (`#4ade80`)
     - `2-5%`: yellow (`#eab308`)
     - `5-8%`: orange (`#f97316`)
     - `> 8%`: red (`#ef4444`)
   - Create `L.polyline` for each segment with the assigned color and add to a `L.featureGroup`.
4. Add the feature group to the main map as `routeLine`.

---

### Step 2.6 — Implement JavaScript: Physics Engine

Implement the power calculation functions:

1. **`calculatePower(mass, gradeDecimal, velocityMps, cdA, crr, eta)`**:
   - Compute `P_gravity`, `P_drag`, `P_rolling` using formulas from the skill file.
   - Return `P_total`.
2. **`calculateBalancePower(mass, gradeDecimal)`**:
   - Call `calculatePower` with `velocity = 1.667` (6 km/h).
3. **`calculateGrade(p1, p2)`**:
   - Compute distance and altitude diff, return grade as percentage.
4. **`haversineDistance(lat1, lon1, lat2, lon2)`**:
   - Implement the Haversine formula with R = 6371000 m.
5. **`msToKmh(mps)`** and **`kmhToMs(kmh)`**:
   - Simple multipliers.

---

### Step 2.7 — Implement JavaScript: Telemetry Loop and Climb Detection

Implement `processTelemetryLoop()`:

1. **Simulate movement** if GPS is not providing real data:
   - If `routeCoordinates.length > 0` and `currentRouteIndex < routeCoordinates.length - 1`:
     - Advance `currentRouteIndex` by 1 per tick.
     - Set `userState.lat/lng/alt` from `routeCoordinates[currentRouteIndex]`.
     - Calculate speed from distance between consecutive route points.
   - Otherwise, simulate small random movement around current position.
2. **Update telemetry**:
   - Calculate distance from last position using Haversine, add to `totalDistance`.
   - If altitude increased, add difference to `totalElevationGain`.
   - Calculate current grade from last two positions.
   - Calculate power using current speed and grade.
   - Calculate balance power using current grade.
   - Calculate bearing from last two positions.
3. **Update DOM**:
   - Set `#val-power`, `#val-speed`, `#val-grade`, `#val-dist`, `#val-climb`, `#val-bearing`.
4. **Update map**:
   - Move `userMarker` to new position.
   - Pan the main map to keep user centered.
   - Update inset map center.
5. **Climb detection**:
   - If current grade > 5%: show `#climb-alert` with `.active` class.
     - Calculate remaining distance along route where grade > 5%.
     - Set `#climb-remaining`, `#climb-min-speed` (6.0 km/h constant), `#climb-min-power` (from `calculateBalancePower`).
   - Else: hide `#climb-alert`.
6. **Dynamic rerouting check**:
   - If `routeCoordinates.length > 0`:
     - Check if current position is > 100m from nearest route segment.
     - If deviation detected, auto-call `calculateRoute()` to recalculate.

---

### Step 2.8 — Verify Physics Against Test Cases

1. Open `index.html` at `http://localhost:8080` (start the Python HTTP server first).
2. Run the three physics test cases from `.kilo/skill/cycling-physics/SKILL.md` by calling the power calculation function programmatically from the browser console or a Python test script.
3. Log actual vs expected values.
4. If any test case deviates by more than ±2%, identify the source of error (unit conversion, formula transcription, constant value) and fix it.
5. Re-run until all three test cases pass.

---

### Step 2.9 — Run the Test Command

Invoke `/test-telemetry` to execute the comprehensive test harness:

1. Power calculation (3 test cases).
2. Speed conversion.
3. Gradient conversion.
4. Haversine distance (known test: from London to Paris ≈ 344 km).
5. Elevation gain accumulation.

The test harness may run via Python (extracting JS logic or reimplementing the math in Python for validation) or via a headless browser. All tests must output PASS. Fix any failures.

---

### Step 2.10 — Launch Preview and Validate UX

Invoke `/preview-app` to start the Python HTTP server at `http://localhost:8080`.

Manual validation checklist (perform each via webfetch or documented observation):

1. Page loads without console errors.
2. Map tiles render in both main map and inset map.
3. Routing panel accepts start/end coordinates.
4. "Plan Route" button triggers a route fetch and draws color-coded polylines.
5. Inset map shows the full route overview.
6. Telemetry panel shows updating values (power, speed, gradient, distance, elevation, heading).
7. Gradient coloring reflects steepness: green (flat), yellow (moderate), orange (steep), red (very steep).
8. Climb alert appears when gradient exceeds 5%, showing distance remaining and min stability power.
9. GPS simulation advances position along the route (or falls back to simulated random movement).
10. Dashboard is scrollable on small screens.
11. UI is usable on a mobile-width viewport (375px width).
12. **All resource URLs use `https://`** — no mixed-content warnings in the browser console.
13. The OSRM fetch URL (`https://router.project-osrm.org/...`) returns valid GeoJSON route data.
14. The app does NOT rely on any relative-path assets that would break when deployed under a GitHub Pages subpath.
15. `navigator.geolocation` is detected and the watchPosition callback fires (may timeout on desktop — this is fine).

Log any failures found and fix before proceeding.

---

### Step 2.11 — Validate the Physics Skill

Invoke `/validate-physics` to cross-check the implementation against the skill's test cases:

1. Open the JavaScript physics functions in `index.html`.
2. Run each test case programmatically.
3. Report results.

The skill should report all three test cases within ±2% tolerance.

---

### Step 2.12 — Dynamic Rerouting Validation

Manually test dynamic rerouting:

1. Plan a route between two points.
2. Simulate deviating from the route by setting `userState.lat/lng` to a point > 100m from the nearest route segment (via browser console or by modifying the simulation logic).
3. Verify that `calculateRoute()` is called automatically.
4. Verify the new route renders and telemetry continues.

---

### Step 2.13 — Local End-to-End Validation

1. Kill any existing `python3 -m http.server` process.
2. Restart the preview server: `python3 -m http.server 8080`.
3. Open `http://localhost:8080` in a browser.
4. Enter start coordinate `51.0447,-114.0708` and end coordinate `51.0500,-114.0950` in the routing panel.
5. Click "Plan Route" and verify:
   - A colored route polyline appears on the main map.
   - The inset map shows the full route.
   - The telemetry loop begins and values update every second.
   - The gradient-based color coding is visible (green/yellow/orange/red segments).
6. Wait for the simulated position to reach a steep segment and verify the climb alert panel appears.
7. Verify the dashboard panel is scrollable (resize the browser to a mobile height).

---

### Step 2.14 — Deploy to GitHub Pages

Deploy the application to GitHub Pages for mobile GPS testing over HTTPS.

**2.14.1 — Initialize Git Repository**

```bash
cd /home/James/Documents/HarnessTutorial
git init
git checkout -b main
```

**2.14.2 — Create `.gitignore`**

Write `.gitignore`:
```
__pycache__/
*.pyc
.DS_Store
```

**2.14.3 — Create GitHub Repository and Push**

1. Create a new **public** repository on GitHub named e.g. `cycling-dashboard`.
2. Add the remote and push:

```bash
git add -A
git commit -m "Initial commit: Cyclist Navigation & Power Telemetry Dashboard"
git remote add origin https://github.com/<username>/cycling-dashboard.git
git push -u origin main
```

**2.14.4 — Enable GitHub Pages**

1. Go to repository Settings → Pages.
2. Set Source to "Deploy from a branch", branch `main`, folder `/ (root)`.
3. Save. GitHub Pages will deploy at `https://<username>.github.io/cycling-dashboard/`.

**2.14.5 — Verify GitHub Pages Deployment (Desktop)**

1. Wait 1-2 minutes for the initial deploy.
2. Access the app at `https://<username>.github.io/cycling-dashboard/`.
3. Confirm the page loads over HTTPS (check the URL bar / padlock icon).
4. Confirm `navigator.geolocation` is available (browser console: `!!navigator.geolocation` should print `true`). Note: on a desktop machine without GPS hardware the API may return a timeout — the simulated fallback must still produce moving telemetry.
5. Confirm Leaflet tiles load (no 404s or mixed-content warnings).
6. Confirm OSRM routing works by entering start/end coordinates and clicking "Plan Route".
7. Confirm the browser console shows zero errors and zero mixed-content warnings.

**2.14.6 — Mobile GPS Testing** (manual, by developer)

1. Open `https://<username>.github.io/cycling-dashboard/` on a mobile phone's browser (Safari on iOS, Chrome on Android).
2. Grant location permission when prompted by the browser.
3. Verify the blue dot (user marker) appears at or near the device's current location.
4. Enter a nearby destination address or coordinates and tap "Plan Route".
5. Begin moving (walking, cycling, or as a passenger in a vehicle) and verify:
   - The blue dot tracks movement along the map.
   - Telemetry values (speed, distance, power) update in real time consistent with actual movement.
   - Power output changes with speed changes and detected gradient changes.
   - If a hill exceeding ~5% gradient is encountered, the climb alert banner appears.
   - If the user deviates significantly from the planned route, a new route is automatically calculated.
   - The inset map always shows the full route overview.
6. Rotate the phone to landscape — verify the UI adapts.

---

### Step 2.15 — Final Integration Test

Run a complete end-to-end test:

1. Start fresh: delete `index.html`, remove `.git/` directory, and reinitialize the repository.
2. Rebuild the entire application using only the infrastructure files and the commands defined in this guide.
3. Deploy to a fresh GitHub Pages site.
4. Verify the rebuilt app passes all tests — local validation (physics test cases, telemetry harness) AND GitHub Pages deployment verification (HTTPS, GPS API availability, no mixed content).

This ensures the guide is complete, self-contained, and fully deployable.

---

## Appendix: MCP Configuration Reference

### Filesystem MCP Server (Python)
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "python3",
      "args": ["mcp_filesystem.py"]
    }
  }
}
```
**Exposed Tools**: `read_file`, `write_file`, `list_directory`, `search_files`, `get_file_info`, `move_file`, `copy_file`

### Fetch MCP Server (Python)
```json
{
  "mcpServers": {
    "fetch": {
      "command": "python3",
      "args": ["mcp_fetch.py"]
    }
  }
}
```
**Exposed Tools**: `fetch` (HTTP GET requests)

### Cycling Telemetry Bridge (Optional, Live Hardware — Python)
```json
{
  "mcpServers": {
    "cycling-telemetry-bridge": {
      "command": "python3",
      "args": ["ant_plus_or_ble_mcp_bridge.py"],
      "env": { "BIND_PORT": "8080" }
    }
  }
}
```
**Exposed Tools**: `get_live_sensor_readings`

---

## Appendix: File Tree (Final State)

```
/home/James/Documents/HarnessTutorial/
├── AGENTS.md
├── BIKE_SKILLS.md
├── IMPLEMENTATION_PLAN.md
├── InitialDescription.md
├── InitialDescription.txt
├── ant_plus_or_ble_mcp_bridge.py
├── index.html                   ← THE APPLICATION (target output)
├── kilo.json
├── mcp_filesystem.py
├── mcp_fetch.py
└── .kilo/
    ├── kilo.json
    ├── agent/
    │   └── cyclist-builder.md
    ├── command/
    │   ├── preview-app.md
    │   ├── test-telemetry.md
    │   └── validate-physics.md
    └── skill/
        └── cycling-physics/
            └── SKILL.md
```

---

*End of Build Guide. Pass this file to the agent harness to begin execution.*