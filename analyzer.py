#!/usr/bin/env python3
import json, os, glob, subprocess, re
from datetime import datetime
from collections import defaultdict

def analyze_channels(networks):
    ch_data = defaultdict(lambda: {"networks": [], "stations": 0, "util": 0, "band": "", "max_signal": -100})
    for n in networks:
        ch = n.get("channel", 0)
        if ch == 0:
            continue
        band = n.get("band", "")
        key = f"{band}_{ch}"
        ch_data[key]["networks"].append(n)
        ch_data[key]["band"] = band
        ch_data[key]["stations"] += n.get("stations", 0)
        ch_data[key]["util"] = max(ch_data[key]["util"], n.get("channel_util", 0))
        if n.get("signal_dbm", -100) > ch_data[key]["max_signal"]:
            ch_data[key]["max_signal"] = n["signal_dbm"]
    return dict(ch_data)

def analyze_congestion(ch_data):
    issues = []
    ch24 = {k: v for k, v in ch_data.items() if "2.4GHz" in k}
    ch5 = {k: v for k, v in ch_data.items() if "5GHz" in k}

    for key, data in sorted(ch24.items()):
        net_count = len(data["networks"])
        if net_count >= 5:
            issues.append({
                "severity": "critical",
                "channel": key,
                "message": f"Channel {key.split('_')[1]} ({data['band']}): {net_count} APs competing — severe congestion"
            })
        elif net_count >= 3:
            issues.append({
                "severity": "warning",
                "channel": key,
                "message": f"Channel {key.split('_')[1]} ({data['band']}): {net_count} APs — moderate congestion"
            })
        if data["util"] > 150:
            issues.append({
                "severity": "critical",
                "channel": key,
                "message": f"Channel {key.split('_')[1]}: utilization {data['util']}/255 ({data['util']*100//255}%) — extremely busy"
            })
        elif data["util"] > 80:
            issues.append({
                "severity": "warning",
                "channel": key,
                "message": f"Channel {key.split('_')[1]}: utilization {data['util']}/255 ({data['util']*100//255}%) — moderately busy"
            })

    secure_nets = [n for n in sum([d["networks"] for d in ch_data.values()], []) if n.get("ssid") == "Secure Network"]
    my_nets = [n for n in secure_nets if n.get("is_mine")]
    other_secure = [n for n in secure_nets if not n.get("is_mine")]

    if my_nets:
        my_ch = my_nets[0].get("channel", 0)
        same_ch = [n for n in other_secure if n.get("channel") == my_ch]
        if same_ch:
            issues.append({
                "severity": "info",
                "channel": f"2.4GHz_{my_ch}" if my_nets[0].get("band") == "2.4GHz" else f"5GHz_{my_ch}",
                "message": f"{len(same_ch)} other Secure Network APs on same channel — sharing airtime"
            })

    return issues

def get_optimal_channel(ch_data):
    score_24 = {}
    for ch_num in [1, 6, 11]:
        key = f"2.4GHz_{ch_num}"
        data = ch_data.get(key, {"networks": [], "stations": 0, "util": 0})
        score = len(data["networks"]) * 10 + data["stations"] + data["util"] // 5
        score_24[ch_num] = score

    score_5 = {}
    for key, data in ch_data.items():
        if "5GHz" not in key:
            continue
        parts = key.split("_")
        ch_num = int(parts[1])
        score = len(data["networks"]) * 10 + data["stations"] + data["util"] // 5
        score_5[ch_num] = score

    best_24 = min(score_24, key=score_24.get) if score_24 else None
    best_5 = min(score_5, key=score_5.get) if score_5 else None

    return {
        "best_2_4ghz": best_24,
        "best_2_4ghz_score": score_24.get(best_24, 0) if best_24 else None,
        "best_5ghz": best_5,
        "best_5ghz_score": score_5.get(best_5, 0) if best_5 else None,
        "all_2_4_scores": score_24,
        "all_5_scores": score_5,
    }

def signal_to_quality(dbm):
    if dbm >= -50: return 100
    if dbm >= -60: return 85
    if dbm >= -67: return 70
    if dbm >= -73: return 55
    if dbm >= -80: return 35
    if dbm >= -90: return 15
    return 5

def generate_analysis(data):
    networks = data.get("networks", [])
    conn = data.get("connection", {})
    link = data.get("link_stats", {})

    ch_data = analyze_channels(networks)
    issues = analyze_congestion(ch_data)
    optimal = get_optimal_channel(ch_data)

    secure_24 = [n for n in networks if n.get("ssid") == "Secure Network" and n.get("band") == "2.4GHz"]
    secure_5 = [n for n in networks if n.get("ssid") == "Secure Network" and n.get("band") == "5GHz"]
    my_net = [n for n in networks if n.get("is_mine")]

    analysis = {
        "timestamp": datetime.now().isoformat(),
        "channel_analysis": ch_data,
        "issues": issues,
        "optimal_channels": optimal,
        "summary": {
            "total_aps": len(networks),
            "total_stations": sum(n.get("stations", 0) for n in networks),
            "secure_networks_2_4": len(secure_24),
            "secure_networks_5": len(secure_5),
            "my_connection": {
                "bssid": conn.get("bssid", "N/A"),
                "signal_dbm": conn.get("signal_dbm", 0),
                "signal_quality": signal_to_quality(conn.get("signal_dbm", -80)),
                "rx_mbps": link.get("rx_rate", 0),
                "tx_mbps": link.get("tx_rate", 0),
                "channel": my_net[0].get("channel", 0) if my_net else 0,
                "band": my_net[0].get("band", "?") if my_net else "?",
                "channel_util": my_net[0].get("channel_util", 0) if my_net else 0,
                "stations_on_ap": my_net[0].get("stations", 0) if my_net else 0,
            }
        }
    }
    return analysis

if __name__ == "__main__":
    import sys
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    files = sorted(glob.glob(os.path.join(data_dir, "scan_*.json")))
    if not files:
        print("No scan data found. Run scanner.py first.")
        sys.exit(1)

    with open(files[-1]) as f:
        data = json.load(f)

    result = generate_analysis(data)
    out_path = files[-1].replace("scan_", "analysis_")
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\n=== NETWORK ANALYSIS ===")
    print(f"Total APs: {result['summary']['total_aps']}")
    print(f"Secure Network APs: {result['summary']['secure_networks_2_4']} (2.4GHz) + {result['summary']['secure_networks_5']} (5GHz)")
    print(f"Total stations: {result['summary']['total_stations']}")
    print(f"\nYour connection:")
    mc = result['summary']['my_connection']
    print(f"  BSSID: {mc['bssid']}")
    print(f"  Signal: {mc['signal_dbm']} dBm (quality: {mc['signal_quality']}%)")
    print(f"  Speed: {mc['rx_mbps']} Mbps rx / {mc['tx_mbps']} Mbps tx")
    print(f"  Channel: {mc['channel']} ({mc['band']})")
    print(f"  Users on AP: {mc['stations_on_ap']}")
    print(f"  Channel utilization: {mc['channel_util']}/255 ({mc['channel_util']*100//255}%)")

    if result['issues']:
        print(f"\n=== ISSUES ({len(result['issues'])}) ===")
        for i in result['issues']:
            print(f"  [{i['severity'].upper()}] {i['message']}")

    print(f"\n=== OPTIMAL CHANNELS ===")
    opt = result['optimal_channels']
    print(f"  2.4GHz: Channel {opt['best_2_4ghz']} (score: {opt['best_2_4ghz_score']})")
    print(f"  5GHz:   Channel {opt['best_5ghz']} (score: {opt['best_5ghz_score']})")

    print(f"\nSaved to {out_path}")
