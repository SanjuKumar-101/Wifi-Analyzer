#!/usr/bin/env python3
import subprocess, re, json, os, sys
from datetime import datetime
from utils import scan_networks as do_scan, get_current_connection, get_link_stats, get_power_save, get_active_ssid, run_cmd

def scan_networks():
    networks = do_scan()
    active_ssid = get_active_ssid()
    for n in networks:
        if n.get("ssid") == active_ssid:
            n["is_mine"] = True
    return networks

def save_scan(networks, connection, link, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    active_ssid = get_active_ssid() or "unknown"
    data = {
        "timestamp": datetime.now().isoformat(),
        "connection": connection,
        "link_stats": link,
        "networks": networks,
        "network_count": len(networks),
        "secure_network_count": len([n for n in networks if n.get("ssid") == active_ssid]),
        "my_secure_networks": len([n for n in networks if n.get("ssid") == active_ssid and n.get("is_mine")]),
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
    active = get_active_ssid() or "unknown"
    print(f"Connected: {conn.get('ssid', active)} at {conn.get('signal_dbm', '?')} dBm")
    print(f"Power save: {'OFF' if ps else 'ON'}")
    path, data = save_scan(networks, conn, link, outdir)
    print(f"Saved to {path}")
