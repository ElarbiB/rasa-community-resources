"""Loopback demo worker; one retained SDK client, closed on shutdown."""
import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from typesafe_sdk import RetryPolicy, TypeSafeClient
from .accounts import Accounts
from .selector import MODEL, Selector
from .scripted import scripted_transport


def handler(selector):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path != "/select":
                self.send_error(404)
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 12000:
                    raise ValueError()
                body = json.loads(self.rfile.read(size))
                if not isinstance(body, dict) or set(body) != {"owner", "message"}:
                    raise ValueError()
                result = selector.select(body["owner"], body["message"])
            except (ValueError, TypeError):
                self.send_error(400)
                return
            encoded = json.dumps(result).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def log_message(self, *_):
            pass

    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Use the paid TypeSafe service; default is scripted")
    parser.add_argument("--port", type=int, default=5029)
    args = parser.parse_args()
    transport = None if args.live else scripted_transport()[0]
    key = os.environ["TYPESAFE_API_KEY"] if args.live else "scripted-local-test"
    base = "https://api.typesafe.ai" if args.live else "https://scripted.invalid"
    with TypeSafeClient(api_key=key, base_url=base, model=MODEL, timeout=2,
                        transport=transport, retry=RetryPolicy(max_retries=0)) as client:
        with HTTPServer(("127.0.0.1", args.port), handler(Selector(client, Accounts()))) as server:
            print("Loopback worker ready; mode=" + ("live" if args.live else "scripted"), flush=True)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass


if __name__ == "__main__":
    main()
