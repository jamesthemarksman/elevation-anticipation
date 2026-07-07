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