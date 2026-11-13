#!/usr/bin/env python3
"""Qwen steuert die Valentina-Werkzeuge direkt im Terminal (ohne Open WebUI).
Aufruf:  python3 /workspace/ai/qwen_chat.py "Mach 2 Fotos von Valentina am Strand beim Joggen"
Ohne Argument: interaktiver Chat. Nur Standardbibliothek."""
import json
import sys
import urllib.request

OLLAMA = "http://127.0.0.1:11434/api/chat"
TOOLS = "http://127.0.0.1:8030"
MODEL = "qwen3.8:27b"
SYSTEM = ("Du bist die Produktionszentrale für Valentina (@valentina_gymcoach), eine offen KI-generierte Fitness-Coachin. "
          "Nutze die Werkzeuge, um Fotos, Videos, Sprachaufnahmen und Web-Recherchen zu erstellen. "
          "Inhalte bleiben Instagram-tauglich (sportlich, nicht sexualisiert). Antworte auf Deutsch, kurz, mit den Links.")


def _req(url, data=None, timeout=900):
    body = None if data is None else json.dumps(data).encode()
    r = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"},
                               method="POST" if data is not None else "GET")
    return json.loads(urllib.request.urlopen(r, timeout=timeout).read())


def load_tools():
    spec = _req(f"{TOOLS}/openapi.json")
    comps = spec.get("components", {}).get("schemas", {})
    tools, routes = [], {}
    for path, ops in spec["paths"].items():
        for method, op in ops.items():
            name = op.get("operationId", path.strip("/").replace("/", "_"))
            params = {"type": "object", "properties": {}, "required": []}
            ref = op.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {}).get("$ref")
            if ref:
                s = comps[ref.split("/")[-1]]
                params = {"type": "object", "properties": {k: {kk: vv for kk, vv in v.items() if kk in ("type", "description", "enum", "default")}
                                                            for k, v in s.get("properties", {}).items()},
                          "required": s.get("required", [])}
            for p in op.get("parameters", []):
                params["properties"][p["name"]] = {"type": p.get("schema", {}).get("type", "string")}
                params["required"].append(p["name"])
            tools.append({"type": "function", "function": {"name": name, "description": (op.get("description") or op.get("summary", ""))[:900], "parameters": params}})
            routes[name] = (method.upper(), path)
    return tools, routes


def call(routes, name, args):
    method, path = routes[name]
    for k in list(args):
        if "{" + k + "}" in path:
            path = path.replace("{" + k + "}", str(args.pop(k)))
    return _req(TOOLS + path, args if method == "POST" else None)


def turn(msgs, tools, routes):
    while True:
        r = _req(OLLAMA, {"model": MODEL, "messages": msgs, "tools": tools, "stream": False, "think": False})
        m = r["message"]
        msgs.append(m)
        if not m.get("tool_calls"):
            return m.get("content", "")
        for tc in m["tool_calls"]:
            fn = tc["function"]
            print(f"  → {fn['name']}({json.dumps(fn['arguments'], ensure_ascii=False)})", flush=True)
            try:
                out = call(routes, fn["name"], dict(fn["arguments"]))
            except Exception as e:  # noqa: BLE001
                out = {"error": str(e)}
            msgs.append({"role": "tool", "tool_name": fn["name"], "content": json.dumps(out, ensure_ascii=False)})


def main():
    tools, routes = load_tools()
    msgs = [{"role": "system", "content": SYSTEM}]
    if len(sys.argv) > 1:
        msgs.append({"role": "user", "content": " ".join(sys.argv[1:])})
        print(turn(msgs, tools, routes))
        return
    while True:
        try:
            q = input("\nDu: ").strip()
        except EOFError:
            break
        if q:
            msgs.append({"role": "user", "content": q})
            print("Qwen:", turn(msgs, tools, routes))


if __name__ == "__main__":
    main()
