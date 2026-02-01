#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import aiohttp
import time
import ssl
import os
import sys
from urllib.parse import urlparse

# =========================
# LAVA • PERFORMANCE TESTER (AUTHORIZED ONLY)
# - Allowlist saved automatically (first run)
# - Trial expires after 3 days
# - Per-request colored logs
# - Post-test HEALTH CHECK (reachable / degraded / unreachable)
# =========================

# ---- Authorized allowlist ----
ALLOWED_PATH = os.path.join(os.path.expanduser("~"), ".lava_allowed.txt")

# ---- Defaults (tune for YOUR authorized servers) ----
DEFAULT_CONCURRENCY = 50
DEFAULT_TOTAL_REQUESTS = 1000
DEFAULT_TIMEOUT_S = 8.0

# ---- Indicators ----
WARN_LAT_MS = 700            # per-request warning latency threshold
DEGRADED_5XX_RATIO = 0.10    # if 5xx >= 10% => degraded
DEGRADED_P95_MS = 1200       # if p95 >= 1200ms => degraded

# =========================
# UI
# =========================
def c(text, code):
    return f"\033[{code}m{text}\033[0m"

def hr():
    return c("═" * 60, "36")

def clear():
    os.system("clear" if os.name != "nt" else "cls")

ART = r"""

⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣀⣀⣀⣀⣠⣼⠂⠀⠀⠀⠀⠙⣦⢀⠀⠀⠀⠀⠀⢶⣤⣀⣀⣀⣀⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣠⣴⣶⣿⣿⣿⣿⣿⣿⣿⣿⠷⢦⠀⣹⣶⣿⣦⣿⡘⣇⠀⠀⠀⢰⠾⣿⣿⣿⣟⣻⣿⣿⣿⣷⣦⣄⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣤⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⡟⠀⠀⠀⠀⢺⣿⣿⣿⣿⣿⣿⣿⣆⠀⠀⠀⠀⠀⠀⢹⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣦⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⢟⣥⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀⠀⠀⠀⢻⣿⣿⡏⢹⣿⣿⣿⣿⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣮⣝⢷⣄⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⣴⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⢛⣿⣿⣿⡇⠀⠀⠀⠀⠛⣿⣿⣷⡀⠘⢿⣧⣻⡷⠀⠀⠀⠀⠀⠀⣿⣿⣿⣟⢿⣿⣿⣿⣿⣿⣿⣿⣿⣝⢧⡀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⢠⣾⣿⠟⣡⣾⣿⣿⣧⣿⡿⣋⣴⣿⣿⣿⣿⣧⠀⠀⠀⠀⠀⢻⣿⣿⣿⣶⡄⠙⠛⠁⠀⠀⠀⠀⠀⢸⣿⣿⣿⣿⣷⣝⢻⣿⣟⣿⣿⣷⣮⡙⢿⣽⣆⠀⠀⠀⠀⠀
⠀⠀⠀⠀⢀⡿⢋⣴⣿⣿⣿⣿⣿⣼⣯⣾⣿⣿⡿⣻⣿⣿⣿⣦⠀⠀⠀⠀⢀⣹⣿⣿⣿⣿⣶⣤⠀⠀⠀⠀⠀⣰⣿⣿⣿⣿⠻⣿⣿⣿⣮⣿⣿⣿⣿⣿⣿⣦⡙⢿⣇⠀⠀⠀⠀
⠀⠀⠀⣠⡏⣰⣿⣿⡿⢿⣿⣿⣿⣿⣿⣿⡿⢋⣼⣿⣿⣿⣿⣿⣷⡤⠀⣠⣿⣿⣿⣿⣿⣿⣿⣿⣷⣄⠀⢠⣾⣿⣿⣿⣿⣿⣷⡜⢿⣿⣿⣿⣿⣿⣿⡿⠿⣿⣿⣦⡙⣦⠀⠀⠀
⠀⠀⣰⢿⣿⣿⠟⠋⣠⣾⣿⣿⣿⣿⣿⠛⢡⣾⡿⢻⣿⣿⣿⣿⣿⣿⣿⣿⡿⠋⠻⣿⡟⣿⣿⣿⠻⢿⣿⣿⣿⣿⣿⣿⣿⣟⠻⣿⣆⠙⢿⣿⣿⣿⣿⣿⣦⡈⠻⣿⣿⣟⣧⠀⠀
⠀⣰⢣⣿⡿⠃⣠⡾⠟⠁⠀⣸⣿⡟⠁⢀⣿⠋⢠⣿⡏⣿⣿⣿⣿⣿⢿⠁⢀⣠⣴⢿⣷⣿⣿⣿⠀⠀⠽⢻⣿⣿⣿⣿⡼⣿⡇⠈⢿⡆⠀⠻⣿⣧⠀⠈⠙⢿⣆⠈⠻⣿⣎⢧⠀
⠀⢣⣿⠟⢀⡼⠋⠀⠀⢀⣴⠿⠋⠀⠀⣾⡟⠀⢸⣿⠙⣿⠃⠘⢿⡟⠀⣰⢻⠟⠻⣿⣿⣿⣿⣿⣀⠀⠀⠘⣿⠋⠀⣿⡇⣿⡇⠀⠸⣿⡄⠀⠈⠻⣷⣄⠀⠀⠙⢷⡀⠙⣿⣆⠁
⢀⣿⡏⠀⡞⠁⢀⡠⠞⠋⠁⠀⠀⠀⠈⠉⠀⠀⠀⠿⠀⠈⠀⠀⠀⠀⠀⣿⣿⣰⣾⣿⣿⣿⣿⣿⣿⣤⠀⠀⠀⠀⠀⠉⠀⠸⠃⠀⠀⠈⠋⠀⠀⠀⠀⠙⠳⢤⣀⠀⠹⡄⠘⣿⡄
⣸⡟⠀⣰⣿⠟⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠛⠿⠿⠿⠟⠁⠀⠹⣿⣷⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠻⣿⣧⠀⢹⣷
⣿⠃⢠⡿⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣄⣤⣀⠀⠀⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢻⡇⠀⣿
⣿⠀⢸⠅⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣰⡿⠋⠉⢻⣧⢀⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠀⢸
⡇⠀⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢿⣧⡀⠀⠀⣿⣾⡟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠀⢸
⢸⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠻⠿⣿⣿⠟⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡾
⠈⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣰⡿⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠃
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⡏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣧⢀⣾⣤⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⡼⣿⣿⣾⣤⣠⡼⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀

██████╗░██████╗░░█████╗░░██████╗░░░░█████╗░████████╗░█████╗░░█████╗░██╗░░██╗
██╔══██╗██╔══██╗██╔══██╗██╔════╝░░░██╔══██╗╚══██╔══╝██╔══██╗██╔══██╗██║░██╔╝
██║░░██║██║░░██║██║░░██║╚█████╗░░░░███████║░░░██║░░░███████║██║░░╚═╝█████═╝░
██║░░██║██║░░██║██║░░██║░╚═══██╗██╗██╔══██║░░░██║░░░██╔══██║██║░░██╗██╔═██╗░
██████╔╝██████╔╝╚█████╔╝██████╔╝╚█║██║░░██║░░░██║░░░██║░░██║╚█████╔╝██║░╚██╗
╚═════╝░╚═════╝░░╚════╝░╚═════╝░░╚╝╚═╝░░╚═╝░░░╚═╝░░░╚═╝░░╚═╝░╚════╝░╚═╝░░╚═╝


        LAVA • ULTRA TOOLKIT
      High-Speed Load Tester (SAFE)
"""

DISCLAIMER = f"""
[DISCLAIMER]
This tool is for EDUCATIONAL & AUTHORIZED performance testing only.
Use ONLY on systems you own or have explicit permission to test.
Developer contact: {DEVELOPER_TG}

Type: I AGREE  to continue
"""

def slow_print(lines, delay=0.002):
    for ch in lines:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def now():
    return time.strftime("%H:%M:%S")

# =========================
# Allowlist
# =========================
def load_allowed_hosts():
    hosts = set()
    try:
        with open(ALLOWED_PATH, "r", encoding="utf-8") as f:
            for line in f:
                h = line.strip().lower()
                if h and not h.startswith("#"):
                    hosts.add(h)
    except Exception:
        pass
    return hosts

def write_allowed_hosts(hosts):
    try:
        with open(ALLOWED_PATH, "w", encoding="utf-8") as f:
            for h in sorted(set(hosts)):
                f.write(h + "\n")
    except Exception:
        pass

def add_allowed_host(host: str):
    host = (host or "").strip().lower()
    host = host.replace("http://", "").replace("https://", "").strip("/")
    if not host or "/" in host or " " in host:
        return False
    hosts = load_allowed_hosts()
    hosts.add(host)
    write_allowed_hosts(hosts)
    return True

def first_time_setup():
    if load_allowed_hosts():
        return
    clear()
    print(c(ART, "31"))
    print(hr())
    print(c("FIRST TIME SETUP", "92"))
    print(c("Enter ONE authorized domain you own / have permission to test.", "93"))
    print(hr())
    host = input(c("Authorized domain (example.com): ", "92")).strip()
    if add_allowed_host(host):
        print(c("Saved ✅", "92"))
        time.sleep(0.8)
    else:
        print(c("Invalid domain. Restart and try again.", "91"))
        time.sleep(1.2)

def validate_url_allowlist(url: str):
    u = urlparse(url)
    if u.scheme not in ("http", "https"):
        raise ValueError("URL must include http:// or https://")
    host = (u.hostname or "").lower()
    if not host:
        raise ValueError("Invalid URL host")
    allowed = load_allowed_hosts()
    if not allowed:
        raise PermissionError("No authorized domains configured.")
    if host not in allowed:
        raise PermissionError(
            f"Target host '{host}' is not allowed.\n"
            f"Allowed: {', '.join(sorted(allowed))}\n"
            f"Add ONLY authorized domains in menu."
        )
    return u

# =========================
# Stats helpers
# =========================
def pct(arr, p):
    if not arr:
        return None
    arr = sorted(arr)
    k = int(round((p/100) * (len(arr)-1)))
    return arr[k]

def ask_int(prompt, default):
    raw = input(prompt).strip()
    return default if raw == "" else int(raw)

def ask_float(prompt, default):
    raw = input(prompt).strip()
    return default if raw == "" else float(raw)

# =========================
# Core load test
# =========================
async def worker(session, url, sem, stats, timeout):
    async with sem:
        t0 = time.perf_counter()
        try:
            async with session.get(url, timeout=timeout) as r:
                await r.read()
                dt_ms = (time.perf_counter() - t0) * 1000.0

                stats["ok"] += 1
                stats["lat"].append(dt_ms)
                stats["codes"][r.status] = stats["codes"].get(r.status, 0) + 1

                # Per-request indicator (objective)
                # Green: 2xx/3xx and fast
                # Orange: slow or 4xx
                # Red: 5xx
                if r.status >= 500:
                    print(c(f"[FAIL] {r.status}  {dt_ms:7.1f} ms  -> {url}", "31"))
                elif r.status >= 400 or dt_ms >= WARN_LAT_MS:
                    print(c(f"[WARN] {r.status}  {dt_ms:7.1f} ms  -> {url}", "33"))
                else:
                    print(c(f"[OK]   {r.status}  {dt_ms:7.1f} ms  -> {url}", "32"))

        except Exception as e:
            dt_ms = (time.perf_counter() - t0) * 1000.0
            stats["fail"] += 1
            name = type(e).__name__
            stats["errors"][name] = stats["errors"].get(name, 0) + 1
            print(c(f"[ERR]  ---  {dt_ms:7.1f} ms  -> {name}: {e}", "31"))

async def run(url, concurrency, total, timeout_s, verify_tls, show_progress=True):
    sem = asyncio.Semaphore(concurrency)
    stats = {"ok": 0, "fail": 0, "lat": [], "codes": {}, "errors": {}}

    ssl_ctx = None
    if urlparse(url).scheme == "https":
        ssl_ctx = ssl.create_default_context()
        if not verify_tls:
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE

    timeout = aiohttp.ClientTimeout(total=timeout_s)
    conn = aiohttp.TCPConnector(ssl=ssl_ctx, limit=0)

    async with aiohttp.ClientSession(connector=conn, headers={"User-Agent": "LAVA-PERF/1.0"}) as session:
        tasks = [asyncio.create_task(worker(session, url, sem, stats, timeout)) for _ in range(int(total))]

        if show_progress:
            while True:
                done = sum(1 for t in tasks if t.done())
                bar_len = 28
                filled = int((done / int(total)) * bar_len) if total else bar_len
                bar = "█" * filled + "░" * (bar_len - filled)
                sys.stdout.write("\r" + c(f"[{now()}] Running ", "90") + c(f"|{bar}| ", "96") + c(f"{done}/{total}", "92"))
                sys.stdout.flush()
                if done >= int(total):
                    break
                await asyncio.sleep(0.15)
            print()

        await asyncio.gather(*tasks, return_exceptions=True)

    return stats

# =========================
# Post-test Health Check (objective)
# =========================
async def health_check(url, timeout_s, verify_tls):
    ssl_ctx = None
    if urlparse(url).scheme == "https":
        ssl_ctx = ssl.create_default_context()
        if not verify_tls:
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE

    timeout = aiohttp.ClientTimeout(total=timeout_s)
    conn = aiohttp.TCPConnector(ssl=ssl_ctx, limit=0)

    try:
        async with aiohttp.ClientSession(connector=conn, headers={"User-Agent": "LAVA-HEALTH/1.0"}) as session:
            t0 = time.perf_counter()
            async with session.get(url, timeout=timeout) as r:
                await r.read()
                dt_ms = (time.perf_counter() - t0) * 1000.0
                return {"reachable": True, "status": r.status, "lat_ms": dt_ms, "error": None}
    except Exception as e:
        return {"reachable": False, "status": None, "lat_ms": None, "error": f"{type(e).__name__}: {e}"}

def classify_after_test(stats):
    sent = stats["ok"] + stats["fail"]
    codes = stats["codes"]
    lat = stats["lat"]

    five_xx = sum(v for k, v in codes.items() if isinstance(k, int) and k >= 500)
    five_ratio = (five_xx / sent) if sent else 0.0
    p95 = pct(lat, 95) if lat else None

    degraded = (five_ratio >= DEGRADED_5XX_RATIO) or (p95 is not None and p95 >= DEGRADED_P95_MS)
    return five_ratio, p95, degraded

# =========================
# Screens
# =========================
def menu():
    print(hr())
    print(c("  [1] Start Performance Test (HTTP GET)", "92"))
    print(c("  [2] Help / Instructions", "93"))
    print(c("  [3] Exit", "91"))
    print(c("  [4] Add Allowed Domain (authorized only)", "96"))
    print(c("  [5] Show Allowed Domains", "96"))
    print(hr())

def help_screen():
    clear()
    print(c(ART, "31"))
    print(hr())
    print(c("HOW TO USE:", "92"))
    print(" • Add your authorized domain(s) once (menu [4]).")
    print(" • Start test (menu [1]) and enter a full URL.")
    print(" • Watch per-request logs: OK / WARN / FAIL.")
    print(" • After test, you get a HEALTH CHECK (reachable/degraded/unreachable).")
    print(hr())
    input(c("Press Enter to return...", "90"))

def show_allowed():
    clear()
    print(c(ART, "31"))
    print(hr())
    hosts = load_allowed_hosts()
    if not hosts:
        print(c("No allowed domains yet.", "91"))
    else:
        print(c("ALLOWED DOMAINS:", "92"))
        for h in sorted(hosts):
            print(" • " + c(h, "96"))
    print(hr())
    input(c("Press Enter to return...", "90"))

def add_domain_screen():
    clear()
    print(c(ART, "31"))
    print(hr())
    print(c("ADD AUTHORIZED DOMAIN", "92"))
    print(c("Example: example.com (no http/https)", "93"))
    print(hr())
    host = input(c("Domain: ", "92")).strip()
    if add_allowed_host(host):
        print(c("Saved ✅", "92"))
    else:
        print(c("Invalid domain ❌", "91"))
    time.sleep(1.0)

def results_screen(url, dt, stats, verify_tls):
    clear()
    ok, fail = stats["ok"], stats["fail"]
    sent = ok + fail
    rps = (sent / dt) if dt > 0 else 0.0

    print(c("✅ TEST COMPLETED", "92"))
    print(hr())
    print(c("TARGET :", "96"), url)
    print(c("TIME   :", "96"), f"{dt:.2f}s")
    print(c("SENT   :", "96"), sent)
    print(c("OK     :", "92"), ok)
    print(c("FAILED :", "91"), fail)
    print(c("RPS    :", "93"), f"{rps:.2f}")
    print(hr())

    lat = stats["lat"]
    if lat:
        avg = sum(lat) / len(lat)
        p50 = pct(lat, 50)
        p95 = pct(lat, 95)
        mx = max(lat)
        print(c("LATENCY (ms)", "95"))
        print(f"  avg: {avg:.1f}   p50: {p50:.1f}   p95: {p95:.1f}   max: {mx:.1f}")
        print(hr())

    print(c("HTTP STATUS CODES", "94"))
    if stats["codes"]:
        for code in sorted(stats["codes"].keys()):
            print(f"  {code}: {stats['codes'][code]}")
    else:
        print("  (none)")
    print(hr())

    print(c("ERRORS", "91"))
    if stats["errors"]:
        for e, cnt in sorted(stats["errors"].items(), key=lambda x: x[1], reverse=True):
            print(f"  {e}: {cnt}")
    else:
        print("  (none)")
    print(hr())

    # Post-test status (objective)
    five_ratio, p95, degraded = classify_after_test(stats)
    hc = asyncio.run(health_check(url, timeout_s=DEFAULT_TIMEOUT_S, verify_tls=verify_tls))

    print(c("WEBSITE STATUS AFTER TEST", "94"))  # blue header
    if not hc["reachable"]:
        print(c("❌ Service unreachable (no response / timeout)", "31"))
        print(c(f"   Error: {hc['error']}", "90"))
    else:
        # reachable: decide OK vs Degraded based on ratios/latency/status
        if degraded or (hc["status"] is not None and hc["status"] >= 500):
            print(c("⚠️  Degraded / server issues detected", "33"))
            if hc["status"] is not None:
                print(c(f"   Health status: {hc['status']}  |  {hc['lat_ms']:.1f} ms", "90"))
            print(c(f"   5xx ratio during test: {five_ratio*100:.1f}%  |  p95: {p95:.0f} ms" if p95 else f"   5xx ratio: {five_ratio*100:.1f}%", "90"))
        else:
            print(c("✅ Service reachable (still responding normally)", "32"))
            print(c(f"   Health status: {hc['status']}  |  {hc['lat_ms']:.1f} ms", "90"))

    print(hr())
    print(c(f"Developer: {DEVELOPER_TG}", "93"))
    input(c("Press Enter to return to menu...", "90"))

# =========================
# Main
# =========================

    clear()
    print(c(ART, "31"))
    print(hr())
    slow_print(c(DISCLAIMER.strip(), "93"), delay=0.002)
    print(hr())
    agree = input(c(">> ", "92")).strip()
    if agree != "I AGREE":
        print(c("Exiting... (Disclaimer not accepted)", "91"))
        sys.exit(0)

    while True:
        clear()
        print(c(ART, "31"))
        menu()
        choice = input(c("Select: ", "92")).strip()

        if choice == "1":
            clear()
            print(c("⚙ CONFIGURATION", "96"))
            print(hr())

            url = input("Target URL (http/https): ").strip()
            try:
                validate_url_allowlist(url)
            except Exception as e:
                print(c(f"\n[ERROR] {e}", "91"))
                input(c("Press Enter...", "90"))
                continue

            conc = ask_int(f"Concurrency [{DEFAULT_CONCURRENCY}]: ", DEFAULT_CONCURRENCY)
            total = ask_int(f"Total Requests [{DEFAULT_TOTAL_REQUESTS}]: ", DEFAULT_TOTAL_REQUESTS)
            tout  = ask_float(f"Timeout seconds [{DEFAULT_TIMEOUT_S}]: ", DEFAULT_TIMEOUT_S)
            verify = input("Verify TLS? (Y/n) [Y]: ").strip().lower()
            verify_tls = (verify != "n")

            print(hr())
            print(c("🚀 STARTING...", "92"))
            print(c("Logs: OK (green) / WARN (orange) / FAIL (red).", "90"))
            print(hr())

            t0 = time.time()
            stats = asyncio.run(run(url, conc, total, tout, verify_tls, show_progress=True))
            dt = time.time() - t0

            results_screen(url, dt, stats, verify_tls)

        elif choice == "2":
            help_screen()

        elif choice == "3":
            print(c("Bye 👋", "90"))
            break

        elif choice == "4":
            add_domain_screen()

        elif choice == "5":
            show_allowed()

        else:
            print(c("Invalid option.", "91"))
            time.sleep(0.8)

if __name__ == "__main__":
    main()
