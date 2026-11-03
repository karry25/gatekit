import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKFLOWS = os.path.join(ROOT, "workflows")

REQUIRED_SECTIONS = ["## Purpose", "## Inputs", "## Procedure",
                     "## Evidence", "## Stop conditions"]


class WorkflowFormatTests(unittest.TestCase):
    def files(self):
        names = [n for n in os.listdir(WORKFLOWS) if n.endswith(".md")]
        self.assertGreaterEqual(len(names), 5,
                                "expected at least 5 workflows")
        return names

    def test_every_workflow_has_required_sections(self):
        for name in self.files():
            with open(os.path.join(WORKFLOWS, name), encoding="utf-8") as f:
                text = f.read()
            for section in REQUIRED_SECTIONS:
                self.assertIn(section, text,
                              "%s missing %s" % (name, section))

    def test_every_workflow_has_h1_title_matching_filename(self):
        for name in self.files():
            with open(os.path.join(WORKFLOWS, name), encoding="utf-8") as f:
                first = f.readline().strip()
            self.assertEqual(first, "# " + name[:-3],
                             "%s title mismatch" % name)

    def test_procedure_is_numbered(self):
        for name in self.files():
            with open(os.path.join(WORKFLOWS, name), encoding="utf-8") as f:
                text = f.read()
            proc = text.split("## Procedure", 1)[1].split("## Evidence", 1)[0]
            steps = re.findall(r"^\d+\.\s", proc, re.M)
            self.assertGreaterEqual(len(steps), 3,
                                    "%s procedure needs numbered steps" % name)

    def test_stop_conditions_are_bulleted(self):
        for name in self.files():
            with open(os.path.join(WORKFLOWS, name), encoding="utf-8") as f:
                text = f.read()
            stop = text.split("## Stop conditions", 1)[1]
            stops = re.findall(r"^[-*]\s", stop, re.M)
            self.assertGreaterEqual(len(stops), 2,
                                    "%s needs real stop conditions" % name)


if __name__ == "__main__":
    unittest.main()
