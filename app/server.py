#!/usr/bin/env python3
"""gatekit studio - a local web app for gatekit.

Runs the real gatekit tools (bin/preflight, bin/brief) on directories you
choose on THIS computer, and composes paste-ready workflow prompts.

Privacy and trust boundary:
- Binds to 127.0.0.1 only. No network calls, no analytics, no CDNs.
- Scans are read-only. --run-checks is deliberately NOT exposed here because
  it executes commands defined by the scanned repo; use the terminal for
  that, only on code you trust.
- Uploaded zips are extracted to a temporary directory, scanned, deleted.
- Ratings are stored only on this computer in app/data/ratings.json.
"""
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

APP_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(APP_DIR)
STATIC_DIR = os.path.join(APP_DIR, "static")
DATA_DIR = os.path.join(APP_DIR, "data")
RATINGS_FILE = os.path.join(DATA_DIR, "ratings.json")
PREFLIGHT = os.path.join(REPO_ROOT, "bin", "preflight")
BRIEF = os.path.join(REPO_ROOT, "bin", "brief")
WORKFLOWS_DIR = os.path.join(REPO_ROOT, "workflows")

MAX_UPLOAD_BYTES = 25 * 1024 * 1024
MAX_EXTRACT_FILES = 2000
TOOL_TIMEOUT = 120
LOCAL_HEADER = "x-gatekit-local"

# Hostnames the server will answer for. The app binds to 127.0.0.1 only;
# without this check a DNS-rebinding site (evil.example resolving to
# 127.0.0.1) would be same-origin to the browser and could read scan
# results and post scans/ratings with the custom header.
ALLOWED_HOSTS = {"127.0.0.1", "localhost", "::1"}


def host_is_allowed(host_header):
    """Parse Host robustly: optional bracketed IPv6, optional :port.
    Only exact loopback names pass; anything else (including rebinding
    domains, trailing-dot tricks aside, which we normalize) is rejected."""
    if not host_header or len(host_header) > 100:
        return False
    host = host_header.strip().lower()
    if host.startswith("["):
        end = host.find("]")
        if end == -1:
            return False
        name = host[1:end]
        rest = host[end + 1:]
        if rest and not (rest.startswith(":") and rest[1:].isdigit()):
            return False
    else:
        if host.count(":") > 1:  # bare IPv6 without brackets: reject
            return False
        if ":" in host:
            name, _, port = host.rpartition(":")
            if not port.isdigit():
                return False
        else:
            name = host
    name = name.rstrip(".")
    return name in ALLOWED_HOSTS


def run_tool(tool, path):
    """Run a gatekit CLI read-only (--json). Returns (ok, data_or_error)."""
    try:
        proc = subprocess.run(
            [sys.executable, tool, path, "--json"],
            capture_output=True, text=True, timeout=TOOL_TIMEOUT)
    except subprocess.TimeoutExpired:
        return False, {"error": "scan timed out after %ds" % TOOL_TIMEOUT}
    except OSError as e:
        return False, {"error": "could not run tool: %s" % e}
    if proc.returncode not in (0, 1):  # 1 = findings, still a valid report
        return False, {"error": (proc.stderr or "tool failed").strip()[:500]}
    try:
        return True, json.loads(proc.stdout)
    except json.JSONDecodeError:
        return False, {"error": "tool produced unreadable output"}


def resolve_scan_dir(raw):
    """Validate a user-supplied directory path. Returns (ok, path_or_error)."""
    if not raw or not isinstance(raw, str):
        return False, "path is required"
    if len(raw) > 500:
        return False, "path too long"
    path = os.path.realpath(os.path.expanduser(raw.strip()))
    if not os.path.isdir(path):
        return False, "not a directory: %s" % raw
    if path == os.path.sep:
        return False, "refusing to scan the filesystem root"
    return True, path


def extract_zip_safely(body):
    """Extract uploaded zip bytes into a temp dir. Returns (ok, dir_or_error)."""
    try:
        zf = zipfile.ZipFile(io.BytesIO(body))
    except zipfile.BadZipFile:
        return False, "not a valid zip file"
    names = zf.namelist()
    if len(names) > MAX_EXTRACT_FILES:
        return False, "zip has too many files (max %d)" % MAX_EXTRACT_FILES
    dest = tempfile.mkdtemp(prefix="gatekit-upload-")
    dest_real = os.path.realpath(dest)
    total = 0
    try:
        return _extract_into(zf, dest_real)
    except ZipUnsafe as e:
        import shutil
        shutil.rmtree(dest_real, ignore_errors=True)
        return False, str(e)
    except (zipfile.BadZipFile, OSError, EOFError, RuntimeError):
        # corrupt entry (bad CRC), truncated archive, unreadable member:
        # clean up and report, never drop the connection or leak the dir
        import shutil
        shutil.rmtree(dest_real, ignore_errors=True)
        return False, "zip file is damaged or unreadable"


class ZipUnsafe(Exception):
    pass


def _extract_into(zf, dest_real):
    names = zf.namelist()
    total = 0
    for info in zf.infolist():
        name = info.filename.replace("\\", "/")
        if name.startswith("/") or ".." in name.split("/"):
            raise ZipUnsafe("unsafe path inside zip: %s" % info.filename)
        if info.is_dir():
            continue
        total += info.file_size
        if total > MAX_UPLOAD_BYTES * 4:
            raise ZipUnsafe("zip contents too large")
        target = os.path.realpath(os.path.join(dest_real, name))
        if not (target == dest_real or target.startswith(dest_real + os.sep)):
            raise ZipUnsafe("unsafe path inside zip: %s" % info.filename)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with zf.open(info) as src, open(target, "wb") as out:
            while True:
                chunk = src.read(65536)
                if not chunk:
                    break
                out.write(chunk)
    return True, dest_real


INPUT_RE = re.compile(r"^\s*-\s*`([A-Z][A-Z0-9_-]+)`(\s*\(optional\))?\s*:\s*(.+?)\s*$")


def load_workflows():
    """Parse the real workflow markdown files into UI-friendly records."""
    items = []
    for fname in sorted(os.listdir(WORKFLOWS_DIR)):
        if not fname.endswith(".md"):
            continue
        slug = fname[:-3]
        with open(os.path.join(WORKFLOWS_DIR, fname), "r",
                  encoding="utf-8") as f:
            text = f.read()
        title = slug
        m = re.search(r"^#\s+(.+)$", text, re.M)
        if m:
            title = m.group(1).strip()
        purpose = ""
        m = re.search(r"## Purpose\s*\n\s*\n(.+?)(?:\n\s*\n|\Z)", text, re.S)
        if m:
            purpose = " ".join(m.group(1).split())
        inputs = []
        m = re.search(r"## Inputs\s*\n(.*?)(?:\n## |\Z)", text, re.S)
        if m:
            for line in m.group(1).splitlines():
                im = INPUT_RE.match(line)
                if im:
                    inputs.append({"name": im.group(1),
                                   "optional": bool(im.group(2)),
                                   "hint": im.group(3)})
        items.append({"slug": slug, "title": title, "purpose": purpose,
                      "inputs": inputs})
    return items


def render_prompt(slug, values):
    """Compose the paste-ready prompt: real workflow text + filled inputs."""
    path = os.path.join(WORKFLOWS_DIR, os.path.basename(slug) + ".md")
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    lines = ["## My inputs", ""]
    for name, value in values.items():
        if not re.fullmatch(r"[A-Z][A-Z0-9_-]{0,40}", str(name)):
            continue
        lines.append("- `%s`: %s" % (name, str(value).strip()[:4000]))
    return text.rstrip() + "\n\n---\n\n" + "\n".join(lines) + "\n"


def load_ratings():
    try:
        with open(RATINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return []


def save_rating(entry):
    os.makedirs(DATA_DIR, exist_ok=True)
    ratings = load_ratings()
    ratings.append(entry)
    ratings = ratings[-500:]
    tmp = RATINGS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(ratings, f, indent=1)
    os.replace(tmp, RATINGS_FILE)
    return ratings


class Handler(BaseHTTPRequestHandler):
    server_version = "gatekit-studio/0.3.0"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        sys.stderr.write("studio: " + fmt % args + "\n")

    def setup(self):
        super().setup()
        self.connection.settimeout(30)  # slow clients must not tie up a thread

    # -- helpers ---------------------------------------------------------
    def _send(self, code, body, ctype="application/json"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode("utf-8")
        elif isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy",
                         "default-src 'self'; style-src 'self' 'unsafe-inline'")
        self.end_headers()
        self.wfile.write(body)

    def _local_only(self):
        """POSTs must carry our custom header; cross-site forms cannot."""
        return self.headers.get(LOCAL_HEADER) == "1"

    def _read_body(self):
        try:
            n = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return None
        if n < 0 or n > MAX_UPLOAD_BYTES:
            return None
        return self.rfile.read(n)

    def _read_json(self):
        body = self._read_body()
        if body is None:
            return None
        try:
            data = json.loads(body.decode("utf-8", errors="replace"))
        except json.JSONDecodeError:
            return None
        return data if isinstance(data, dict) else None

    # -- routes ----------------------------------------------------------
    def _gate(self):
        if not host_is_allowed(self.headers.get("Host")):
            self._send(403, {"error": "host not allowed - this app answers localhost only"})
            return False
        return True

    def do_GET(self):
        if not self._gate():
            return
        if self.path == "/" or self.path == "/index.html":
            with open(os.path.join(STATIC_DIR, "index.html"), "rb") as f:
                self._send(200, f.read(), "text/html; charset=utf-8")
            return
        if self.path.startswith("/static/"):
            name = os.path.basename(self.path[len("/static/"):])
            path = os.path.join(STATIC_DIR, name)
            if os.path.isfile(path):
                ctype = ("text/css" if name.endswith(".css") else
                         "application/javascript" if name.endswith(".js")
                         else "application/octet-stream")
                with open(path, "rb") as f:
                    self._send(200, f.read(), ctype)
                return
            self._send(404, {"error": "not found"})
            return
        if self.path == "/api/workflows":
            self._send(200, {"workflows": load_workflows()})
            return
        if self.path == "/api/ratings":
            self._send(200, {"ratings": load_ratings()})
            return
        self._send(404, {"error": "not found"})

    def do_POST(self):
        if not self._gate():
            return
        if not self._local_only():
            self._send(403, {"error": "missing local-app header"})
            return
        if self.path == "/api/scan" or self.path == "/api/brief":
            data = self._read_json()
            if data is None:
                self._send(400, {"error": "bad request body"})
                return
            ok, resolved = resolve_scan_dir(data.get("path"))
            if not ok:
                self._send(400, {"error": resolved})
                return
            tool = PREFLIGHT if self.path == "/api/scan" else BRIEF
            ok, result = run_tool(tool, resolved)
            self._send(200 if ok else 500, result)
            return
        if self.path == "/api/upload":
            body = self._read_body()
            if body is None:
                self._send(400, {"error": "zip too large or missing (max 25 MB)"})
                return
            ok, dest = extract_zip_safely(body)
            if not ok:
                self._send(400, {"error": dest})
                return
            try:
                results = {}
                ok1, results["preflight"] = run_tool(PREFLIGHT, dest)
                ok2, results["brief"] = run_tool(BRIEF, dest)
                results["ok"] = ok1 and ok2
                self._send(200, results)
            finally:
                import shutil
                shutil.rmtree(dest, ignore_errors=True)
            return
        if self.path == "/api/render":
            data = self._read_json()
            if data is None:
                self._send(400, {"error": "bad request body"})
                return
            slug = str(data.get("workflow", ""))
            inputs = data.get("inputs") or {}
            if not isinstance(inputs, dict):
                self._send(400, {"error": "inputs must be an object"})
                return
            prompt = render_prompt(slug, inputs)
            if prompt is None:
                self._send(404, {"error": "unknown workflow"})
                return
            self._send(200, {"prompt": prompt})
            return
        if self.path == "/api/rate":
            data = self._read_json()
            if data is None:
                self._send(400, {"error": "bad request body"})
                return
            try:
                rating = int(data.get("rating"))
            except (TypeError, ValueError):
                self._send(400, {"error": "rating must be 1-5"})
                return
            if not 1 <= rating <= 5:
                self._send(400, {"error": "rating must be 1-5"})
                return
            entry = {
                "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                "kind": str(data.get("kind", ""))[:30],
                "subject": str(data.get("subject", ""))[:200],
                "rating": rating,
                "note": str(data.get("note", ""))[:1000],
            }
            ratings = save_rating(entry)
            self._send(200, {"saved": True, "count": len(ratings)})
            return
        self._send(404, {"error": "not found"})


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print("gatekit studio running at http://127.0.0.1:%d" % port)
    print("local only - stop with Ctrl+C")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
