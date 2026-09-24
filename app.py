import html
import json
import os
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

STARTED_AT = time.monotonic()
RUNTIME_KEYS = (
    "RENDER",
    "RENDER_SERVICE_NAME",
    "RENDER_SERVICE_TYPE",
    "RENDER_EXTERNAL_HOSTNAME",
    "RENDER_EXTERNAL_URL",
    "RENDER_GIT_BRANCH",
    "RENDER_GIT_COMMIT",
    "RENDER_INSTANCE_ID",
    "RENDER_CPU_COUNT",
)


def runtime_data():
    data = {key: os.environ.get(key) for key in RUNTIME_KEYS}
    data["uptime_seconds"] = round(time.monotonic() - STARTED_AT, 3)
    data["current_time_utc"] = datetime.now(timezone.utc).isoformat()
    return data


class Handler(BaseHTTPRequestHandler):
    def send_content(self, status, content_type, body):
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/healthz":
            self.send_content(200, "application/json", json.dumps({"status": "ok"}))
            return
        if path == "/api/runtime":
            self.send_content(200, "application/json", json.dumps(runtime_data()))
            return
        if path == "/":
            rows = "".join(
                f"<tr><th>{html.escape(key)}</th><td>{html.escape(str(value))}</td></tr>"
                for key, value in runtime_data().items()
            )
            page = f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Bunny Render Control Lab</title></head>
<body><h1>Bunny Render Control Lab</h1><p>Running successfully on Render.</p><table>{rows}</table></body>
</html>"""
            self.send_content(200, "text/html; charset=utf-8", page)
            return
        self.send_content(404, "text/plain; charset=utf-8", "Not Found")

    def log_message(self, format, *args):
        print(f"{self.address_string()} - {format % args}", flush=True)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
