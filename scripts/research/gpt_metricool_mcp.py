#!/usr/bin/env python3
"""Token-free, LLM-free client for the official Metricool MCP server (read-only).

One-time interactive step (opens your normal browser, you log in to Metricool):
    python gpt_metricool_mcp.py login
Afterwards every call is plain HTTPS using a refresh token kept outside the repo
(%LOCALAPPDATA%\\web-escritor-social\\metricool_oauth.json, or $SOCIAL_STATE_DIR):
    python gpt_metricool_mcp.py status
    python gpt_metricool_mcp.py tools
Standard library only. Never prints tokens.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import http.server
import json
import os
from pathlib import Path
import secrets
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser

MCP_URL = "https://ai.metricool.com/mcp"
AUTH_URL = "https://app.metricool.com/oauth/authorize"
TOKEN_URL = "https://app.metricool.com/oauth/token"
REGISTER_URL = "https://app.metricool.com/oauth/register"
SCOPE = "mcp:read"
LOGIN_PORTS = range(53682, 53700)  # dedicated high range, first free one is used
PROTOCOL = "2025-06-18"


class ReauthRequired(RuntimeError):
    """The refresh token is gone or revoked: run `login` again."""


def state_dir() -> Path:
    base = os.environ.get("SOCIAL_STATE_DIR")
    root = Path(base) if base else Path(os.environ.get("LOCALAPPDATA") or Path.home() / ".local/state") / "web-escritor-social"
    root.mkdir(parents=True, exist_ok=True)
    return root


def restrict_permissions() -> None:
    """Windows: drop inherited ACLs on the state dir so only the current user can read the tokens."""
    if os.name == "nt":
        import subprocess
        subprocess.run(["icacls", str(state_dir()), "/inheritance:r", "/grant:r", f"{os.environ['USERNAME']}:(OI)(CI)F"],
                       capture_output=True)


def _creds_path() -> Path:
    return state_dir() / "metricool_oauth.json"


def _load() -> dict:
    try:
        return json.loads(_creds_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _save(data: dict) -> None:
    path = _creds_path()
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data), encoding="utf-8")
    os.replace(tmp, path)


def _post(url: str, *, form: dict | None = None, body: dict | None = None, headers: dict | None = None,
          timeout: int = 30) -> tuple[int, dict, str]:
    data = urllib.parse.urlencode(form).encode() if form is not None else json.dumps(body).encode()
    h = {"Content-Type": "application/x-www-form-urlencoded" if form is not None else "application/json",
         "Accept": "application/json, text/event-stream", "User-Agent": "web-escritor-social/1"}
    h.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=h, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, dict(r.headers), r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", "replace")


def _free_port() -> int:
    import socket
    for port in LOGIN_PORTS:
        with socket.socket() as sock:
            if sock.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise OSError("no free loopback port for the OAuth callback")


def login() -> int:
    creds = {}  # re-register every login: the redirect URI embeds the chosen port
    port = _free_port()
    REDIRECT = f"http://127.0.0.1:{port}/callback"
    if True:
        status, _, text = _post(REGISTER_URL, body={
            "client_name": "web-escritor social refresh (local)", "redirect_uris": [REDIRECT],
            "grant_types": ["authorization_code", "refresh_token"], "response_types": ["code"],
            "token_endpoint_auth_method": "none", "scope": SCOPE})
        if status >= 300:
            print(f"client registration failed: HTTP {status}", file=sys.stderr)
            return 1
        creds["client_id"] = json.loads(text)["client_id"]
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    state = secrets.token_urlsafe(16)
    got: dict = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            got.update({k: v[0] for k, v in q.items()})
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write("Autorizacion recibida. Puedes cerrar esta pestana.".encode())

        def log_message(self, *a):
            pass

    server = http.server.HTTPServer(("127.0.0.1", port), Handler)
    server.timeout = 1
    url = AUTH_URL + "?" + urllib.parse.urlencode({
        "response_type": "code", "client_id": creds["client_id"], "redirect_uri": REDIRECT,
        "scope": SCOPE, "state": state, "code_challenge": challenge, "code_challenge_method": "S256",
        "resource": MCP_URL})
    print("Abre este enlace si el navegador no se abre solo y accede a Metricool:\n" + url, flush=True)
    webbrowser.open(url)
    deadline = time.time() + 600
    while "code" not in got and "error" not in got and time.time() < deadline:
        server.handle_request()
    server.server_close()
    if got.get("state") != state or "code" not in got:
        print("login cancelled or timed out: " + got.get("error", "no code"), file=sys.stderr)
        return 1
    status, _, text = _post(TOKEN_URL, form={
        "grant_type": "authorization_code", "code": got["code"], "redirect_uri": REDIRECT,
        "client_id": creds["client_id"], "code_verifier": verifier, "resource": MCP_URL})
    if status >= 300:
        print(f"token exchange failed: HTTP {status}", file=sys.stderr)
        return 1
    _store_tokens(creds, json.loads(text))
    restrict_permissions()
    print("login ok: refresh token saved outside the repository")
    return 0


def _store_tokens(creds: dict, tok: dict) -> None:
    creds["access_token"] = tok["access_token"]
    creds["expires_at"] = time.time() + int(tok.get("expires_in", 3600))
    if tok.get("refresh_token"):
        creds["refresh_token"] = tok["refresh_token"]
    _save(creds)


def access_token() -> str:
    creds = _load()
    if not creds.get("refresh_token") and not creds.get("access_token"):
        raise ReauthRequired("no Metricool credentials: run `gpt_metricool_mcp.py login`")
    if creds.get("access_token") and creds.get("expires_at", 0) - 60 > time.time():
        return creds["access_token"]
    if not creds.get("refresh_token"):
        raise ReauthRequired("access token expired and no refresh token: run `login`")
    status, _, text = _post(TOKEN_URL, form={
        "grant_type": "refresh_token", "refresh_token": creds["refresh_token"],
        "client_id": creds["client_id"], "resource": MCP_URL})
    if status in (400, 401):
        raise ReauthRequired("Metricool refresh token rejected: run `login`")
    if status >= 300:
        raise OSError(f"Metricool token endpoint HTTP {status}")  # transient: keep credentials
    _store_tokens(creds, json.loads(text))
    return _load()["access_token"]


def _decode(text: str) -> dict:
    text = text.strip()
    if text.startswith("{"):
        return json.loads(text)
    for line in text.splitlines():  # Streamable HTTP may answer as an SSE event
        if line.startswith("data:") and line[5:].strip().startswith("{"):
            return json.loads(line[5:].strip())
    raise ValueError("unparseable MCP response")


class McpClient:
    def __init__(self, token: str | None = None):
        self.token = token or access_token()
        self.session: str | None = None
        self._id = 0
        self.rpc("initialize", {"protocolVersion": PROTOCOL, "capabilities": {},
                                "clientInfo": {"name": "web-escritor-social", "version": "1"}})
        self._send({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def _send(self, message: dict) -> dict:
        headers = {"Authorization": f"Bearer {self.token}", "MCP-Protocol-Version": PROTOCOL}
        if self.session:
            headers["Mcp-Session-Id"] = self.session
        status, hdrs, text = _post(MCP_URL, body=message, headers=headers, timeout=60)
        if status in (401, 403):
            raise ReauthRequired(f"Metricool MCP rejected the token (HTTP {status})")
        if status >= 300:
            raise OSError(f"Metricool MCP HTTP {status}")
        self.session = {k.lower(): v for k, v in hdrs.items()}.get("mcp-session-id", self.session)
        return _decode(text) if "id" in message and text.strip() else {}

    def rpc(self, method: str, params: dict | None = None) -> dict:
        self._id += 1
        reply = self._send({"jsonrpc": "2.0", "id": self._id, "method": method, "params": params or {}})
        if "error" in reply:
            raise ValueError(f"MCP {method}: {reply['error'].get('message', reply['error'])}")
        return reply.get("result", {})

    def tools(self) -> list[dict]:
        return self.rpc("tools/list").get("tools", [])

    def call(self, name: str, arguments: dict) -> object:
        result = self.rpc("tools/call", {"name": name, "arguments": arguments})
        if result.get("isError"):
            raise ValueError(f"tool {name} failed")
        if "structuredContent" in result:
            return result["structuredContent"]
        text = "".join(c.get("text", "") for c in result.get("content", []) if c.get("type") == "text")
        try:
            return json.loads(text)
        except ValueError:
            return text


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("command", choices=["login", "status", "tools"])
    args = p.parse_args(argv)
    if args.command == "login":
        return login()
    try:
        client = McpClient()
    except ReauthRequired as e:
        print("REAUTH REQUIRED: " + str(e), file=sys.stderr)
        return 2
    tools = client.tools()
    if args.command == "status":
        print(f"ok: {len(tools)} tools available")
    else:
        for t in tools:
            print(t["name"], "-", (t.get("description") or "").split("\n")[0][:100])
    return 0


if __name__ == "__main__":
    sys.exit(main())
