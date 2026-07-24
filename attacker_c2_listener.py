"""
================================================================
Attacker VM - Fake C2 Listener
(Scenario 3 - Insider-Introduced Malware: Data Theft via
Trojanized Download)
================================================================
Purpose: Purely for lab detection-engineering. Serves a harmless
"fake payload" file (posing as a trojanized download), logs beacon
check-ins from the Employee PC (simulating C2 heartbeat traffic),
and accepts uploaded files to a local folder (simulating stolen
data being exfiltrated to the attacker). No encryption/impact
stage - this scenario models data theft, not ransomware.

This does NOT execute anything on the receiving end, does NOT
contain any exploit code, and does NOT perform any destructive
action. It only generates network traffic patterns for your IDS
to detect.

Usage:
    python3 attacker_c2_listener.py

Then confirm your Suricata sensor is watching this VM's interface.
================================================================
"""

import http.server
import socketserver
import datetime
import os

PORT = 8080
LOG_FILE = "c2_activity.log"
PAYLOAD_DIR = "payload_store"
EXFIL_DIR = "exfil_received"

os.makedirs(PAYLOAD_DIR, exist_ok=True)
os.makedirs(EXFIL_DIR, exist_ok=True)

# Harmless "fake payload" - just a text file, no executable content.
# Renamed with a double extension to trigger delivery-stage IDS rules.
FAKE_PAYLOAD_NAME = "invoice.pdf.exe"
FAKE_PAYLOAD_PATH = os.path.join(PAYLOAD_DIR, FAKE_PAYLOAD_NAME)
if not os.path.exists(FAKE_PAYLOAD_PATH):
    with open(FAKE_PAYLOAD_PATH, "w") as f:
        f.write("MZ-- this is a benign placeholder file for FYP IDS testing. "
                "It performs no action if executed.\n")


def log(msg):
    line = f"[{datetime.datetime.now().isoformat()}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


class C2Handler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        client_ip = self.client_address[0]

        if self.path.startswith("/payload"):
            log(f"[DELIVERY] Fake payload requested by {client_ip}")
            with open(FAKE_PAYLOAD_PATH, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Disposition",
                              f'attachment; filename="{FAKE_PAYLOAD_NAME}"')
            self.end_headers()
            self.wfile.write(data)

        elif self.path.startswith("/beacon"):
            log(f"[C2] Beacon check-in from {client_ip} -- path: {self.path}")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"ack")

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        client_ip = self.client_address[0]
        if self.path.startswith("/exfil"):
            length = int(self.headers.get("Content-Length", 0))
            data = self.rfile.read(length)
            filename = os.path.join(
                EXFIL_DIR,
                f"exfil_{client_ip}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.bin"
            )
            with open(filename, "wb") as f:
                f.write(data)
            log(f"[EXFIL] Received {length} bytes from {client_ip} -> saved as {filename}")
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"received")
        else:
            self.send_response(404)
            self.end_headers()

    # Silence default console logging (we do our own via log())
    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    log(f"Starting fake C2 listener on port {PORT}")
    log(f"Endpoints: /payload (GET), /beacon (GET), /exfil (POST)")
    with socketserver.TCPServer(("0.0.0.0", PORT), C2Handler) as httpd:
        httpd.serve_forever()
