#!/usr/bin/env python3
import subprocess, re, json, os, sys
from datetime import datetime

def scan_networks():
    result = subprocess.run(
        ["iw", "dev", "wlp0s20f3", "scan"],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        print(f"Scan failed: {result.stderr}", file=sys.stderr)
        return []

    networks = []
    current = {}

    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("BSS "):
            if current:
                networks.append(current)
            mac = line.split()[1].rstrip(":")
            current = {"bssid": mac.upper(), "stations": 0, "channel_util": 0}
        elif "SSID:" in line:
            current["ssid"] = line.split("SSID:", 1)[1].strip()
        elif "signal:" in line:
            m = re.search(r"(-?\d+\.?\d*)\s*dBm", line)
            if m:
                current["signal_dbm"] = float(m.group(1))
        elif "freq:" in line:
            m = re.search(r"freq:\s*(\d+)", line)
            if m:
                freq = int(m.group(1))
                current["frequency"] = freq
                if freq < 3000:
                    current["band"] = "2.4GHz"
                    channels_24 = {2412:1,2417:2,2422:3,2427:4,2432:5,2437:6,2442:7,2447:8,2452:9,2457:10,2462:11}
                    current["channel"] = channels_24.get(freq, 0)
                else:
                    current["band"] = "5GHz"
                    if freq >= 5745:
                        current["channel"] = 149 + int((freq - 5745) / 5)
                    elif freq >= 5500:
                        current["channel"] = 100 + int((freq - 5500) / 5)
                    elif freq >= 5260:
                        current["channel"] = 52 + int((freq - 5260) / 5)
                    elif freq >= 5180:
                        current["channel"] = 36 + int((freq - 5180) / 5)
                    else:
                        current["channel"] = int((freq - 5000) / 5)
        elif "DS Parameter set:" in line:
            m = re.search(r"channel\s+(\d+)", line)
            if m:
                current["channel"] = int(m.group(1))
        elif "station count:" in line:
            m = re.search(r"station count:\s*(\d+)", line)
            if m:
                current["stations"] = int(m.group(1))
        elif "channel utilisation:" in line:
            m = re.search(r"channel utilisation:\s*(\d+)/255", line)
            if m:
                current["channel_util"] = int(m.group(1))
        elif "capability:" in line and "ESS" in line:
            current["type"] = "Infrastructure"
        elif "WPA:" in line or "RSN:" in line:
            if "WPA" in line:
                current["security"] = "WPA2"
            elif "RSN" in line:
                current["security"] = "WPA2/WPA3"
        elif "802.1X" in line or "key_mgmt" in line:
            current["enterprise"] = True
            current["security"] = "WPA2-Enterprise"

    if current:
        networks.append(current)

    for n in networks:
        if "ssid" not in n:
            n["ssid"] = "(hidden)"
        if "signal_dbm" not in n:
            n["signal_dbm"] = -100
        if "channel" not in n:
            n["channel"] = 0
        if "band" not in n:
            n["band"] = "unknown"
        if "security" not in n:
            n["security"] = "Open"
        if n["bssid"] in get_my_bssids():
            n["is_mine"] = True
        else:
            n["is_mine"] = False

    return networks

def get_my_bssids():
    result = subprocess.run(
        ["nmcli", "connection", "show", "Secure Network"],
        capture_output=True, text=True, timeout=5
    )
    bssids = set()
    for line in result.stdout.splitlines():
        if "seen-bssids" in line:
            for bssid in re.findall(r"([0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2})", line):
                bssids.add(bssid.upper())
    return bssids

def get_current_connection():
    result = subprocess.run(
        ["iw", "dev", "wlp0s20f3", "link"],
        capture_output=True, text=True, timeout=5
    )
    info = {}
    for line in result.stdout.splitlines():
        if "Connected to" in line:
            info["bssid"] = re.search(r"([0-9a-f:]+)", line).group(1).upper()
        elif "SSID:" in line:
            info["ssid"] = line.split("SSID:", 1)[1].strip()
        elif "freq:" in line:
            m = re.search(r"freq:\s*(\d+\.?\d*)", line)
            if m: info["frequency"] = float(m.group(1))
        elif "signal:" in line:
            m = re.search(r"signal:\s*(-?\d+\.?\d*)\s*dBm", line)
            if m: info["signal_dbm"] = float(m.group(1))
        elif "rx bitrate:" in line:
            m = re.search(r"(\d+\.?\d*)\s*MBit/s", line)
            if m: info["rx_mbps"] = float(m.group(1))
        elif "tx bitrate:" in line:
            m = re.search(r"(\d+\.?\d*)\s*MBit/s", line)
            if m: info["tx_mbps"] = float(m.group(1))
    return info

def get_link_stats():
    result = subprocess.run(
        ["iw", "dev", "wlp0s20f3", "link"],
        capture_output=True, text=True, timeout=5
    )
    info = {}
    for line in result.stdout.splitlines():
        if "signal:" in line:
            m = re.search(r"(-?\d+\.?\d*)\s*dBm", line)
            if m: info["signal"] = float(m.group(1))
        elif "rx bitrate:" in line:
            parts = line.strip()
            m = re.search(r"(\d+\.?\d*)\s*MBit/s", parts)
            if m: info["rx_rate"] = float(m.group(1))
            m2 = re.search(r"(\d+)MHz", parts)
            if m2: info["rx_width"] = int(m2.group(1))
            m3 = re.search(r"HE-MCS\s+(\d+)", parts)
            if m3: info["rx_mcs"] = int(m3.group(1))
        elif "tx bitrate:" in line:
            parts = line.strip()
            m = re.search(r"(\d+\.?\d*)\s*MBit/s", parts)
            if m: info["tx_rate"] = float(m.group(1))
            m2 = re.search(r"(\d+)MHz", parts)
            if m2: info["tx_width"] = int(m2.group(1))
            m3 = re.search(r"HE-MCS\s+(\d+)", parts)
            if m3: info["tx_mcs"] = int(m3.group(1))
    return info

def get_power_save():
    result = subprocess.run(
        ["iw", "dev", "wlp0s20f3", "get", "power_save"],
        capture_output=True, text=True, timeout=5
    )
    return "off" in result.stdout.lower()

def save_scan(networks, connection, link, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    data = {
        "timestamp": datetime.now().isoformat(),
        "connection": connection,
        "link_stats": link,
        "networks": networks,
        "network_count": len(networks),
        "secure_network_count": len([n for n in networks if n.get("ssid") == "Secure Network"]),
        "my_secure_networks": len([n for n in networks if n.get("ssid") == "Secure Network" and n.get("is_mine")]),
    }
    path = os.path.join(output_dir, f"scan_{timestamp}.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    return path, data

if __name__ == "__main__":
    outdir = os.path.join(os.path.dirname(__file__), "data")
    print("Scanning WiFi networks...")
    networks = scan_networks()
    conn = get_current_connection()
    link = get_link_stats()
    ps = get_power_save()
    print(f"Found {len(networks)} networks")
    print(f"Secure Networks: {len([n for n in networks if n.get('ssid') == 'Secure Network'])}")
    print(f"Connected: {conn.get('ssid','?')} at {conn.get('signal_dbm','?')} dBm")
    print(f"Power save: {'OFF' if ps else 'ON'}")
    path, data = save_scan(networks, conn, link, outdir)
    print(f"Saved to {path}")
