import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREFLIGHT = os.path.join(ROOT, "bin", "preflight")


def run_preflight(path, *extra):
    return subprocess.run(
        [sys.executable, PREFLIGHT, path, "--json"] + list(extra),
        capture_output=True, text=True, timeout=120)


def write(base, rel, content):
    path = os.path.join(base, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)


class PreflightScanTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def report(self, *extra):
        proc = run_preflight(self.dir, *extra)
        self.assertEqual(proc.stderr.strip(), "", msg=proc.stderr)
        return proc, json.loads(proc.stdout)

    def test_clean_python_project_is_clear(self):
        write(self.dir, "app.py", "def add(a, b):\n    return a + b\n")
        write(self.dir, "pyproject.toml", "[project]\nname = 'demo'\n")
        proc, rep = self.report()
        self.assertEqual(proc.returncode, 0)
        self.assertTrue(rep["ok"])
        self.assertEqual(rep["errors"], [])
        self.assertIn("python", rep["project"])
        self.assertIn("python3 -m pytest", rep["suggested_checks"])

    def test_aws_key_is_blocking_error(self):
        fake_aws = "AKIA" + "IOSFODNN7" + "EXAMPLE"  # built at runtime
        write(self.dir, "config.py", "AWS_KEY = '%s'\n" % fake_aws)
        proc, rep = self.report()
        self.assertEqual(proc.returncode, 1)
        self.assertFalse(rep["ok"])
        self.assertEqual(rep["errors"][0]["pattern"], "AWS access key id")
        self.assertEqual(rep["errors"][0]["file"], "config.py")

    def test_private_key_block_detected(self):
        key_block = "-----BEGIN " + "RSA PRIVATE " + "KEY-----"
        write(self.dir, "deploy.sh", "KEY='%s\nblah'\n" % key_block)
        proc, rep = self.report()
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(rep["errors"][0]["pattern"], "private key block")

    def test_env_reference_is_not_flagged(self):
        write(self.dir, "settings.py",
              "import os\nAPI_KEY = os.environ['API_KEY']\n")
        proc, rep = self.report()
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(rep["errors"], [])
        self.assertEqual(rep["warnings"], [])

    def test_placeholder_value_is_not_flagged(self):
        write(self.dir, "settings.py",
              "API_KEY = 'your-api-key-here'\n")
        proc, rep = self.report()
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(rep["warnings"], [])

    def test_generic_credential_assignment_warns(self):
        fake_key = "k9f2m4x7" + "q1w8e5r3" + "t6y9"
        write(self.dir, "settings.py", "API_KEY = '%s'\n" % fake_key)
        proc, rep = self.report()
        self.assertEqual(proc.returncode, 0)
        kinds = [w["kind"] for w in rep["warnings"]]
        self.assertIn("possible-credential", kinds)

    def test_strict_mode_fails_on_warnings(self):
        fake_key = "k9f2m4x7" + "q1w8e5r3" + "t6y9"
        write(self.dir, "settings.py", "API_KEY = '%s'\n" % fake_key)
        proc, rep = self.report("--strict")
        self.assertEqual(proc.returncode, 1)
        self.assertFalse(rep["ok"])

    def test_console_log_warns(self):
        write(self.dir, "index.js",
              "function main() {\n  console.log('debug');\n}\n")
        proc, rep = self.report()
        self.assertEqual(proc.returncode, 0)
        kinds = [w["kind"] for w in rep["warnings"]]
        self.assertIn("debug-residue", kinds)

    def test_pdb_warns(self):
        write(self.dir, "app.py", "import pdb\npdb.set_trace()\n")
        proc, rep = self.report()
        kinds = [w["kind"] for w in rep["warnings"]]
        self.assertIn("debug-residue", kinds)

    def test_todo_counted_as_note(self):
        write(self.dir, "app.py", "# TODO: clean this up\ndef f():\n    pass\n")
        proc, rep = self.report()
        self.assertEqual(rep["todo_fixme_total"], 1)
        self.assertEqual(proc.returncode, 0)

    def test_skip_dirs_are_ignored(self):
        write(self.dir, "node_modules/pkg/index.js",
              "console.log('vendored');\n")
        write(self.dir, "src/index.js", "export const x = 1;\n")
        proc, rep = self.report()
        self.assertEqual(rep["warnings"], [])

    def test_node_scripts_detected(self):
        write(self.dir, "package.json",
              '{"scripts": {"test": "jest", "build": "tsc"}}')
        proc, rep = self.report()
        self.assertIn("node", rep["project"])
        self.assertIn("npm test", rep["suggested_checks"])
        self.assertIn("npm run build", rep["suggested_checks"])

    def test_custom_checks_file_wins_and_runs(self):
        write(self.dir, "preflight.checks",
              "# my checks\nexit 0\n")
        proc, rep = self.report("--run-checks")
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(rep["checks_run"][0]["command"], "exit 0")
        self.assertTrue(rep["checks_run"][0]["passed"])

    def test_failing_custom_check_blocks(self):
        write(self.dir, "preflight.checks", "exit 3\n")
        proc, rep = self.report("--run-checks")
        self.assertEqual(proc.returncode, 1)
        self.assertFalse(rep["ok"])
        self.assertEqual(rep["errors"][0]["kind"], "check-failed")

    def test_non_git_directory_still_scans(self):
        write(self.dir, "app.py", "print('hello')\n")
        proc, rep = self.report()
        self.assertEqual(proc.returncode, 0)
        self.assertFalse(rep["git"]["is_repo"])

    def test_preflightignore_skips_matching_files(self):
        fake_aws = "AKIA" + "IOSFODNN7" + "EXAMPLE"
        write(self.dir, "fixtures/old.py", "K = '%s'\n" % fake_aws)
        write(self.dir, ".preflightignore", "fixtures/*\n")
        proc, rep = self.report()
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(rep["errors"], [])

    def test_symlink_outside_root_is_not_followed(self):
        outside = os.path.join(self.dir, "..", "outside-%d" % os.getpid())
        os.makedirs(outside, exist_ok=True)
        try:
            fake_aws = "AKIA" + "IOSFODNN7" + "EXAMPLE"
            write(outside, "secret.py", "K = '%s'\n" % fake_aws)
            link = os.path.join(self.dir, "linked.py")
            os.symlink(os.path.join(outside, "secret.py"), link)
            proc, rep = self.report()
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(rep["errors"], [])
        finally:
            import shutil
            shutil.rmtree(outside, ignore_errors=True)

    def init_git(self):
        subprocess.run(["git", "init", "-q"], cwd=self.dir, check=True)
        subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                        "add", "-A"], cwd=self.dir, check=True)

    def test_tracked_env_is_blocking_error(self):
        write(self.dir, ".env", "TOKEN=abc123def456ghi789\n")
        self.init_git()
        proc, rep = self.report()
        self.assertEqual(proc.returncode, 1)
        kinds = [e["kind"] for e in rep["errors"]]
        self.assertIn("env-tracked", kinds)

    def test_untracked_env_warns_when_not_ignored(self):
        write(self.dir, ".env", "TOKEN=abc123def456ghi789\n")
        self.init_git()
        subprocess.run(["git", "-C", self.dir, "rm", "--cached", "-q", ".env"],
                       check=True)
        proc, rep = self.report()
        kinds = [w["kind"] for w in rep["warnings"]]
        self.assertIn("env-not-ignored", kinds)
        self.assertNotIn("env-tracked", [e["kind"] for e in rep["errors"]])

    def test_ignored_env_is_quiet(self):
        write(self.dir, ".env", "TOKEN=abc123def456ghi789\n")
        write(self.dir, ".gitignore", ".env\n")
        self.init_git()
        proc, rep = self.report()
        kinds = [w["kind"] for w in rep["warnings"]]
        self.assertNotIn("env-not-ignored", kinds)
        self.assertNotIn("env-tracked", [e["kind"] for e in rep["errors"]])

    def test_custom_checks_replace_auto_detection(self):
        write(self.dir, "package.json",
              '{"scripts": {"test": "jest"}}')
        write(self.dir, "preflight.checks", "exit 0\n")
        proc, rep = self.report()
        self.assertEqual(rep["suggested_checks"], ["exit 0"])
        self.assertNotIn("npm test", rep["suggested_checks"])


    def test_python_unittest_fallback_when_no_pytest(self):
        import importlib.util
        if importlib.util.find_spec("pytest") is not None:
            self.skipTest("pytest installed here; fallback path not active")
        write(self.dir, "pyproject.toml", "[project]\nname='x'\n")
        write(self.dir, "tests/test_x.py", "import unittest\n")
        proc, rep = self.report()
        self.assertIn("python3 -m unittest discover -s tests",
                      rep["suggested_checks"])

    def test_python_pytest_suggested_without_tests_dir(self):
        write(self.dir, "pyproject.toml", "[project]\nname='x'\n")
        proc, rep = self.report()
        self.assertIn("python3 -m pytest", rep["suggested_checks"])


    def test_unittest_repo_runs_green_without_pytest(self):
        import importlib.util
        if importlib.util.find_spec("pytest") is not None:
            self.skipTest("pytest installed here; fallback path not active")
        write(self.dir, "pyproject.toml", "[project]\nname='x'\n")
        write(self.dir, "tests/test_x.py",
              "import unittest\n\nclass T(unittest.TestCase):\n"
              "    def test_ok(self):\n        self.assertTrue(True)\n")
        proc, rep = self.report("--run-checks")
        self.assertIn("python3 -m unittest discover -s tests",
                      rep["suggested_checks"])
        self.assertTrue(rep["ok"], rep)
        self.assertTrue(rep["checks_run"][0]["passed"])

    def test_conftest_signals_pytest(self):
        write(self.dir, "pyproject.toml", "[project]\nname='x'\n")
        write(self.dir, "conftest.py", "")
        proc, rep = self.report()
        self.assertIn("python3 -m pytest", rep["suggested_checks"])

    def test_oversize_file_reported_not_silently_skipped(self):
        big = "x\n" * (3 * 1024 * 1024 // 2)  # ~3 MB
        write(self.dir, "big.py", big + "AWS_KEY = 'AKIA" + "I" * 16 + "'\n")
        proc, rep = self.report()
        self.assertIn("big.py", rep["skipped_oversize"])
        self.assertEqual(rep["errors"], [])  # secret missed, but disclosed
        self.assertIn("oversize", proc.stdout if proc.stdout else "")

    def test_missing_directory_is_usage_error(self):
        proc = run_preflight(os.path.join(self.dir, "nope"))
        self.assertEqual(proc.returncode, 2)


if __name__ == "__main__":
    unittest.main()
