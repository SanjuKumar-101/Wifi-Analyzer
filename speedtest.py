#!/usr/bin/env python3
import subprocess, json, os, time, sys
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
SPEED_LOG = os.path.join(DATA_DIR, "speed_history.json")

def run_speed_test():
    results = {}
    servers = [
        ("Cloudflare 50MB", "https://speed.cloudflare.com/__down?bytes=50000000"),
        ("Cloudflare 25MB", "https://speed.cloudflare.com/__down?bytes=25000000"),
        ("Cloudflare 5MB", "https://speed.cloudflare.com/__down?bytes=5000000"),
    ]
    for name, url in servers:
        try:
            r = subprocess.run(
                ["curl", "-s", "--max-time", "20", "-o", "/dev/null",
                 "-w", "%{speed_download}|%{time_total}|%{size_download}|%{http_code}", url],
                capture_output=True, text=True, timeout=25
            )
            parts = r.stdout.strip().split("|")
            if len(parts) >= 4:
                speed_bps = float(parts[0])
                time_s = float(parts[1])
                size = float(parts[2])
                code = parts[3]
                results[name] = {
                    "speed_mbps": round(speed_bps * 8 / 1_000_000, 2),
                    "speed_mbs": round(speed_bps / 1_000_000, 2),
                    "time_s": round(time_s, 2),
                    "size_mb": round(size / 1_000_000, 2),
                    "http_code": code,
                }
        except Exception as e:
            results[name] = {"error": str(e)}
    return results

def run_tcp_stats():
    stats = {}
    try:
        r = subprocess.run(["ss", "-ti", "dst", "1.1.1.1"], capture_output=True, text=True, timeout=5)
        for line in r.stdout.splitlines():
            if "cwnd" in line:
                m_cwnd = __import__("re").search(r"cwnd:(\d+)", line)
                m_rtt = __import__("re").search(r"rtt:(\d+\.?\d*)", line)
                m_bw = __import__("re").search(r"bw:(\d+\.?\d*)", line)
                if m_cwnd: stats["cwnd"] = int(m_cwnd.group(1))
                if m_rtt: stats["rtt_ms"] = float(m_rtt.group(1))
                if m_bw: stats["bandwidth_kbps"] = float(m_bw.group(1))
                break
    except:
        pass
    return stats

def run_latency_test():
    results = {}
    targets = [("Gateway", "10.227.0.1"), ("Cloudflare", "1.1.1.1"), ("Google", "8.8.8.8")]
    for name, host in targets:
        try:
            r = subprocess.run(
                ["ping", "-c", "5", "-W", "3", host],
                capture_output=True, text=True, timeout=10
            )
            loss_line = [l for l in r.stdout.splitlines() if "packet loss" in l]
            rtt_line = [l for l in r.stdout.splitlines() if "rtt" in l or "round-trip" in l]
            if loss_line:
                loss = __import__("re").search(r"(\d+)% packet loss", loss_line[0])
                results[name] = {"loss_pct": int(loss.group(1)) if loss else 100}
            if rtt_line:
                parts = rtt_line[0].split("=")[1].strip().split("/")
                results[name] = results.get(name, {})
                results[name]["min_ms"] = float(parts[0])
                results[name]["avg_ms"] = float(parts[1])
                results[name]["max_ms"] = float(parts[2])
        except:
            results[name] = {"error": "timeout"}
    return results

def get_signal_history():
    try:
        r = subprocess.run(["iw", "dev", "wlp0s20f3", "link"], capture_output=True, text=True, timeout=5)
        for line in r.stdout.splitlines():
            if "signal:" in line:
                import re
                m = re.search(r"(-?\d+\.?\d*)\s*dBm", line)
                if m: return float(m.group(1))
    except:
        pass
    return None

def load_history():
    if os.path.exists(SPEED_LOG):
        with open(SPEED_LOG) as f:
            return json.load(f)
    return {"tests": []}

def save_history(history):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(SPEED_LOG, "w") as f:
        json.dump(history, f, indent=2)

def run_full_test():
    print("=" * 60)
    print("  WIFI NETWORK DIAGNOSTIC SUITE - Speed Test")
    print("=" * 60)

    signal = get_signal_history()
    print(f"\nSignal: {signal} dBm")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    print("\n--- Speed Tests ---")
    speed = run_speed_test()
    for name, data in speed.items():
        if "error" in data:
            print(f"  {name}: ERROR - {data['error']}")
        else:
            print(f"  {name}: {data['speed_mbps']} Mbps ({data['size_mb']}MB in {data['time_s']}s)")

    print("\n--- TCP Stats ---")
    tcp = run_tcp_stats()
    if tcp:
        print(f"  cwnd: {tcp.get('cwnd', '?')}, rtt: {tcp.get('rtt_ms', '?')} ms, bw: {tcp.get('bandwidth_kbps', '?')} kbps")
    else:
        print("  No active TCP connections")

    print("\n--- Latency ---")
    latency = run_latency_test()
    for name, data in latency.items():
        if "error" in data:
            print(f"  {name}: {data['error']}")
        else:
            print(f"  {name}: avg={data.get('avg_ms','?')}ms loss={data.get('loss_pct','?')}%")

    entry = {
        "timestamp": datetime.now().isoformat(),
        "signal": signal,
        "speed": speed,
        "tcp": tcp,
        "latency": latency,
    }

    history = load_history()
    history["tests"].append(entry)
    if len(history["tests"]) > 500:
        history["tests"] = history["tests"][-500:]
    save_history(history)

    print(f"\n--- Summary ---")
    best = max(speed.values(), key=lambda x: x.get("speed_mbps", 0))
    print(f"Best speed: {best.get('speed_mbps', 0)} Mbps")
    print(f"Results saved to {SPEED_LOG}")
    return entry

if __name__ == "__main__":
    run_full_test()
