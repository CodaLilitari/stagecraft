"""Offline synthetic checks: python -B -m unittest -v test_check_updates.py"""
import copy
from http.client import BadStatusLine
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError
from urllib.request import Request

import check_updates as checker


def release(version="1.0.1"):
    return {"schema_version": 1, "name": "Stagecraft", "version": version,
            "artifact": {"url": "https://gitlab.com/codalilitari/stagecraft/-/releases/v1.0.1/downloads/stagecraft.zip",
                         "sha256": "AB" * 32, "bytes": 12345}}


class FakeResponse:
    def __init__(self, url, payload, headers=None, status=200):
        self.url, self.payload, self.status = url, payload, status
        self.headers = headers or {}
        self.read_sizes = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def geturl(self):
        return self.url

    def read(self, size):
        self.read_sizes.append(size)
        return self.payload[:size]


class FakeOpener:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def open(self, request, timeout):
        self.calls.append((request, timeout))
        result = self.responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


class ReleaseCheckerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.version_file = self.root / "skill-version.json"
        self.version_file.write_text(json.dumps({"schema_version": 1, "name": "Stagecraft", "version": "1.0.0"}))
        self.manifest = self.root / "release.json"

    def check(self, **kwargs):
        return checker.run_check(version_file=self.version_file, **kwargs)

    def response(self, url=None, data=None, **kwargs):
        return FakeResponse(url or checker.DEFAULT_FEEDS[0], json.dumps(data or release()).encode(), **kwargs)

    def test_offline_comparison_and_no_artifact_verification_claim(self):
        for remote, status in (("1.0.0", "up_to_date"), ("1.0.1", "update_available"),
                               ("0.9.9", "local_newer"), ("1.10.0", "update_available")):
            with self.subTest(version=remote):
                self.manifest.write_text(json.dumps(release(remote)))
                before = {p: p.read_bytes() for p in self.root.iterdir()}
                with patch.object(checker, "public_opener", side_effect=AssertionError("No offline network")):
                    report, code = self.check(manifest=self.manifest)
                self.assertEqual(code, 0)
                self.assertEqual(report["status"], status)
                self.assertTrue(report["verified_schema"])
                self.assertEqual(report["release_feed_status"], "available")
                self.assertEqual(report["artifact_status"], "not_downloaded")
                self.assertEqual(report["artifact_hash_status"], "not_verified")
                self.assertEqual(report["artifact_availability"], "not_checked")
                self.assertEqual(report["remote"]["artifact"]["sha256"], "ab" * 32)
                self.assertEqual(before, {p: p.read_bytes() for p in self.root.iterdir()})

    def test_default_404_falls_back_to_portfolio_and_only_fetches_metadata(self):
        primary, backup = checker.DEFAULT_FEEDS
        response = self.response(backup)
        opener = FakeOpener([HTTPError(primary, 404, "Not Found", {}, None), response])
        report, code = self.check(opener=opener)
        self.assertEqual(code, 0)
        self.assertEqual([call[0].full_url for call in opener.calls], [primary, backup])
        self.assertEqual(report["source"], backup)
        self.assertEqual(report["attempts"][0]["error"], "HTTP 404")
        self.assertEqual(response.read_sizes, [checker.MAX_BYTES + 1])
        for request, timeout in opener.calls:
            self.assertEqual(timeout, 10.0)
            self.assertEqual(request.get_method(), "GET")
            self.assertEqual({k.lower() for k, _ in request.header_items()}, {"accept", "user-agent"})

    def test_invalid_primary_json_falls_back_and_explicit_feed_does_not(self):
        custom = "https://example.org/release.json"
        bad = FakeResponse(checker.DEFAULT_FEEDS[0], b"<html>not JSON</html>")
        opener = FakeOpener([bad, self.response(checker.DEFAULT_FEEDS[1])])
        self.assertEqual(self.check(opener=opener)[1], 0)
        self.assertEqual(len(opener.calls), 2)
        opener = FakeOpener([FakeResponse(custom, b"not JSON")])
        report, code = self.check(feed=custom, opener=opener)
        self.assertEqual(code, 1)
        self.assertFalse(report["verified_schema"])
        self.assertEqual(len(opener.calls), 1)

    def test_missing_or_invalid_local_metadata_prevents_network(self):
        cases = (None, b"not JSON", b'{"schema_version":1,"name":"Other","version":"1.0.0"}',
                 b'{"schema_version":1,"name":"Stagecraft","version":"01.0.0"}')
        for payload in cases:
            with self.subTest(payload=payload):
                self.version_file.unlink(missing_ok=True)
                if payload is not None:
                    self.version_file.write_bytes(payload)
                opener = FakeOpener([])
                report, code = self.check(opener=opener)
                self.assertEqual(code, 2)
                self.assertEqual(report["status"], "invalid_local_configuration")
                self.assertEqual(opener.calls, [])

    def test_missing_local_release_and_failed_network_return_unavailable(self):
        report, code = self.check(manifest=self.manifest)
        self.assertEqual(code, 1)
        self.assertEqual(report["status"], "unavailable")
        opener = FakeOpener([TimeoutError(), OSError("private operating-system details")])
        report, code = self.check(opener=opener)
        self.assertEqual(code, 1)
        self.assertEqual(len(report["attempts"]), 2)
        self.assertNotIn("private", json.dumps(report))

    def test_duplicate_nonfinite_nonobject_and_non_json_feeds_rejected(self):
        original = json.dumps(release())
        cases = (
            original.replace('"version": "1.0.1"', '"version": "9.0.0", "version": "1.0.1"'),
            original.replace('"bytes": 12345', '"by\\u0074es": 1, "bytes": 12345'),
            original[:-1] + ', "notes": {"x": 1, "x": 2}}',
            original[:-1] + ', "notes": NaN}', original[:-1] + ', "notes": 1e10000}',
            '[]', '<html>unavailable</html>', '\ufeffnot JSON',
            '{"deep":' + '[' * 2000 + '0' + ']' * 2000 + '}',
        )
        for text in cases:
            with self.subTest(text=text[:80]):
                self.manifest.write_text(text, encoding="utf-8")
                report, code = self.check(manifest=self.manifest)
                self.assertEqual(code, 1)
                self.assertFalse(report["verified_schema"])
                self.assertIsNone(report["remote"])

    def test_schema_artifact_and_canonical_version_validation(self):
        mutations = [
            lambda d: d.update(schema_version=True), lambda d: d.update(schema_version=2),
            lambda d: d.update(name="stagecraft"), lambda d: d.pop("artifact"),
            lambda d: d["artifact"].update(sha256="a" * 63), lambda d: d["artifact"].update(sha256="g" * 64),
            lambda d: d["artifact"].update(bytes=True), lambda d: d["artifact"].update(bytes=0),
            lambda d: d["artifact"].update(bytes=1.0), lambda d: d["artifact"].update(bytes="100"),
            lambda d: d["artifact"].update(url="file:///tmp/archive.zip"),
        ]
        for version in ("1.0", "v1.0.0", "01.0.0", "1.0.0-rc1", "1.0.0+build", "1.0.0 ", "1.0.٠", 1, None):
            mutations.append(lambda d, v=version: d.update(version=v))
        for index, mutation in enumerate(mutations):
            with self.subTest(case=index):
                data = copy.deepcopy(release())
                mutation(data)
                with self.assertRaises(checker.ReleaseError):
                    checker.validate_metadata(data, release=True)

    def test_response_and_local_reads_are_bounded(self):
        oversized = b" " * (checker.MAX_BYTES + 1)
        self.manifest.write_bytes(oversized)
        self.assertEqual(self.check(manifest=self.manifest)[1], 1)
        for headers, payload in (({}, oversized), ({"Content-Length": str(checker.MAX_BYTES + 1)}, b"{}"),
                                 ({"Content-Length": "-1"}, b"{}"), ({"Content-Length": "9" * 100}, b"{}")):
            with self.subTest(headers=headers):
                response = FakeResponse(checker.DEFAULT_FEEDS[0], payload, headers)
                report, code = self.check(feed=checker.DEFAULT_FEEDS[0], opener=FakeOpener([response]))
                self.assertEqual(code, 1)
                self.assertFalse(report["verified_schema"])
                self.assertTrue(not response.read_sizes or response.read_sizes == [checker.MAX_BYTES + 1])

    def test_unsafe_urls_refused_without_credentials_in_report(self):
        urls = ("http://gitlab.com/release.json", "file:///release.json", "https://user:secret@gitlab.com/r",
                "https://gitlab.com:8443/r", "https://gitlab.com/r#fragment", "https://gitlab.com/\nr",
                "https://gitlab.com/%0dr", "https://gitlab.com\\@example.org/r", "https://gitlab.com/%zz",
                "https://gitlab.com/%5cr", "https://gitlab.com./r")
        for url in urls:
            with self.subTest(url=url):
                opener = FakeOpener([])
                report, code = self.check(feed=url, opener=opener)
                self.assertEqual(code, 2)
                self.assertEqual(opener.calls, [])
                self.assertNotIn("secret", json.dumps(report))

    def test_redirects_are_bounded_and_strip_credentials(self):
        handler = checker.SafeRedirectHandler()
        request = Request(checker.DEFAULT_FEEDS[0], headers={"Authorization": "secret", "Cookie": "private"})
        for destination in ("https://gitlab.com/next.json", checker.DEFAULT_FEEDS[1]):
            with self.subTest(destination=destination):
                redirected = handler.redirect_request(request, None, 302, "Found", {}, destination)
                self.assertEqual(redirected.full_url, destination)
                self.assertEqual({k.lower() for k, _ in redirected.header_items()}, {"accept", "user-agent"})
        for destination in ("https://evil.example/release.json", "http://gitlab.com/release.json",
                            "https://user:secret@gitlab.com/release.json", "file:///release.json"):
            with self.subTest(destination=destination), self.assertRaises(checker.ReleaseError):
                handler.redirect_request(request, None, 302, "Found", {}, destination)
        self.assertEqual(handler.max_redirections, 5)
        self.assertEqual(handler.max_repeats, 2)
        custom = Request("https://releases.example.org/release.json")
        self.assertEqual(handler.redirect_request(custom, None, 302, "Found", {},
                                                 "https://releases.example.org/next.json").full_url,
                         "https://releases.example.org/next.json")

    def test_artifact_url_can_use_an_independent_https_host_without_fetching_it(self):
        data = release()
        data["artifact"]["url"] = "https://downloads.example.org/stagecraft-1.0.1.zip"
        opener = FakeOpener([self.response(data=data)])
        report, code = self.check(opener=opener)
        self.assertEqual(code, 0)
        self.assertEqual(report["remote"]["artifact"]["url"], data["artifact"]["url"])
        self.assertEqual([call[0].full_url for call in opener.calls], [checker.DEFAULT_FEEDS[0]])

    def test_redirect_body_is_closed_without_unbounded_drain(self):
        handler = checker.SafeRedirectHandler()
        final_response = self.response(checker.DEFAULT_FEEDS[1])
        opener = FakeOpener([final_response])
        handler.add_parent(opener)
        request = Request(checker.DEFAULT_FEEDS[0])
        request.timeout = 10
        redirect_body = Mock()
        redirect_body.read.side_effect = AssertionError("Redirect bodies must not be drained")
        result = handler.http_error_302(request, redirect_body, 302, "Found",
                                        {"location": checker.DEFAULT_FEEDS[1]})
        self.assertIs(result, final_response)
        redirect_body.close.assert_called_once_with()
        redirect_body.read.assert_not_called()

    def test_malformed_http_response_is_reported_without_server_text(self):
        report, code = self.check(feed=checker.DEFAULT_FEEDS[0],
                                  opener=FakeOpener([BadStatusLine("untrusted server text")]))
        self.assertEqual(code, 1)
        self.assertNotIn("untrusted server text", json.dumps(report))

    def test_unapproved_final_response_and_redirect_refusal_reported(self):
        for item in (self.response("https://evil.example/release.json"),
                     checker.ReleaseError("Redirect to an unapproved host refused")):
            with self.subTest(item=type(item).__name__):
                report, code = self.check(feed=checker.DEFAULT_FEEDS[0], opener=FakeOpener([item]))
                self.assertEqual(code, 1)
                self.assertFalse(report["verified_schema"])

    def test_timeout_and_source_conflicts_prevent_network(self):
        for timeout in (0, -1, 31, float("inf"), float("nan"), True):
            with self.subTest(timeout=timeout):
                opener = FakeOpener([])
                self.assertEqual(self.check(timeout=timeout, opener=opener)[1], 2)
                self.assertEqual(opener.calls, [])
        self.assertEqual(self.check(feed=checker.DEFAULT_FEEDS[0], manifest=self.manifest)[1], 2)

    def test_cli_prints_json_report_only(self):
        expected = {"status": "up_to_date", "artifact_hash_status": "not_verified"}
        output = io.StringIO()
        with patch.object(checker, "run_check", return_value=(expected, 0)) as run, patch("sys.stdout", output):
            self.assertEqual(checker.main(["--manifest", str(self.manifest)]), 0)
        self.assertEqual(json.loads(output.getvalue()), expected)
        self.assertEqual(run.call_args.kwargs["manifest"], self.manifest)


if __name__ == "__main__":
    unittest.main()
