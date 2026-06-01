#!/usr/bin/env python3
"""
Local web server — Chatbot vs ReAct Agent demo.
Chạy: .venv/bin/python web_server.py
Mở:   http://localhost:8787
"""

import json
import os
import sys
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(ROOT, "web", "public")
CHARTS_DIR = os.path.join(ROOT, "charts")
sys.path.insert(0, ROOT)

load_dotenv()

PORT = int(os.getenv("WEB_PORT", "8787"))
_llm = None


def get_llm():
    global _llm
    if _llm is None:
        from test_chatbot import create_llm
        _llm = create_llm()
    return _llm


class DemoHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PUBLIC_DIR, **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/health":
            self._json(200, {
                "ok": True,
                "has_openai": bool(os.getenv("OPENAI_API_KEY", "").startswith("sk-")),
                "has_gemini": bool(os.getenv("GEMINI_API_KEY", "").startswith("AI")),
                "provider": os.getenv("DEFAULT_PROVIDER", "openai"),
                "model": os.getenv("DEFAULT_MODEL", "gpt-4o-mini"),
            })
            return
        if path == "/api/demo":
            self._json(405, {
                "error": "Method not allowed. Use POST with JSON body: {\"message\": \"your question\"}",
                "ui": f"http://localhost:{PORT}/",
            })
            return
        if path.startswith("/charts/"):
            self._serve_chart(path)
            return
        super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/api/demo":
            self._json(404, {"error": "Not found"})
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(body.decode())
        except json.JSONDecodeError:
            self._json(400, {"error": "Invalid JSON"})
            return

        message = (payload.get("message") or "").strip()
        if not message:
            self._json(400, {"error": "Message is required"})
            return

        try:
            from test_chatbot import run_chatbot
            from src.tools.finance_tools import FINANCE_TOOLS
            from src.tools.visual_tools import VISUAL_TOOLS
            from src.agent.agent import ReActAgent

            llm = get_llm()
            all_tools = FINANCE_TOOLS + VISUAL_TOOLS
            agent_result = ReActAgent(llm, all_tools, max_steps=10).run(message)
            if isinstance(agent_result, dict):
                agent_result["charts"] = [
                    {**c, "url": f"/charts/{c['filename']}"}
                    for c in agent_result.get("charts", [])
                ]
            result = {
                "chatbot": run_chatbot(llm, message),
                "agent": agent_result,
            }
            self._json(200, result)
        except Exception as e:
            self._json(500, {"error": str(e)})

    def _serve_chart(self, path: str):
        filename = os.path.basename(path)
        if not filename or ".." in filename:
            self.send_error(400)
            return
        chart_path = os.path.join(CHARTS_DIR, filename)
        if not os.path.isfile(chart_path):
            self.send_error(404)
            return
        with open(chart_path, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", "image/png")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)

    def _json(self, status: int, data: dict):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print(f"[web] {self.address_string()} {fmt % args}")


def main():
    if not os.path.isdir(PUBLIC_DIR):
        raise SystemExit(f"Không tìm thấy {PUBLIC_DIR}")

    server = ThreadingHTTPServer(("127.0.0.1", PORT), DemoHandler)
    print(f"Chatbot vs Agent — local web")
    print(f"  Mở UI:  http://localhost:{PORT}/")
    print(f"  API:    POST /api/demo  (JSON: {{\"message\": \"...\"}})")
    print(f"  Provider: {os.getenv('DEFAULT_PROVIDER', 'openai')} / {os.getenv('DEFAULT_MODEL', 'gpt-4o-mini')}")
    print("  Ctrl+C để dừng\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
