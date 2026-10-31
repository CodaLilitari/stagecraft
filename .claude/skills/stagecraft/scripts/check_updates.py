"""Read Stagecraft release metadata; never download, install, or execute an artifact.

Red's fork note: the fork's skill-version.json records the upstream Stagecraft
version it was built from. "update_available" therefore means Coda published a
newer upstream release whose findings may be worth folding into Red's fork by
hand; this checker never installs or overwrites anything.

Only public unauthenticated HTTPS feed requests are made. No account lookup,
cookie jar, environment proxy, paid API, installation, or archive extraction is
used. --manifest reads one explicit local release manifest without networking.
"""
from __future__ import annotations

import argparse
from http.client import HTTPException
from io import BytesIO
import json
import math
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


MAX_BYTES = 1024 * 1024
DEFAULT_TIMEOUT = 10.0
VERSION_FILE = Path(__file__).resolve().parent.parent / "skill-version.json"
DEFAULT_FEEDS = (
    "https://gitlab.com/codalilitari/stagecraft/-/raw/main/release.json",
    "https://richard-pemberton-research.darkahn.chatgpt.site/projects/stagecraft/release.json",
)
KNOWN_HOSTS = frozenset(urlsplit(url).hostname for url in DEFAULT_FEEDS)
HEADERS = {"Accept": "application/json", "User-Agent": "Stagecraft-release-checker/1"}


class ReleaseError(ValueError):
    """Rejected input or feed, with a short diagnostic safe to include in a report."""


def safe_https_url(value):
    """Require a plain HTTPS URL without credentials, fragments, or unusual ports."""
    if not isinstance(value, str) or not value or len(value) > 4096 or not value.isascii():
        raise ReleaseError("Expected an ASCII HTTPS URL of at most 4096 characters")
    if re.search(r"[\x00-\x20\x7f\\]", value) or re.search(r"%(?![0-9a-fA-F]{2})", value):
        raise ReleaseError("URL contains whitespace, control characters, backslashes, or invalid escapes")
    if re.search(r"[\x00-\x1f\x7f\\]", unquote(value)):
        raise ReleaseError("URL contains encoded control characters or backslashes")
    try:
        parts = urlsplit(value)
        port = parts.port
    except ValueError as error:
        raise ReleaseError("Malformed HTTPS URL") from error
    if parts.scheme != "https" or not parts.hostname or parts.username is not None or parts.password is not None:
        raise ReleaseError("URL must use HTTPS with a host and no embedded credentials")
    if parts.fragment or port not in (None, 443):
        raise ReleaseError("URL fragments and nonstandard HTTPS ports are forbidden")
    host = parts.hostname
    if len(host) > 253 or any(not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?", label)
                              for label in host.split(".")):
        raise ReleaseError("Expected an ordinary DNS host name")
    return value


def version_key(value):
    """Canonical three-part versions only; compare without unbounded integer parsing."""
    if not isinstance(value, str) or not re.fullmatch(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)", value):
        raise ReleaseError("Version must contain exactly three canonical decimal numbers, e.g. 1.0.0")
    return tuple((len(part), part) for part in value.split("."))


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ReleaseError("Duplicate JSON object member")
        result[key] = value
    return result


def decode_json(payload):
    if len(payload) > MAX_BYTES:
        raise ReleaseError("Release metadata exceeds the 1 MiB limit")
    def reject_constant(value):
        raise ReleaseError("Non-finite JSON number")
    def finite_float(value):
        number = float(value)
        if not math.isfinite(number):
            reject_constant(value)
        return number
    try:
        value = json.loads(payload.decode("utf-8-sig"), object_pairs_hook=unique_object,
                           parse_constant=reject_constant, parse_float=finite_float)
    except (UnicodeError, ValueError, RecursionError) as error:
        if isinstance(error, ReleaseError):
            raise
        raise ReleaseError("Metadata must be valid UTF-8 JSON") from error
    if not isinstance(value, dict):
        raise ReleaseError("Metadata must be a JSON object")
    return value


def validate_metadata(data, *, release):
    if type(data.get("schema_version")) is not int or data["schema_version"] != 1:
        raise ReleaseError("Expected integer schema_version 1")
    if data.get("name") != "Stagecraft":
        raise ReleaseError("Expected release name Stagecraft")
    version_key(data.get("version"))
    result = {"schema_version": 1, "name": "Stagecraft", "version": data["version"]}
    if release:
        artifact = data.get("artifact")
        if not isinstance(artifact, dict):
            raise ReleaseError("Expected artifact object")
        url = safe_https_url(artifact.get("url"))
        digest = artifact.get("sha256")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
            raise ReleaseError("Expected artifact SHA-256 as 64 hexadecimal characters")
        size = artifact.get("bytes")
        if type(size) is not int or size <= 0:
            raise ReleaseError("Expected positive integer artifact bytes")
        result["artifact"] = {"url": url, "sha256": digest.lower(), "bytes": size}
    return result


def read_local(path):
    with Path(path).open("rb") as source:
        return decode_json(source.read(MAX_BYTES + 1))


class SafeRedirectHandler(HTTPRedirectHandler):
    max_redirections = 5
    max_repeats = 2

    def http_error_302(self, req, fp, code, msg, headers):
        # urllib otherwise drains an unlimited redirect body before following it.
        # Close that response and let its redirect logic consume only an empty body.
        fp.close()
        with BytesIO() as empty_body:
            return super().http_error_302(req, empty_body, code, msg, headers)

    http_error_301 = http_error_303 = http_error_307 = http_error_308 = http_error_302

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        safe_https_url(newurl)
        old_host = urlsplit(req.full_url).hostname
        new_host = urlsplit(newurl).hostname
        if new_host != old_host and new_host not in KNOWN_HOSTS:
            raise ReleaseError("Redirect to an unapproved host refused")
        if req.get_method() != "GET" or code not in (301, 302, 303, 307, 308):
            raise ReleaseError("Unexpected redirect method or status")
        # Rebuild with only fixed public headers; never forward cookies or auth.
        return Request(newurl, headers=HEADERS, method="GET")


def public_opener(use_env_proxy=False):
    # Default: disable environment proxy inheritance. Hosts whose only route out is
    # an egress proxy (some Claude shells) can opt in with --env-proxy.
    # No cookie or authentication handler either way.
    proxies = ProxyHandler() if use_env_proxy else ProxyHandler({})
    return build_opener(proxies, SafeRedirectHandler())


def fetch_release(url, *, timeout, opener):
    safe_https_url(url)
    request = Request(url, headers=HEADERS, method="GET")
    with opener.open(request, timeout=timeout) as response:
        final_url = safe_https_url(response.geturl())
        if urlsplit(final_url).hostname != urlsplit(url).hostname and urlsplit(final_url).hostname not in KNOWN_HOSTS:
            raise ReleaseError("Response from an unapproved host refused")
        if response.status != 200:
            raise ReleaseError("Expected HTTP status 200")
        length = response.headers.get("Content-Length")
        if length is not None and (not re.fullmatch(r"[0-9]+", length) or len(length) > 10 or int(length) > MAX_BYTES):
            raise ReleaseError("Invalid or oversized Content-Length")
        payload = response.read(MAX_BYTES + 1)
    # GitLab raw feeds may be text/plain. Parse the bytes, never trust the MIME label.
    return validate_metadata(decode_json(payload), release=True), final_url


def run_check(*, version_file=VERSION_FILE, feed=None, manifest=None, timeout=DEFAULT_TIMEOUT, opener=None, use_env_proxy=False):
    report = {
        "name": "Stagecraft", "status": "unavailable", "current": None, "remote": None,
        "attempts": [], "release_feed_status": "unavailable", "verified_schema": False,
        "artifact_availability": "not_checked", "artifact_status": "not_downloaded",
        "artifact_hash_status": "not_verified",
        "activity": {"mode": "offline" if manifest is not None else "public_https_metadata_only",
                     "authentication": "none", "implicit_account_calls": False, "paid_api_calls": False,
                     "install_performed": False, "execution_performed": False, "archive_extracted": False},
    }
    try:
        if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 30:
            raise ReleaseError("Timeout must be finite and greater than zero, at most 30 seconds")
        if manifest is not None and feed is not None:
            raise ReleaseError("Use either --feed or --manifest, not both")
        if feed is not None:
            safe_https_url(feed)
        report["current"] = validate_metadata(read_local(version_file), release=False)
    except (OSError, ValueError) as error:
        report.update(status="invalid_local_configuration", error=diagnostic(error))
        return report, 2
    sources = (str(manifest),) if manifest is not None else ((feed,) if feed is not None else DEFAULT_FEEDS)
    if manifest is None and opener is None:
        opener = public_opener(use_env_proxy)
    for source in sources:
        try:
            if manifest is not None:
                remote = validate_metadata(read_local(source), release=True)
                final_source = source
            else:
                remote, final_source = fetch_release(source, timeout=timeout, opener=opener)
        except (OSError, ValueError, HTTPError, URLError, HTTPException) as error:
            report["attempts"].append({"source": source, "status": "rejected_or_unavailable", "error": diagnostic(error)})
            continue
        current_key = version_key(report["current"]["version"])
        remote_key = version_key(remote["version"])
        status = "update_available" if remote_key > current_key else "local_newer" if remote_key < current_key else "up_to_date"
        report.update(status=status, remote=remote, source=final_source,
                      release_feed_status="available", verified_schema=True)
        report["attempts"].append({"source": source, "status": "validated"})
        return report, 0
    return report, 1


def diagnostic(error):
    # Do not echo server bodies, credential-bearing redirect URLs, or OS paths.
    if isinstance(error, ReleaseError):
        return str(error)
    if isinstance(error, HTTPError):
        return f"HTTP {error.code}"
    if isinstance(error, (TimeoutError, URLError, HTTPException)):
        return "Network request failed or timed out"
    return "Could not read metadata"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--feed", help="One explicit public HTTPS feed; replaces the default fallback pair")
    source.add_argument("--manifest", type=Path, help="One local release.json; no network requests")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="Seconds per network operation (default 10, maximum 30)")
    parser.add_argument("--env-proxy", action="store_true", help="Use the environment's HTTPS proxy (needed on some hosts)")
    args = parser.parse_args(argv)
    report, code = run_check(feed=args.feed, manifest=args.manifest, timeout=args.timeout,
                             use_env_proxy=args.env_proxy)
    print(json.dumps(report, indent=2, allow_nan=False))
    return code


if __name__ == "__main__":
    sys.exit(main())
