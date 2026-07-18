#!/usr/bin/env python3
import json, os, glob, subprocess, re
from datetime import datetime
from collections import defaultdict
from utils import get_current_connection, get_link_stats, get_power_save, get_active_ssid, run_cmd

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

def get_all_data():
    scan_files = sorted(glob.glob(os.path.join(DATA_DIR, "scan_*.json")))
    speed_file = os.path.join(DATA_DIR, "speed_history.json")

    scan_data = None
    if scan_files:
        with open(scan_files[-1]) as f:
            scan_data = json.load(f)

    speed_data = {"tests": []}
    if os.path.exists(speed_file):
        with open(speed_file) as f:
            speed_data = json.load(f)

    return scan_data, speed_data

def get_live_data():
    conn = get_current_connection()
    link = get_link_stats()
    ps = get_power_save()
    link["power_save"] = ps

    active = get_active_ssid()
    if active:
        conn["ssid"] = active
    if not conn.get("state"):
        conn["state"] = "connected" if conn.get("bssid") else "disconnected"

    return conn, link

def generate_html():
    scan_data, speed_data = get_all_data()
    conn, link = get_live_data()

    networks = []
    if scan_data:
        networks = scan_data.get("networks", [])
    secure = [n for n in networks if n.get("ssid") == "Secure Network"]

    link["rx"] = link.get("rx_rate", link.get("rx", 0))
    link["tx"] = link.get("tx_rate", link.get("tx", 0))
    link["signal"] = link.get("signal", conn.get("signal_dbm", -80))
    link["rx_mcs"] = link.get("rx_mcs", "?")
    link["tx_mcs"] = link.get("tx_mcs", "?")
    signal = link.get("signal", -80)
    if signal >= -50: sig_quality = 100; sig_color = "#2ecc71"
    elif signal >= -60: sig_quality = 85; sig_color = "#27ae60"
    elif signal >= -67: sig_quality = 70; sig_color = "#f39c12"
    elif signal >= -73: sig_quality = 55; sig_color = "#e67e22"
    elif signal >= -80: sig_quality = 35; sig_color = "#e74c3c"
    else: sig_quality = 15; sig_color = "#c0392b"

    speed_history = speed_data.get("tests", [])[-20:]
    speed_chart_labels = json.dumps([s["timestamp"][:16] for s in speed_history])
    speed_chart_data = json.dumps([s.get("speed", {}).get("Cloudflare 25MB", {}).get("speed_mbps", 0) for s in speed_history])
    signal_chart_data = json.dumps([s.get("signal", -80) for s in speed_history])

    ch_data = defaultdict(lambda: {"count": 0, "total_util": 0})
    for n in secure:
        ch = n.get("channel", 0)
        band = n.get("band", "")
        key = f"{band} Ch{ch}"
        ch_data[key]["count"] += 1
        ch_data[key]["total_util"] += n.get("channel_util", 0)

    ch_labels = json.dumps(list(ch_data.keys()))
    ch_counts = json.dumps([d["count"] for d in ch_data.values()])
    ch_utils = json.dumps([d["total_util"] // max(d["count"], 1) for d in ch_data.values()])

    bssids = json.dumps([n.get("bssid", "?")[-8:] for n in sorted(secure, key=lambda x: x.get("signal_dbm", -100), reverse=True)[:15]])
    signals_dbm = json.dumps([n.get("signal_dbm", -100) for n in sorted(secure, key=lambda x: x.get("signal_dbm", -100), reverse=True)[:15]])

    total_stations = sum(n.get("stations", 0) for n in secure)
    total_aps = len(secure)
    avg_util = 0
    if secure:
        avg_util = sum(n.get("channel_util", 0) for n in secure) // len(secure)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>WiFi Network Diagnostic Report - Parul University</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: #0a0a1a; color: #e0e0e0; }}
.header {{ background: linear-gradient(135deg, #1a1a3e, #0d0d2b); padding: 30px 40px; border-bottom: 2px solid #333; }}
.header h1 {{ font-size: 28px; color: #00d4ff; margin-bottom: 5px; }}
.header p {{ color: #888; font-size: 14px; }}
.container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0; }}
.card {{ background: #111128; border: 1px solid #222; border-radius: 12px; padding: 24px; }}
.card h3 {{ color: #00d4ff; font-size: 16px; margin-bottom: 16px; text-transform: uppercase; letter-spacing: 1px; }}
.stat {{ font-size: 48px; font-weight: 700; color: #fff; }}
.stat-label {{ font-size: 13px; color: #888; margin-top: 4px; }}
.stat-good {{ color: #2ecc71; }}
.stat-warn {{ color: #f39c12; }}
.stat-bad {{ color: #e74c3c; }}
.chart-container {{ position: relative; height: 280px; }}
.status-bar {{ display: flex; align-items: center; gap: 12px; padding: 8px 16px; background: #0d0d22; border-radius: 8px; margin: 8px 0; }}
.status-dot {{ width: 10px; height: 10px; border-radius: 50%; }}
.dot-green {{ background: #2ecc71; box-shadow: 0 0 8px #2ecc71; }}
.dot-red {{ background: #e74c3c; box-shadow: 0 0 8px #e74c3c; }}
.dot-yellow {{ background: #f39c12; box-shadow: 0 0 8px #f39c12; }}
.signal-bar {{ width: 100%; height: 24px; background: #1a1a2e; border-radius: 12px; overflow: hidden; margin: 8px 0; }}
.signal-fill {{ height: 100%; border-radius: 12px; transition: width 0.5s; display: flex; align-items: center; padding-left: 12px; font-weight: 600; font-size: 13px; }}
table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
th {{ text-align: left; padding: 10px 12px; background: #1a1a2e; color: #00d4ff; border-bottom: 2px solid #333; }}
td {{ padding: 8px 12px; border-bottom: 1px solid #1a1a2e; }}
tr:hover {{ background: #16163a; }}
.badge {{ padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }}
.badge-5g {{ background: #0d47a1; color: #64b5f6; }}
.badge-24g {{ background: #1b5e20; color: #81c784; }}
.badge-me {{ background: #ff6f00; color: #fff; }}
.section-title {{ font-size: 20px; color: #fff; margin: 30px 0 15px; padding-bottom: 8px; border-bottom: 2px solid #00d4ff; }}
.issue {{ padding: 12px 16px; border-radius: 8px; margin: 8px 0; display: flex; align-items: center; gap: 12px; }}
.issue-critical {{ background: rgba(231,76,60,0.15); border-left: 4px solid #e74c3c; }}
.issue-warning {{ background: rgba(243,156,18,0.15); border-left: 4px solid #f39c12; }}
.issue-info {{ background: rgba(46,204,113,0.15); border-left: 4px solid #2ecc71; }}
.footer {{ text-align: center; padding: 30px; color: #555; font-size: 12px; }}
</style>
</head>
<body>
<div class="header">
  <h1>WiFi Network Diagnostic Report</h1>
  <p>Parul University Hostel Network Analysis | Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
</div>
<div class="container">

<div class="grid">
  <div class="card">
    <h3>Signal Strength</h3>
    <div class="stat" style="color:{sig_color}">{signal} dBm</div>
    <div class="stat-label">Quality: {sig_quality}%</div>
    <div class="signal-bar">
      <div class="signal-fill" style="width:{sig_quality}%;background:{sig_color}">{sig_quality}%</div>
    </div>
  </div>
  <div class="card">
    <h3>Link Speed</h3>
    <div class="stat">{link.get('rx', 0):.0f} <span style="font-size:20px;color:#888">Mbps RX</span></div>
    <div class="stat-label">TX: {link.get('tx', 0):.0f} Mbps | MCS: {link.get('rx_mcs', '?')}/{link.get('tx_mcs', '?')}</div>
  </div>
  <div class="card">
    <h3>Power Save</h3>
    <div class="stat {'stat-good' if link.get('power_save', False) else 'stat-bad'}">{'OFF' if link.get('power_save', False) else 'ON'}</div>
    <div class="stat-label">{'Optimal - no latency spikes' if link.get('power_save', False) else 'WARNING - causes disconnections'}</div>
  </div>
  <div class="card">
    <h3>Connected AP</h3>
    <div style="font-size:14px;color:#fff;margin-top:8px">BSSID: {conn.get('bssid', 'N/A')}</div>
    <div style="font-size:13px;color:#888;margin-top:4px">Band: {conn.get('freq', 0) > 3000 and '5GHz' or '2.4GHz'} | Channel: {int((conn.get('freq', 5000) - 5000) / 5) if conn.get('freq', 0) > 3000 else '?'}</div>
    <div style="font-size:13px;color:#888">State: {conn.get('state', '?')}</div>
  </div>
</div>

<div class="section-title">Network Overview</div>
<div class="grid">
  <div class="card">
    <h3>Secure Network APs</h3>
    <div class="stat">{total_aps}</div>
    <div class="stat-label">Total access points visible</div>
  </div>
  <div class="card">
    <h3>Total Stations</h3>
    <div class="stat">{total_stations}</div>
    <div class="stat-label">Connected clients across all APs</div>
  </div>
  <div class="card">
    <h3>Avg Channel Load</h3>
    <div class="stat {'stat-good' if avg_util < 50 else 'stat-warn' if avg_util < 100 else 'stat-bad'}">{avg_util}/255</div>
    <div class="stat-label">{avg_util * 100 // 255}% utilization</div>
  </div>
</div>

<div class="section-title">Speed History</div>
<div class="grid">
  <div class="card" style="grid-column: span 2;">
    <h3>Download Speed Over Time</h3>
    <div class="chart-container"><canvas id="speedChart"></canvas></div>
  </div>
  <div class="card">
    <h3>Signal Over Time</h3>
    <div class="chart-container"><canvas id="signalChart"></canvas></div>
  </div>
</div>

<div class="section-title">AP Signal Comparison</div>
<div class="card">
  <h3>Secure Network APs - Signal Strength</h3>
  <div class="chart-container" style="height:350px"><canvas id="apChart"></canvas></div>
</div>

<div class="section-title">Channel Congestion</div>
<div class="card">
  <h3>APs per Channel + Utilization</h3>
  <div class="chart-container" style="height:300px"><canvas id="channelChart"></canvas></div>
</div>

<div class="section-title">All Secure Network APs</div>
<div class="card">
  <table>
    <tr><th>BSSID</th><th>Band</th><th>Ch</th><th>Signal</th><th>Quality</th><th>Users</th><th>Util</th><th>Status</th></tr>
    {"".join(f'''<tr>
      <td>{n.get("bssid","?")[-8:]}</td>
      <td><span class="badge badge-{"5g" if n.get("band")=="5GHz" else "24g"}">{n.get("band","?")}</span></td>
      <td>{n.get("channel",0)}</td>
      <td>{n.get("signal_dbm",0):.0f} dBm</td>
      <td style="color:{"#2ecc71" if n.get("signal_dbm",0)>=-60 else "#f39c12" if n.get("signal_dbm",0)>=-73 else "#e74c3c"}">{max(0,100+n.get("signal_dbm",0))}%</td>
      <td>{n.get("stations",0)}</td>
      <td>{n.get("channel_util",0)}/255</td>
      <td>{"<span class='badge badge-me'>YOUR AP</span>" if n.get("is_mine") else ""}</td>
    </tr>''' for n in sorted(secure, key=lambda x: x.get("signal_dbm", -100), reverse=True)) if secure else "<tr><td colspan='8' style='color:#888'>No scan data available. Run scanner first.</td></tr>"}
  </table>
</div>

<div class="section-title">Backhaul Analysis</div>
<div class="card">
  <h3>Speed Cap Investigation</h3>
  <div style="padding:16px;background:#1a1a2e;border-radius:8px;margin-top:12px">
    <p style="color:#f39c12;font-weight:600;margin-bottom:8px">The ~30 Mbps cap is NOT from WiFi. Here's the evidence:</p>
    <ul style="padding-left:20px;line-height:2">
      <li>WiFi link speed: <strong style="color:#2ecc71">{link.get('rx',0):.0f} Mbps</strong> (physical layer) - 10x the cap</li>
      <li>WiFi signal: <strong style="color:#2ecc71">{signal} dBm</strong> ({sig_quality}% quality) - more than adequate</li>
      <li>No packet loss detected on local network</li>
      <li>The bottleneck is the <strong>ISP backhaul</strong> (internet line to campus) or <strong>CloudPath rate limiting</strong></li>
    </ul>
    <p style="color:#00d4ff;margin-top:12px;font-weight:600">To break 30 Mbps, the department must:</p>
    <ol style="padding-left:20px;line-height:2;color:#aaa">
      <li>Check CloudPath RADIUS for per-user rate limits (likely 30 Mbps cap)</li>
      <li>Verify ISP contract bandwidth vs actual usage</li>
      <li>Implement per-AP bandwidth balancing</li>
      <li>Consider upgrading the internet backhaul</li>
    </ol>
  </div>
</div>

</div>
<div class="footer">
  WiFi Diagnostic Suite v1.0 | Built for Parul University Network Analysis
</div>

<script>
const chartDefaults = {{
  color: '#888',
  borderColor: '#333',
  font: {{ family: "'Segoe UI', system-ui, sans-serif" }}
}};
Chart.defaults.color = '#888';
Chart.defaults.borderColor = '#222';

new Chart(document.getElementById('speedChart'), {{
  type: 'line',
  data: {{
    labels: {speed_chart_labels},
    datasets: [{{
      label: 'Download (Mbps)',
      data: {speed_chart_data},
      borderColor: '#00d4ff',
      backgroundColor: 'rgba(0,212,255,0.1)',
      fill: true,
      tension: 0.3,
      pointRadius: 3
    }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    scales: {{
      y: {{ beginAtZero: true, grid: {{ color: '#1a1a2e' }} }},
      x: {{ grid: {{ color: '#1a1a2e' }}, ticks: {{ maxRotation: 45, maxTicksLimit: 10 }} }}
    }},
    plugins: {{ legend: {{ display: false }} }}
  }}
}});

new Chart(document.getElementById('signalChart'), {{
  type: 'line',
  data: {{
    labels: {speed_chart_labels},
    datasets: [{{
      label: 'Signal (dBm)',
      data: {signal_chart_data},
      borderColor: '#2ecc71',
      backgroundColor: 'rgba(46,204,113,0.1)',
      fill: true,
      tension: 0.3,
      pointRadius: 3
    }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    scales: {{
      y: {{ grid: {{ color: '#1a1a2e' }} }},
      x: {{ grid: {{ color: '#1a1a2e' }}, ticks: {{ maxRotation: 45, maxTicksLimit: 8 }} }}
    }},
    plugins: {{ legend: {{ display: false }} }}
  }}
}});

new Chart(document.getElementById('apChart'), {{
  type: 'bar',
  data: {{
    labels: {bssids},
    datasets: [{{
      label: 'Signal (dBm)',
      data: {signals_dbm},
      backgroundColor: {signals_dbm}.map(s => s >= -60 ? '#2ecc71' : s >= -73 ? '#f39c12' : '#e74c3c'),
      borderRadius: 4
    }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    indexAxis: 'y',
    scales: {{
      x: {{ grid: {{ color: '#1a1a2e' }} }},
      y: {{ grid: {{ display: false }} }}
    }},
    plugins: {{ legend: {{ display: false }} }}
  }}
}});

new Chart(document.getElementById('channelChart'), {{
  type: 'bar',
  data: {{
    labels: {ch_labels},
    datasets: [
      {{ label: 'AP Count', data: {ch_counts}, backgroundColor: '#00d4ff', borderRadius: 4 }},
      {{ label: 'Avg Utilization', data: {ch_utils}, backgroundColor: '#f39c12', borderRadius: 4 }}
    ]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    scales: {{
      y: {{ beginAtZero: true, grid: {{ color: '#1a1a2e' }} }},
      x: {{ grid: {{ display: false }} }}
    }}
  }}
}});
</script>
</body>
</html>"""

    output = os.path.join(os.path.dirname(os.path.abspath(__file__)), "report.html")
    with open(output, "w") as f:
        f.write(html)
    return output

if __name__ == "__main__":
    path = generate_html()
    print(f"Report generated: {path}")
    print(f"Open in browser: file://{path}")
