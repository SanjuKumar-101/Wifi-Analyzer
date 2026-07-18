#!/usr/bin/env python3
import subprocess, re, os, sys, platform

OS = platform.system()

def run_cmd(cmd, timeout=10):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return subprocess.CompletedProcess(cmd, returncode=1, stdout="", stderr="")

def get_wifi_interface():
    if OS == "Linux":
        return _get_iface_linux()
    elif OS == "Darwin":
        return "en0"
    elif OS == "Windows":
        return _get_iface_win()
    return None


def _get_iface_win():
    try:
        r = run_cmd(["netsh", "wlan", "show", "interfaces"], timeout=5)
        for line in r.stdout.splitlines():
            if "Name" in line and ":" in line:
                name = line.split(":", 1)[1].strip()
                if name and "Wi-Fi" in name or "Wireless" in name or "wlan" in name.lower():
                    return name
        for line in r.stdout.splitlines():
            if "Name" in line and ":" in line:
                return line.split(":", 1)[1].strip()
    except:
        pass
    return None

def ping_host(host, count=5):
    if OS == "Windows":
        cmd = ["ping", "-n", str(count), "-w", "3000", host]
    else:
        cmd = ["ping", "-c", str(count), "-W", "3", host]
    return run_cmd(cmd, timeout=15)

def _get_iface_linux():
    try:
        r = run_cmd(["iw", "dev"], timeout=5)
        for line in r.stdout.splitlines():
            m = re.match(r"\s*Interface\s+(\S+)", line)
            if m:
                return m.group(1)
    except:
        pass
    try:
        r = run_cmd(["nmcli", "-t", "-f", "DEVICE,TYPE", "device"], timeout=5)
        for line in r.stdout.splitlines():
            parts = line.split(":")
            if len(parts) == 2 and parts[1] == "wifi":
                return parts[0]
    except:
        pass
    return None

def get_active_ssid():
    if OS == "Linux":
        return _get_active_ssid_linux()
    elif OS == "Darwin":
        return _get_active_ssid_mac()
    elif OS == "Windows":
        return _get_active_ssid_win()
    return None

def _get_active_ssid_linux():
    try:
        r = run_cmd(["nmcli", "-t", "-f", "ACTIVE,SSID", "device", "wifi", "list"], timeout=5)
        for line in r.stdout.splitlines():
            if line.startswith("yes:"):
                return line.split(":", 1)[1].strip()
    except:
        pass
    iface = get_wifi_interface()
    if iface:
        try:
            r = run_cmd(["iw", "dev", iface, "link"], timeout=5)
            for line in r.stdout.splitlines():
                if "SSID:" in line:
                    return line.split("SSID:", 1)[1].strip()
        except:
            pass
    return None

def _get_active_ssid_mac():
    try:
        r = run_cmd(["networksetup", "-getairportnetwork", "en0"], timeout=5)
        if "You are not associated" not in r.stdout:
            return r.stdout.strip().split("Current Wi-Fi Network: ")[-1].strip()
    except:
        pass
    return None

def _get_active_ssid_win():
    try:
        r = run_cmd(["netsh", "wlan", "show", "interfaces"], timeout=5)
        for line in r.stdout.splitlines():
            if "SSID" in line and "BSSID" not in line:
                return line.split(":", 1)[1].strip()
    except:
        pass
    return None

def scan_networks():
    if OS == "Linux":
        return _scan_linux()
    elif OS == "Darwin":
        return _scan_mac()
    elif OS == "Windows":
        return _scan_win()
    return []

def _scan_linux():
    iface = get_wifi_interface()
    if not iface:
        print("No WiFi interface found", file=sys.stderr)
        return []
    result = run_cmd(["iw", "dev", iface, "scan"], timeout=30)
    if result.returncode != 0:
        nm_result = run_cmd(["nmcli", "dev", "wifi", "list"], timeout=15)
        if nm_result.returncode == 0 and nm_result.stdout.strip():
            return _parse_nmcli_scan(nm_result.stdout)
        print(f"Scan failed: {result.stderr.strip()}", file=sys.stderr)
        return []
    return _parse_iw_scan(result.stdout)

def _parse_nmcli_scan(output):
    networks = []
    lines = output.strip().splitlines()
    if len(lines) < 2:
        return []
    for line in lines[1:]:
        parts = line.split()
        if len(parts) < 6:
            continue
        ssid = parts[0]
        signal_pct = 0
        channel = 0
        bssid = ""
        security = "Open"
        for i, p in enumerate(parts):
            if p.endswith("dBm"):
                try: signal_pct = int(parts[i-1])
                except: pass
            elif p == "CH:":

                try: channel = int(parts[i+1])
                except: pass
            elif ":" in p and len(p) == 17 and p.count(":") == 5:
                bssid = p.upper()
            elif "WPA2" in p or "WPA" in p:
                security = "WPA2"
            elif "802.1X" in p or "WPA1" in p:
                security = "WPA2-Enterprise"
        signal_dbm = -100 + signal_pct if signal_pct else -100
        band = "2.4GHz" if channel <= 14 else "5GHz"
        freq = 2412 if channel <= 14 else 5180 + (channel - 36) * 5
        networks.append({
            "bssid": bssid or f"unknown".upper(), "ssid": ssid, "signal_dbm": signal_dbm,
            "channel": channel, "band": band, "frequency": freq,
            "security": security, "stations": 0, "channel_util": 0, "is_mine": False,
        })
    return networks

def _parse_iw_scan(output):
    networks = []
    current = {}
    for line in output.splitlines():
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
            if m: current["signal_dbm"] = float(m.group(1))
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
                    if freq >= 5745: current["channel"] = 149 + int((freq - 5745) / 5)
                    elif freq >= 5500: current["channel"] = 100 + int((freq - 5500) / 5)
                    elif freq >= 5260: current["channel"] = 52 + int((freq - 5260) / 5)
                    elif freq >= 5180: current["channel"] = 36 + int((freq - 5180) / 5)
                    else: current["channel"] = int((freq - 5000) / 5)
        elif "DS Parameter set:" in line:
            m = re.search(r"channel\s+(\d+)", line)
            if m: current["channel"] = int(m.group(1))
        elif "station count:" in line:
            m = re.search(r"station count:\s*(\d+)", line)
            if m: current["stations"] = int(m.group(1))
        elif "channel utilisation:" in line:
            m = re.search(r"channel utilisation:\s*(\d+)/255", line)
            if m: current["channel_util"] = int(m.group(1))
        elif "capability:" in line and "ESS" in line:
            current["type"] = "Infrastructure"
        elif "WPA:" in line or "RSN:" in line:
            current["security"] = "WPA2" if "WPA" in line else "WPA2/WPA3"
        elif "802.1X" in line or "key_mgmt" in line:
            current["enterprise"] = True
            current["security"] = "WPA2-Enterprise"
    if current:
        networks.append(current)
    for n in networks:
        n.setdefault("ssid", "(hidden)")
        n.setdefault("signal_dbm", -100)
        n.setdefault("channel", 0)
        n.setdefault("band", "unknown")
        n.setdefault("security", "Open")
        n["is_mine"] = False
    return networks

def _scan_mac():
    networks = []
    try:
        airport = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
        r = run_cmd([airport, "-s"], timeout=15)
        lines = r.stdout.strip().splitlines()
        if not lines:
            return []
        for line in lines[1:]:
            parts = line.split()
            if len(parts) < 6:
                continue
            ssid = parts[0]
            bssid = parts[1]
            try:
                signal = -int(parts[2].replace("-", ""))
            except:
                signal = -100
            try:
                channel = int(parts[3])
            except:
                channel = 0
            freq = 2412 if channel <= 14 else 5180 + (channel - 36) * 5
            band = "2.4GHz" if channel <= 14 else "5GHz"
            security = "Open"
            rest = " ".join(parts[4:])
            if "WPA2" in rest or "WPA" in rest:
                security = "WPA2"
            if "802.1X" in rest or "EAP" in rest:
                security = "WPA2-Enterprise"
            networks.append({
                "bssid": bssid.upper(), "ssid": ssid, "signal_dbm": signal,
                "channel": channel, "band": band, "frequency": freq,
                "security": security, "stations": 0, "channel_util": 0, "is_mine": False,
            })
    except Exception as e:
        print(f"Scan failed: {e}", file=sys.stderr)
    return networks

def _scan_win():
    networks = []
    try:
        r = run_cmd(["netsh", "wlan", "show", "networks", "mode=bssid"], timeout=15)
        current = {}
        for line in r.stdout.splitlines():
            line = line.strip()
            if line.startswith("SSID") and "BSSID" not in line:
                if current:
                    networks.append(current)
                ssid = line.split(":", 1)[1].strip()
                current = {"ssid": ssid, "stations": 0, "channel_util": 0, "band": "unknown", "channel": 0}
            elif "BSSID" in line:
                mac = line.split(":", 1)[1].strip()
                if current:
                    current["bssid"] = mac.upper()
            elif "Signal" in line:
                try:
                    pct = int(line.split(":", 1)[1].strip().replace("%", ""))
                    current["signal_dbm"] = -100 + pct
                except:
                    current["signal_dbm"] = -100
            elif "Channel" in line or "Freq" in line:
                try:
                    ch = int(line.split(":", 1)[1].strip())
                    current["channel"] = ch
                    current["band"] = "2.4GHz" if ch <= 14 else "5GHz"
                    current["frequency"] = 2412 if ch <= 14 else 5180 + (ch - 36) * 5
                except:
                    pass
            elif "Authentication" in line or "Encryption" in line:
                val = line.split(":", 1)[1].strip()
                if "WPA2" in val:
                    current["security"] = "WPA2"
                elif "Open" in val:
                    current["security"] = "Open"
        if current:
            networks.append(current)
        for n in networks:
            n.setdefault("bssid", "unknown".upper())
            n.setdefault("signal_dbm", -100)
            n.setdefault("security", "Open")
            n["is_mine"] = False
    except Exception as e:
        print(f"Scan failed: {e}", file=sys.stderr)
    return networks

def get_current_connection():
    if OS == "Linux":
        return _get_conn_linux()
    elif OS == "Darwin":
        return _get_conn_mac()
    elif OS == "Windows":
        return _get_conn_win()
    return {}

def _get_conn_linux():
    iface = get_wifi_interface()
    if not iface:
        return {}
    r = run_cmd(["iw", "dev", iface, "link"], timeout=5)
    info = {}
    for line in r.stdout.splitlines():
        if "Connected to" in line:
            m = re.search(r"([0-9a-f:]+)", line)
            if m:
                info["bssid"] = m.group(1).upper()
        elif "SSID:" in line:
            info["ssid"] = line.split("SSID:", 1)[1].strip()
        elif "freq:" in line:
            m = re.search(r"freq:\s*(\d+\.?\d*)", line)
            if m:
                freq = float(m.group(1))
                info["frequency"] = freq
                info["freq"] = freq
        elif "signal:" in line:
            m = re.search(r"signal:\s*(-?\d+\.?\d*)\s*dBm", line)
            if m:
                info["signal_dbm"] = float(m.group(1))
        elif "rx bitrate:" in line:
            m = re.search(r"(\d+\.?\d*)\s*MBit/s", line)
            if m:
                info["rx_mbps"] = float(m.group(1))
        elif "tx bitrate:" in line:
            m = re.search(r"(\d+\.?\d*)\s*MBit/s", line)
            if m:
                info["tx_mbps"] = float(m.group(1))
    if info.get("bssid"):
        info["state"] = "connected"
    return info

def _get_conn_mac():
    info = {}
    ssid = _get_active_ssid_mac()
    if ssid:
        info["ssid"] = ssid
    try:
        r = run_cmd(["ipconfig", "getifaddr", "en0"], timeout=5)
        if r.stdout.strip():
            info["ip"] = r.stdout.strip()
    except:
        pass
    try:
        iface = get_wifi_interface()
        if iface:
            r = run_cmd(["airport", "-I"], timeout=5)
            for line in r.stdout.splitlines():
                line = line.strip()
                if "channel" in line.lower():
                    m = re.search(r"channel:\s*(\d+)", line, re.IGNORECASE)
                    if m:
                        ch = int(m.group(1))
                        info["channel"] = ch
                        freq = 2412 if ch <= 14 else 5180 + (ch - 36) * 5
                        info["frequency"] = freq
                        info["freq"] = freq
    except:
        pass
    try:
        r = run_cmd(["networksetup", "-getairportnetwork", "en0"], timeout=5)
        if "You are not associated" not in r.stdout:
            info["state"] = "connected"
        else:
            info["state"] = "disconnected"
    except:
        pass
    return info

def _get_conn_win():
    info = {}
    try:
        r = run_cmd(["netsh", "wlan", "show", "interfaces"], timeout=5)
        for line in r.stdout.splitlines():
            line = line.strip()
            if "State" in line:
                info["state"] = line.split(":", 1)[1].strip().lower()
            elif "SSID" in line and "BSSID" not in line:
                info["ssid"] = line.split(":", 1)[1].strip()
            elif "BSSID" in line:
                info["bssid"] = line.split(":", 1)[1].strip().upper()
            elif "Signal" in line:
                try:
                    info["signal_quality"] = int(line.split(":", 1)[1].strip().replace("%", ""))
                    info["signal_dbm"] = -100 + info["signal_quality"]
                except:
                    pass
            elif "Receive" in line and "Rate" in line:
                try:
                    info["rx_mbps"] = float(line.split(":", 1)[1].strip().replace("Mbps", "").strip())
                except:
                    pass
            elif "Transmit" in line and "Rate" in line:
                try:
                    info["tx_mbps"] = float(line.split(":", 1)[1].strip().replace("Mbps", "").strip())
                except:
                    pass
            elif "Frequency" in line or "Channel" in line:
                try:
                    ch = int(line.split(":", 1)[1].strip())
                    info["channel"] = ch
                    freq = 2412 if ch <= 14 else 5180 + (ch - 36) * 5
                    info["frequency"] = freq
                    info["freq"] = freq
                except:
                    pass
    except:
        pass
    return info

def get_link_stats():
    if OS == "Linux":
        return _get_link_linux()
    elif OS == "Darwin":
        return _get_link_mac()
    elif OS == "Windows":
        return _get_link_win()
    return {}

def _get_link_linux():
    iface = get_wifi_interface()
    if not iface: return {}
    r = run_cmd(["iw", "dev", iface, "link"], timeout=5)
    info = {}
    for line in r.stdout.splitlines():
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

def _get_link_mac():
    info = {}
    try:
        r = run_cmd(["airport", "-I"], timeout=5)
        for line in r.stdout.splitlines():
            line = line.strip()
            if "agrCtlRSSI" in line:
                try: info["signal"] = float(line.split(":")[1].strip())
                except: pass
            elif "lastTxRate" in line:
                try: info["tx_rate"] = float(line.split(":")[1].strip().split()[0])
                except: pass
            elif "maxRate" in line:
                try: info["rx_rate"] = float(line.split(":")[1].strip().split()[0])
                except: pass
    except:
        pass
    return info

def _get_link_win():
    info = {}
    try:
        r = run_cmd(["netsh", "wlan", "show", "interfaces"], timeout=5)
        for line in r.stdout.splitlines():
            line = line.strip()
            if "Signal" in line:
                try:
                    pct = int(line.split(":", 1)[1].strip().replace("%", ""))
                    info["signal"] = -100 + pct
                except: pass
            elif "Receive" in line and "Rate" in line:
                try: info["rx_rate"] = float(line.split(":", 1)[1].strip().replace("Mbps", "").strip())
                except: pass
            elif "Transmit" in line and "Rate" in line:
                try: info["tx_rate"] = float(line.split(":", 1)[1].strip().replace("Mbps", "").strip())
                except: pass
    except:
        pass
    return info

def get_power_save():
    if OS == "Linux":
        iface = get_wifi_interface()
        if not iface:
            return True
        r = run_cmd(["iw", "dev", iface, "get", "power_save"], timeout=5)
        return "Power save: off" not in r.stdout
    elif OS == "Darwin":
        try:
            r = run_cmd(["networksetup", "-getairportpower", "en0"], timeout=5)
            return "on" in r.stdout.lower()
        except:
            return True
    return True

def get_gateway():
    try:
        if OS == "Linux":
            r = run_cmd(["ip", "route", "show", "default"], timeout=5)
            m = re.search(r"default via (\S+)", r.stdout)
            if m: return m.group(1)
        elif OS == "Darwin":
            r = run_cmd(["netstat", "-nr", "default"], timeout=5)
            for line in r.stdout.splitlines():
                if "default" in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        return parts[1]
        elif OS == "Windows":
            r = run_cmd(["ipconfig"], timeout=5)
            for line in r.stdout.splitlines():
                if "Default Gateway" in line and ":" in line:
                    gw = line.split(":", 1)[1].strip()
                    if gw and gw != "": return gw
    except:
        pass
    return None
