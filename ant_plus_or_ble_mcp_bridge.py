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