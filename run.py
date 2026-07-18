#!/usr/bin/env python3
import sys, os, subprocess, time, re, platform

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

from utils import get_wifi_interface, get_active_ssid, get_link_stats, get_current_connection, run_cmd

OS = platform.system()

def check_dependencies():
    missing = []
    if OS == "Linux":
        for cmd, pkg in [("iw", "iw"), ("curl", "curl"), ("ping", "iputils-ping")]:
            if not subprocess.run(["which", cmd], capture_output=True).returncode == 0:
                missing.append((cmd, pkg))
    elif OS == "Darwin":
        for cmd in ["curl", "ping"]:
            if not subprocess.run(["which", cmd], capture_output=True).returncode == 0:
                missing.append((cmd, cmd))
    if missing:
        print("\x1b[33m[!] Missing system dependencies:\x1b[0m")
        for cmd, pkg in missing:
            print(f"    - {cmd} ({pkg})")
        if OS == "Linux":
            pkgs = " ".join(p for _, p in missing)
            print(f"\n    Install with: sudo apt install {pkgs}")
        print()
    return len(missing) == 0

BANNER = """
\x1b[36m
 ██╗    ██╗██╗███████╗██╗    ███████╗ ██████╗ █████╗ ███╗   ██╗
 ██║    ██║██║██╔════╝██║    ██╔════╝██╔════╝██╔══██╗████╗  ██║
 ██║ █╗ ██║██║█████╗  ██║    ███████╗██║     ███████║██╔██╗ ██║
 ██║███╗██║██║██╔══╝  ██║    ╚════██║██║     ██╔══██║██║╚██╗██║
 ╚███╔███╔╝██║██║     ██║    ███████║╚██████╗██║  ██║██║ ╚████║
  ╚══╝╚══╝ ╚═╝╚═╝     ╚═╝    ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝
            WiFi Diagnostic Suite v1.0
\x1b[0m"""

def banner():
    print(BANNER)

def cmd_scan():
    from scanner import scan_networks, get_current_connection, get_link_stats, get_power_save, save_scan
    print("\x1b[33m[*] Scanning WiFi networks...\x1b[0m")
    networks = scan_networks()
    conn = get_current_connection()
    link = get_link_stats()
    ps = get_power_save()
    print(f"\x1b[32m[+] Found {len(networks)} networks\x1b[0m")
    active = get_active_ssid() or "unknown"
    print(f"    Connected: {conn.get('ssid', active)} at {conn.get('signal_dbm', '?')} dBm")
    print(f"    Power save: {'OFF' if ps else 'ON'}")
    path, _ = save_scan(networks, conn, link, os.path.join(BASE, "data"))
    print(f"    Saved: {path}")
    return networks, conn, link

def cmd_analyze():
    from scanner import scan_networks, get_current_connection, get_link_stats, save_scan
    from analyzer import generate_analysis
    print("\x1b[33m[*] Full network analysis...\x1b[0m")
    networks = scan_networks()
    conn = get_current_connection()
    link = get_link_stats()
    path, data = save_scan(networks, conn, link, os.path.join(BASE, "data"))
    result = generate_analysis(data)
    out_path = path.replace("scan_", "analysis_")
    import json
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    mc = result['summary']['my_connection']
    print(f"\x1b[32m[+] Analysis complete\x1b[0m")
    print(f"    Total APs: {result['summary']['total_aps']}")
    print(f"    Your signal: {mc['signal_dbm']} dBm ({mc['signal_quality']}%)")
    print(f"    Link speed: {mc['rx_mbps']:.0f} rx / {mc['tx_mbps']:.0f} tx Mbps")
    print(f"    Users on your AP: {mc['stations_on_ap']}")
    print(f"    Channel utilization: {mc['channel_util']}/255")
    if result['issues']:
        print(f"\x1b[33m[!] Issues found:\x1b[0m")
        for i in result['issues']:
            icon = "\x1b[31m✗" if i['severity'] == 'critical' else "\x1b[33m!" if i['severity'] == 'warning' else "\x1b[32mi"
            print(f"    {icon} {i['message']}\x1b[0m")
    print(f"\x1b[36m[~] Best 5GHz: ch{result['optimal_channels']['best_5ghz']}\x1b[0m")
    print(f"    Best 2.4GHz: ch{result['optimal_channels']['best_2_4ghz']}")
    return result

def cmd_speed():
    from speedtest import run_full_test
    print("\x1b[33m[*] Running speed tests...\x1b[0m")
    return run_full_test()

def cmd_report():
    from report import generate_html
    print("\x1b[33m[*] Generating HTML report...\x1b[0m")
    path = generate_html()
    print(f"\x1b[32m[+] Report generated: {path}\x1b[0m")
    print(f"    Open: file://{path}")
    return path

def cmd_monitor(duration=30, interval=2):
    print(f"\x1b[33m[*] Monitoring signal for {duration}s (every {interval}s)...\x1b[0m")
    print(f"    {'Time':<10} {'Signal':>8} {'Quality':>8} {'RX Rate':>10} {'Status'}")
    print("    " + "-" * 55)
    start = time.time()
    while time.time() - start < duration:
        link = get_link_stats()
        sig_val = link.get("signal")
        rx = link.get("rx_rate", 0)
        elapsed = time.time() - start
        t = time.strftime("%H:%M:%S")
        if sig_val:
            q = max(0, min(100, 100 + sig_val))
            color = "\x1b[32m" if sig_val >= -60 else "\x1b[33m" if sig_val >= -73 else "\x1b[31m"
            status = "EXCELLENT" if sig_val >= -50 else "GOOD" if sig_val >= -60 else "FAIR" if sig_val >= -70 else "WEAK" if sig_val >= -80 else "BAD"
            print(f"    {t:<10} {sig_val:>7.0f}dBm {q:>6.0f}% {rx or 0:>8.0f}M {color}{status}\x1b[0m")
        else:
            print(f"    {t:<10} {'DISCONNECTED':>10}")
        time.sleep(interval)
    print("\x1b[32m[+] Monitoring complete\x1b[0m")

def cmd_best_ap():
    from utils import scan_networks as do_scan, get_current_connection
    print("\x1b[33m[*] Finding best AP...\x1b[0m")
    aps = do_scan()

    active = get_active_ssid() or ""
    secure = [a for a in aps if a.get("ssid") == active]

    for a in secure:
        sig = a.get("signal_dbm", -100)
        sta = a.get("stations", 0)
        ut = a.get("channel_util", 0)
        sig_score = max(0, 100 + sig)
        a['score'] = sig_score - (ut / 2.55) - (sta * 2)

    secure.sort(key=lambda x: x.get('score', -999), reverse=True)

    conn = get_current_connection()
    my_bssid = conn.get("bssid", "")

    print(f"\n    {'RANK':<5} {'BSSID':<20} {'Band':<5} {'Signal':>8} {'Score':>6} {'Status'}")
    print("    " + "-" * 60)
    for i, a in enumerate(secure[:10]):
        marker = " \x1b[33m<<< YOU\x1b[0m" if a.get('bssid', '') == my_bssid else ""
        color = "\x1b[32m" if a.get('score',0) > 40 else "\x1b[33m" if a.get('score',0) > 20 else "\x1b[31m"
        print(f"    {i+1:<5} {a['bssid']:<20} {a.get('band','?'):<5} {a.get('signal_dbm',0):>7.0f}dBm {color}{a.get('score',0):>5.0f}\x1b[0m{marker}")

    if secure:
        best = secure[0]
        print(f"\n    \x1b[32m[+] Best AP: {best['bssid']} ({best.get('band')}, {best.get('signal_dbm',0):.0f} dBm, score {best.get('score',0):.0f})\x1b[0m")
        if best['bssid'] != my_bssid:
            print(f"    \x1b[33m[!] You're NOT on the best AP.\x1b[0m")
        else:
            print(f"    \x1b[32m[+] You're already on the best AP!\x1b[0m")
    return secure

def cmd_full():
    banner()
    print("\x1b[36mRunning full diagnostic suite...\x1b[0m\n")
    cmd_scan()
    print()
    cmd_best_ap()
    print()
    cmd_analyze()
    print()
    cmd_speed()
    print()
    path = cmd_report()
    print(f"\n\x1b[32m{'='*60}")
    print(f"  ALL DONE! Open the report:")
    print(f"  file://{path}")
    print(f"{'='*60}\x1b[0m")
    try:
        import platform
        if platform.system() == "Darwin":
            subprocess.Popen(["open", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif platform.system() == "Windows":
            os.startfile(path)
        else:
            subprocess.Popen(["xdg-open", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        pass

def main():
    banner()
    check_dependencies()
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "scan": cmd_scan()
        elif cmd == "analyze": cmd_analyze()
        elif cmd == "speed": cmd_speed()
        elif cmd == "report": cmd_report()
        elif cmd == "monitor": cmd_monitor(int(sys.argv[2]) if len(sys.argv)>2 else 30, int(sys.argv[3]) if len(sys.argv)>3 else 2)
        elif cmd == "best": cmd_best_ap()
        elif cmd == "full": cmd_full()
        else: print(f"Unknown command: {cmd}")
    else:
        print("Usage: python3 run.py [command]")
        print("\nCommands:")
        print("  scan      - Scan all WiFi networks")
        print("  analyze   - Full channel congestion analysis")
        print("  speed     - Run speed tests")
        print("  report    - Generate HTML report")
        print("  monitor   - Real-time signal monitor [duration] [interval]")
        print("  best      - Find the best AP and compare")
        print("  full      - Run everything and generate report")

if __name__ == "__main__":
    main()
