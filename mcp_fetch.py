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