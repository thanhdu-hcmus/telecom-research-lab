"""Checks for M0 evidence integrity, without network or LLM use."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

FILE = Path(__file__).resolve().parents[2] / "scripts" / "probe_environment.py"
SPEC = importlib.util.spec_from_file_location("probe_environment", FILE)
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)


class ProbeEvidenceTests(unittest.TestCase):
    def test_failure_exit_is_preserved(self):
        result = probe.command([sys.executable, "-c", "print('sentinel'); raise SystemExit(7)"])
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["exit_code"], 7)
        self.assertIn("sentinel", result["stdout"])

    def test_missing_tool_is_explicit(self):
        with patch.object(probe, "executable", return_value=None):
            self.assertEqual(probe.tool("not_installed", ["--version"])["status"], "MISSING")

    def test_timeout_is_failure(self):
        with patch.object(probe.subprocess, "run", side_effect=subprocess.TimeoutExpired(["fake"], 1)):
            self.assertEqual(probe.command(["fake"], timeout=1)["reason"], "timeout")

    def test_auth_tokens_and_license_are_redacted(self):
        sample = "  - Token: gho_012345678901234567890\nMATLAB License Number: 123456\nversion 1\n"
        cleaned = probe.redact(sample)
        self.assertNotIn("012345678901234567890", cleaned)
        self.assertNotIn("123456", cleaned)
        self.assertIn("version 1", cleaned)

    def test_reachability_does_not_accept_malformed_payload(self):
        class Response:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, size): return b'{"results": []}'
        with patch.object(probe.urllib.request, "urlopen", return_value=Response()):
            self.assertEqual(probe.network_check("openalex", "https://api.openalex.org/works")["status"], "FAIL")

    def test_plain_xml_is_not_arxiv_success(self):
        class Response:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, size): return b"<html>error page</html>"
        with patch.object(probe.urllib.request, "urlopen", return_value=Response()):
            self.assertEqual(probe.network_check("arxiv", "https://export.arxiv.org/api/query")["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
