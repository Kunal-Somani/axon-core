import ast
import math
import psutil
import platform
import os
from datetime import datetime, timezone
from pathlib import Path

try:
    from duckduckgo_search import DDGS
    _ddgs_available = True
except ImportError:
    _ddgs_available = False

# Safe math evaluator
_SAFE_MATH_NODES = {
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv,
    ast.Mod, ast.Pow, ast.USub, ast.UAdd
}

def _safe_eval(expr: str) -> str:
    try:
        tree = ast.parse(expr.strip(), mode='eval')
        for node in ast.walk(tree):
            if type(node) not in _SAFE_MATH_NODES:
                return f"Error: expression contains disallowed operations"
        result = eval(compile(tree, '<string>', 'eval'), {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"Calculation error: {e}"

PROJECT_ROOT = Path(__file__).parent.parent.parent
ALLOWED_LIST_PATHS = [PROJECT_ROOT, Path.home() / "Documents"]

TOOL_REGISTRY = {
    "get_system_info": lambda **_: {
        "os": platform.system(),
        "os_version": platform.version(),
        "python": platform.python_version(),
        "cpu_count": psutil.cpu_count(logical=True),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "ram_total_gb": round(psutil.virtual_memory().total / 1e9, 2),
        "ram_used_gb": round(psutil.virtual_memory().used / 1e9, 2),
        "disk_used_gb": round(psutil.disk_usage('/').used / 1e9, 2),
        "disk_total_gb": round(psutil.disk_usage('/').total / 1e9, 2),
    },
    "get_current_datetime": lambda **_: {
        "datetime": datetime.now(timezone.utc).isoformat(),
        "timezone": "UTC"
    },
    "list_directory": lambda path=".", **_: _list_directory(path),
    "search_web": lambda query="", **_: _search_web(query),
    "get_weather": lambda city="", **_: _get_weather(city),
    "calculate": lambda expression="", **_: {"result": _safe_eval(expression)},
}

def _list_directory(path: str) -> dict:
    target = Path(path).resolve()
    allowed = any(str(target).startswith(str(p.resolve())) for p in ALLOWED_LIST_PATHS)
    if not allowed:
        return {"error": f"Access denied: path '{path}' is outside allowed directories"}
    try:
        entries = [{"name": e.name, "type": "dir" if e.is_dir() else "file"} for e in sorted(target.iterdir())]
        return {"path": str(target), "entries": entries}
    except Exception as e:
        return {"error": str(e)}

def _search_web(query: str) -> dict:
    if not query:
        return {"error": "No query provided"}
    if not _ddgs_available:
        return {"error": "Web search not available"}
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
        return {"results": [{"title": r["title"], "body": r["body"], "url": r["href"]} for r in results]}
    except Exception as e:
        return {"error": str(e)}

def _get_weather(city: str) -> dict:
    if not city:
        return {"error": "No city provided"}
    try:
        import urllib.request, json as _json
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
        with urllib.request.urlopen(geo_url, timeout=5) as r:
            geo = _json.loads(r.read())
        if not geo.get("results"):
            return {"error": f"City '{city}' not found"}
        lat = geo["results"][0]["latitude"]
        lon = geo["results"][0]["longitude"]
        wx_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        with urllib.request.urlopen(wx_url, timeout=5) as r:
            wx = _json.loads(r.read())
        cw = wx["current_weather"]
        return {"city": city, "temperature_c": cw["temperature"], "windspeed_kmh": cw["windspeed"], "weathercode": cw["weathercode"]}
    except Exception as e:
        return {"error": str(e)}

def execute_tool(tool_name: str, params: dict) -> dict:
    if tool_name not in TOOL_REGISTRY:
        available = list(TOOL_REGISTRY.keys())
        return {"error": f"Tool '{tool_name}' not found. Available: {available}"}
    try:
        return TOOL_REGISTRY[tool_name](**params)
    except Exception as e:
        return {"error": f"Tool execution failed: {e}"}

def get_available_tools() -> list[str]:
    return list(TOOL_REGISTRY.keys())

def build_tool_grammar() -> str:
    tool_names = " | ".join(f'"{name}"' for name in TOOL_REGISTRY.keys())
    return f'''
root   ::= "{{" ws "\\"tool\\":" ws tool-name "," ws "\\"params\\":" ws object ws "}}"
tool-name ::= {tool_names}
object ::= "{{" ws (string ":" ws value ("," ws string ":" ws value)*)? "}}"
value  ::= string | number | "true" | "false" | "null" | object
string ::= "\\"" ([^"\\\\] | "\\\\" .)* "\\""
number ::= "-"? ([0-9]+ ("." [0-9]+)?)
ws     ::= [ \\t\\n]*
'''

TOOL_GRAMMAR = build_tool_grammar()