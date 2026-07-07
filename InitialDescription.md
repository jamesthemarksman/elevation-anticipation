# Cyclist Navigation & Power Telemetry Dashboard

## Learning Objective

Understand how an AI coding harness interfaces with Skills, Templates, Tools, and Model Context Protocol (MCP) Servers by configuring a harness to build a feature-complete, single-file HTML5 mobile-responsive application.

## Core Capabilities

- **Core Navigation**: Real-time mobile GPS tracking, automated map re-centering, route plotting between start/end points using OpenStreetMap/Leaflet, and an on-screen route overview inset.
- **Dynamic Rerouting**: Automatic route recalculation if the rider deviates from the planned path.
- **Advanced Telemetry**: Live calculation of speed, total distance, cumulative elevation gain, and real-time mechanical power output (W) based on rider/bike weight, speed, and slope gradient.
- **Gradient Awareness**: Color-coded route lines mapping slope steepness, countdowns for sustained climbs (>5% gradient), and minimum balance speed thresholds with required wattage.

## Harness Architecture

The AI agent harness connects to:

- **MCP Filesystem Tool** — Reads/writes `index.html` and assets
- **MCP Fetch/Web Tool** — Pulls Leaflet.js and OSRM routing APIs
- **Mathematical Skill** — Validates physics formulas (power, grade)

### MCP Servers

The harness connects to `mcp-server-filesystem` for secure file read/write and `mcp-server-fetch` to query external routing endpoints (e.g., Open Source Routing Machine).

### Tools

The agent executes atomic functions like `write_file`, `view_code`, and `bash_execute` (e.g., to run a local preview web server).

### Skills / Templates

Pre-configured computational skills (physics formulas for rolling resistance and aerodynamic drag) ensure the JavaScript telemetry code is mathematically sound.

## Physical & Mathematical Formulas

### Mechanical Power Equation

Total power required to propel a bicycle:

\[
P_{\text{total}} = \frac{P_{\text{gravity}} + P_{\text{drag}} + P_{\text{rolling}}}{\eta}
\]

Where:

- \(P_{\text{gravity}} = m \cdot g \cdot \sin(\arctan(G)) \cdot v\)
- \(P_{\text{drag}} = 0.5 \cdot C_d \cdot A \cdot \rho \cdot v^3\)
- \(P_{\text{rolling}} = m \cdot g \cdot \cos(\arctan(G)) \cdot C_{rr} \cdot v\)

| Variable | Description | Assumed Value |
|---|---|---|
| \(m\) | Total mass (rider + bicycle) | — |
| \(g\) | Gravity | \(9.81 \, \text{m/s}^2\) |
| \(G\) | Gradient as decimal (e.g., 0.05 for 5%) | — |
| \(v\) | Ground-relative velocity | — |
| \(C_d \cdot A\) | Aerodynamic drag coefficient area | ≈ 0.38 |
| \(\rho\) | Air density | ≈ 1.2 kg/m³ |
| \(C_{rr}\) | Rolling resistance coefficient | ≈ 0.005 (pavement) |
| \(\eta\) | Drivetrain efficiency | ≈ 0.95 |

### Minimum Balance Speed & Stability Wattage

Formulas for the minimum speed required to maintain bicycle stability without stalling on steep inclines, and the wattage needed to sustain that speed.

## Extending the Project

### Custom Skills File (`BIKE_SKILLS.md`)

A localized system prompt acting as tool context, containing rolling resistance profiles (Asphalt: 0.004, Pavement: 0.005, Gravel: 0.008) and aerodynamic profiles (Racing Drops: 0.32, Touring Hood: 0.38, Urban Commuter: 0.42). The harness reads these via its Filesystem Tool to override hardcoded coefficients.

### MCP Server for Live Testing

A local proxy script connects to Bluetooth smart trainers or power meters via an MCP server configuration:

```json
{
  "mcpServers": {
    "cycling-telemetry-bridge": {
      "command": "node",
      "args": ["path/to/ant_plus_or_ble_mcp_bridge.js"],
      "env": { "BIND_PORT": "8080" }
    }
  }
}
```

This exposes a `get_live_sensor_readings` tool, allowing the harness to read live hardware data instead of simulated values.