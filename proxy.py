
from __future__ import annotations

import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urlsplit

UPSTREAM = "http://127.0.0.1:11434"
HOST = "127.0.0.1"
PORT = int(os.environ.get("OLLAMA_PROXY_PORT", "11435"))
MAX_BODY_BYTES = 8 * 1024 * 1024

PUBLIC_ENDPOINTS = {
    ("GET", "/api/tags"),
    ("GET", "/api/version"),
}

HOP_BY_HOP_HEADERS = {
    "connection", "keep-alive", "proxy-authenticate",
    "proxy-authorization", "te", "trailers",
    "transfer-encoding", "upgrade", "host", "authorization",
}


def authorization_is_valid(
    header: str | None,
    expected_token: str,
) -> bool:
    if not header or not expected_token:
        return False

    scheme, separator, supplied = header.partition(" ")

    return (
        separator == " "
        and scheme.casefold() == "bearer"
        and bool(supplied.strip())
        and hmac.compare_digest(supplied.strip(), expected_token)
    )


class OllamaProxyHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "ManoMINI-AuthProxy/1.1"

    def log_message(self, format_string: str, *args) -> None:
        print(f"[proxy] {self.client_address[0]} {self.command} {self.path}")

    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        self.send_response(status)
        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8",
        )
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()

        self.wfile.write(body)
        self.close_connection = True

    def _proxy(self) -> None:
        parsed_path = urlsplit(self.path)
        endpoint = parsed_path.path

        if not endpoint.startswith("/api/"):
            self._send_json(
                404,
                {"error": "Only Ollama /api endpoints are exposed"},
            )
            return

        if (self.command, endpoint) not in PUBLIC_ENDPOINTS:
            if not authorization_is_valid(
                self.headers.get("Authorization"),
                self.server.api_token,
            ):
                self._send_json(401, {"error": "Unauthorized"})
                return

        try:
            content_length = int(
                self.headers.get("Content-Length", "0") or "0"
            )
        except ValueError:
            self._send_json(400, {"error": "Invalid Content-Length"})
            return

        if content_length < 0 or content_length > MAX_BODY_BYTES:
            self._send_json(413, {"error": "Request body is too large"})
            return

        body = (
            self.rfile.read(content_length)
            if content_length
            else None
        )

        headers = {
            key: value
            for key, value in self.headers.items()
            if key.casefold() not in HOP_BY_HOP_HEADERS
            and key.casefold() not in {
                "content-length",
                "accept-encoding",
            }
        }

        headers["Accept-Encoding"] = "identity"

        request = Request(
            UPSTREAM + self.path,
            data=body,
            headers=headers,
            method=self.command,
        )

        try:
            upstream = urlopen(request, timeout=3600)

        except HTTPError as error:
            upstream = error

        except (URLError, TimeoutError, OSError) as error:
            self._send_json(
                502,
                {
                    "error": (
                        "Ollama upstream unavailable: "
                        f"{type(error).__name__}"
                    )
                },
            )
            return

        try:
            self.send_response(upstream.status)

            for key, value in upstream.headers.items():
                if key.casefold() not in HOP_BY_HOP_HEADERS:
                    self.send_header(key, value)

            self.send_header("Connection", "close")
            self.end_headers()

            while True:
                chunk = upstream.read(64 * 1024)

                if not chunk:
                    break

                self.wfile.write(chunk)
                self.wfile.flush()

        except (BrokenPipeError, ConnectionResetError):
            pass

        finally:
            upstream.close()
            self.close_connection = True

    do_GET = _proxy
    do_POST = _proxy
    do_HEAD = _proxy


def main() -> None:
    token = os.environ.get("API_ACCESS_TOKEN", "").strip()

    if len(token) < 32:
        raise SystemExit(
            "API_ACCESS_TOKEN must contain at least 32 characters."
        )

    server = ThreadingHTTPServer(
        (HOST, PORT),
        OllamaProxyHandler,
    )

    server.api_token = token

    print(
        f"ManoMINI proxy listening on {HOST}:{PORT}"
    )

    server.serve_forever()


if __name__ == "__main__":
    main()
