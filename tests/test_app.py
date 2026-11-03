import io
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(ROOT, "app", "server.py")
sys.path.insert(0, os.path.join(ROOT, "app"))
import server as app_server  # noqa: E402

HDR = {"Content-Type": "application/json", "X-Gatekit-Local": "1"}


def free_port():
    import socket
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class StudioServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.port = free_port()
        cls.httpd = app_server.ThreadingHTTPServer(("127.0.0.1", cls.port),
                                                   app_server.Handler)
        cls.thread = threading.Thread(target=cls.httpd.serve_forever,
                                      kwargs={"poll_interval": 0.05},
                                      daemon=True)
        cls.thread.start()
        cls.base = "http://127.0.0.1:%d" % cls.port
        # isolate ratings file from any real user data
        cls.tmp = tempfile.TemporaryDirectory()
        cls.orig_ratings = app_server.RATINGS_FILE
        app_server.RATINGS_FILE = os.path.join(cls.tmp.name, "ratings.json")

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        app_server.RATINGS_FILE = cls.orig_ratings
        cls.tmp.cleanup()

    def get(self, path):
        return urllib.request.urlopen(self.base + path, timeout=15)

    def post(self, path, payload, headers=None):
        req = urllib.request.Request(
            self.base + path, data=payload, method="POST",
            headers=headers or HDR)
        try:
            return urllib.request.urlopen(req, timeout=30)
        except urllib.error.HTTPError as e:
            return e

    def test_index_served(self):
        body = self.get("/").read().decode()
        self.assertIn("gatekit studio", body)

    def test_workflows_listed(self):
        data = json.loads(self.get("/api/workflows").read())
        slugs = [w["slug"] for w in data["workflows"]]
        self.assertEqual(len(slugs), 9)
        self.assertIn("ship-check", slugs)
        ship = [w for w in data["workflows"] if w["slug"] == "ship-check"][0]
        names = [i["name"] for i in ship["inputs"]]
        self.assertIn("CHANGE", names)
        self.assertIn("DIFF", names)

    def test_post_without_local_header_rejected(self):
        req = urllib.request.Request(
            self.base + "/api/scan", data=b'{"path": "."}', method="POST",
            headers={"Content-Type": "application/json"})
        try:
            urllib.request.urlopen(req, timeout=10)
            self.fail("expected 403")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 403)

    def test_scan_demo_repo_blocks_planted_secret(self):
        demo = os.path.join(ROOT, "examples", "demo-repo")
        resp = self.post("/api/scan", json.dumps({"path": demo}).encode())
        rep = json.loads(resp.read())
        self.assertFalse(rep["ok"])
        kinds = [(e["kind"], e.get("pattern")) for e in rep["errors"]]
        self.assertIn(("secret", "JWT"), kinds)

    def test_scan_rejects_missing_dir_and_root(self):
        resp = self.post("/api/scan", json.dumps({"path": "/no/such/dir"}).encode())
        self.assertEqual(resp.code, 400)
        resp = self.post("/api/scan", json.dumps({"path": "/"}).encode())
        self.assertEqual(resp.code, 400)

    def test_brief_on_demo_repo(self):
        demo = os.path.join(ROOT, "examples", "demo-repo")
        resp = self.post("/api/brief", json.dumps({"path": demo}).encode())
        rep = json.loads(resp.read())
        self.assertIn("python", rep["stack"])
        self.assertTrue(rep["tree"])

    def test_upload_scan_zipslip_rejected(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("../../evil.txt", "x")
        resp = self.post("/api/upload", buf.getvalue(),
                         headers={"X-Gatekit-Local": "1",
                                  "Content-Type": "application/zip"})
        self.assertEqual(resp.code, 400)

    def test_upload_scan_real_zip(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("app.py", "print('hi')\n")
            zf.writestr("pyproject.toml", "[project]\nname='x'\n")
        resp = self.post("/api/upload", buf.getvalue(),
                         headers={"X-Gatekit-Local": "1",
                                  "Content-Type": "application/zip"})
        data = json.loads(resp.read())
        self.assertTrue(data["ok"])
        self.assertIn("errors", data["preflight"])
        self.assertIn("python", data["brief"]["stack"])

    def test_render_workflow_fills_inputs(self):
        payload = {"workflow": "ship-check",
                   "inputs": {"CHANGE": "added login", "DIFF": "a.py"}}
        resp = self.post("/api/render", json.dumps(payload).encode())
        data = json.loads(resp.read())
        self.assertIn("# ship-check", data["prompt"])
        self.assertIn("`CHANGE`: added login", data["prompt"])
        self.assertIn("`DIFF`: a.py", data["prompt"])

    def test_render_unknown_workflow_404(self):
        resp = self.post("/api/render", json.dumps(
            {"workflow": "nope", "inputs": {}}).encode())
        self.assertEqual(resp.code, 404)

    def test_rate_roundtrip(self):
        payload = {"kind": "scan", "subject": "demo", "rating": 5,
                   "note": "caught the token"}
        resp = self.post("/api/rate", json.dumps(payload).encode())
        data = json.loads(resp.read())
        self.assertTrue(data["saved"])
        data = json.loads(self.get("/api/ratings").read())
        self.assertEqual(data["ratings"][-1]["rating"], 5)
        self.assertEqual(data["ratings"][-1]["note"], "caught the token")


    def raw_request(self, method, path, host, body=None, headers=None):
        import http.client
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=15)
        hdrs = {"Host": host}
        if headers:
            hdrs.update(headers)
        conn.request(method, path, body=body, headers=hdrs)
        resp = conn.getresponse()
        resp.read()
        conn.close()
        return resp.status

    def test_dns_rebinding_host_rejected_on_get(self):
        status = self.raw_request("GET", "/api/ratings", "evil.attacker.com")
        self.assertEqual(status, 403)

    def test_dns_rebinding_host_rejected_on_post_with_local_header(self):
        status = self.raw_request(
            "POST", "/api/scan", "evil.attacker.com",
            body=b'{"path": "."}',
            headers={"Content-Type": "application/json",
                     "X-Gatekit-Local": "1"})
        self.assertEqual(status, 403)

    def test_loopback_hosts_accepted(self):
        for host in ("127.0.0.1:%d" % self.port, "localhost:%d" % self.port,
                     "LOCALHOST", "127.0.0.1"):
            status = self.raw_request("GET", "/api/ratings", host)
            self.assertEqual(status, 200, host)

    def test_lookalike_hosts_rejected(self):
        for host in ("localhost.evil.com", "127.0.0.1.evil.com",
                     "evil127.0.0.1.com", "localhost@evil.com"):
            status = self.raw_request("GET", "/api/ratings", host)
            self.assertEqual(status, 403, host)

    def test_zipslip_rejection_leaves_no_tempdir(self):
        import glob
        before = set(glob.glob(os.path.join(tempfile.gettempdir(),
                                            "gatekit-upload-*")))
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("../../evil.txt", "x")
        resp = self.post("/api/upload", buf.getvalue(),
                         headers={"X-Gatekit-Local": "1",
                                  "Content-Type": "application/zip"})
        self.assertEqual(resp.code, 400)
        after = set(glob.glob(os.path.join(tempfile.gettempdir(),
                                           "gatekit-upload-*")))
        leaked = after - before
        for d in leaked:
            import shutil
            shutil.rmtree(d, ignore_errors=True)
        self.assertEqual(leaked, set(), "rejected zip leaked tempdirs")


    def test_corrupt_zip_entry_clean_400_and_no_leak(self):
        import glob
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as zf:
            zf.writestr("data.txt", "A" * 2000)
        raw = bytearray(buf.getvalue())
        # corrupt bytes inside the stored entry payload to break its CRC
        start = raw.find(b"AAAA")
        self.assertGreater(start, 0)
        for i in range(start, start + 100):
            raw[i] ^= 0xFF
        before = set(glob.glob(os.path.join(tempfile.gettempdir(),
                                            "gatekit-upload-*")))
        resp = self.post("/api/upload", bytes(raw),
                         headers={"X-Gatekit-Local": "1",
                                  "Content-Type": "application/zip"})
        self.assertEqual(resp.code, 400)
        body = json.loads(resp.read())
        self.assertIn("damaged", body["error"])
        after = set(glob.glob(os.path.join(tempfile.gettempdir(),
                                           "gatekit-upload-*")))
        leaked = after - before
        for d in leaked:
            import shutil
            shutil.rmtree(d, ignore_errors=True)
        self.assertEqual(leaked, set(), "corrupt zip leaked tempdirs")

    def test_rate_rejects_out_of_range(self):
        resp = self.post("/api/rate", json.dumps(
            {"kind": "scan", "subject": "x", "rating": 9}).encode())
        self.assertEqual(resp.code, 400)


if __name__ == "__main__":
    unittest.main()
