import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIEF = os.path.join(ROOT, "bin", "brief")


def run_brief(path, *extra):
    return subprocess.run([sys.executable, BRIEF, path] + list(extra),
                          capture_output=True, text=True, timeout=60)


def write(base, rel, content):
    path = os.path.join(base, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)


class BriefTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def test_markdown_sections_present(self):
        write(self.dir, "app.py", "print('hi')\n")
        write(self.dir, "pyproject.toml", "[project]\nname='x'\n")
        proc = run_brief(self.dir)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        for section in ["# Repo brief:", "## Stack", "## Layout",
                        "## Checks that prove this repo works",
                        "## Working agreement"]:
            self.assertIn(section, proc.stdout)
        self.assertIn("python", proc.stdout)
        self.assertIn("python3 -m pytest", proc.stdout)

    def test_node_scripts_in_brief(self):
        write(self.dir, "package.json",
              '{"name": "demo", "scripts": {"test": "jest", "build": "tsc"}}')
        write(self.dir, "src/index.js", "export {};\n")
        proc = run_brief(self.dir)
        self.assertIn("node", proc.stdout)
        self.assertIn("name: demo", proc.stdout)
        self.assertIn("npm test", proc.stdout)
        self.assertIn("npm run build", proc.stdout)
        self.assertIn("src/", proc.stdout)

    def test_skip_dirs_excluded_from_layout(self):
        write(self.dir, "node_modules/pkg/x.js", "x=1;\n")
        write(self.dir, "index.js", "x=1;\n")
        proc = run_brief(self.dir)
        self.assertNotIn("node_modules", proc.stdout)
        self.assertIn("index.js", proc.stdout)

    def test_json_output_shape(self):
        write(self.dir, "go.mod", "module example.com/x\n")
        proc = run_brief(self.dir, "--json")
        data = json.loads(proc.stdout)
        self.assertEqual(data["stack"], ["go"])
        self.assertIn("go test ./...", data["suggested_checks"])
        self.assertTrue(data["tree"])

    def test_git_info_when_repo(self):
        write(self.dir, "a.py", "x=1\n")
        subprocess.run(["git", "init", "-q"], cwd=self.dir, check=True)
        subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                        "add", "-A"], cwd=self.dir, check=True)
        subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                        "commit", "-qm", "init"], cwd=self.dir, check=True)
        proc = run_brief(self.dir, "--json")
        data = json.loads(proc.stdout)
        self.assertIn(data["git"]["branch"], ("master", "main"))
        self.assertEqual(data["git"]["commits"], "1")


    def test_python_unittest_fallback_when_no_pytest(self):
        import importlib.util
        if importlib.util.find_spec("pytest") is not None:
            self.skipTest("pytest installed here; fallback path not active")
        write(self.dir, "pyproject.toml", "[project]\nname='x'\n")
        write(self.dir, "tests/test_x.py", "import unittest\n")
        proc = run_brief(self.dir, "--json")
        data = json.loads(proc.stdout)
        self.assertIn("python3 -m unittest discover -s tests",
                      data["suggested_checks"])


    def test_tree_indentation_reflects_structure(self):
        write(self.dir, "app.py", "x=1\n")
        write(self.dir, "src/mod.py", "x=1\n")
        proc = run_brief(self.dir, "--json")
        tree = json.loads(proc.stdout)["tree"]
        root_file = [l for l in tree if l.endswith("app.py")][0]
        subdir = [l for l in tree if l.rstrip("/").endswith("src")][0]
        child = [l for l in tree if l.endswith("mod.py")][0]
        # child must be indented deeper than its directory
        self.assertGreater(len(child) - len(child.lstrip()),
                           len(subdir) - len(subdir.lstrip()))
        # a root file and a first-level dir share the top indent level
        self.assertEqual(len(root_file) - len(root_file.lstrip()),
                         len(subdir) - len(subdir.lstrip()))

    def test_missing_directory_is_usage_error(self):
        proc = run_brief(os.path.join(self.dir, "nope"))
        self.assertEqual(proc.returncode, 2)


if __name__ == "__main__":
    unittest.main()
