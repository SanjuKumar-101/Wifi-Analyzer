<p align="center">
  <br/>
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black" alt="Linux"/>
  <img src="https://img.shields.io/badge/macOS-000000?style=for-the-badge&logo=apple&logoColor=white" alt="macOS"/>
  <img src="https://img.shields.io/badge/Windows-0078D4?style=for-the-badge&logo=windows&logoColor=white" alt="Windows"/>
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License"/>
</p>

<h1 align="center">
  <br/>
  <img src="https://raw.githubusercontent.com/AnilDaum/awesome-wifi-analyzer/main/assets/wifi-signal.svg" width="120" alt="WiFi Signal" onerror="this.style.display='none'"/>
  <br/>
  WiFi Analyzer
  <br/>
</h1>

<h4 align="center">Cross-platform WiFi diagnostic toolkit for campus and enterprise networks</h4>

<p align="center">
  <a href="#-features">Features</a> &bull;
  <a href="#-quick-start">Quick Start</a> &bull;
  <a href="#-commands">Commands</a> &bull;
  <a href="#-report-preview">Report</a> &bull;
  <a href="#-how-it-works">How It Works</a>
</p>

<br/>

<div align="center">

```
 ██████╗ ██╗    ██╗██╗███████╗██╗    ███████╗ ██████╗ █████╗ ███╗   ██╗
██╔════╝ ██║    ██║██║██╔════╝██║    ██╔════╝██╔════╝██╔══██╗████╗  ██║
██║  ███╗██║ █╗ ██║██║█████╗  ██║    ███████╗██║     ███████║██╔██╗ ██║
██║   ██║██║███╗██║██║██╔══╝  ██║    ╚════██║██║     ██╔══██║██║╚██╗██║
╚██████╔╝╚███╔███╔╝██║██║     ██║    ███████║╚██████╗██║  ██║██║ ╚████║
 ╚═════╝  ╚══╝╚══╝ ╚═╝╚═╝     ╚═╝    ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝
```

![Signal Scan](https://img.shields.io/badge/Signal-Scan-00ff00?style=flat-square&labelColor=0d1117)
![Speed Test](https://img.shields.io/badge/Speed-Test-00d4ff?style=flat-square&labelColor=0d1117)
![Report](https://img.shields.io/badge/HTML-Report-ff6b6b?style=flat-square&labelColor=0d1117)
![Monitor](https://img.shields.io/badge/Live-Monitor-ffd93d?style=flat-square&labelColor=0d1117)

</div>

<br/>

---

## The Problem

Campus WiFi sucks. Hundreds of APs fighting on the same channel, random disconnections, mysterious speed caps. Nobody knows **why** because nobody can **see** what's happening.

**This tool makes the invisible visible.**

<div align="center">

| Problem | What This Tool Does |
|:--------|:--------------------|
| "WiFi is slow" | Shows your actual link speed vs ISP cap |
| "Which AP should I use?" | Ranks every AP by signal + congestion score |
| "Why does it keep disconnecting?" | Detects power save, signal drops, auth failures |
| "Which channel is best?" | Maps every channel's congestion and utilization |

</div>

<br/>

---

## Features

<table>
<tr>
<td width="50%" valign="top">

### AP Scanner
Scans **100+ access points** in seconds. Gets signal strength, channel, band, security type, station count, and channel utilization data.

### Channel Analyzer  
Maps **channel congestion** across 2.4GHz and 5GHz bands. Identifies critical interference, recommends the least congested channel.

### Speed Tracker
Runs multi-server speed tests against **Cloudflare**. Logs download speed, latency, TCP stats. Tracks history over time.

</td>
<td width="50%" valign="top">

### Live Monitor
Real-time signal strength display with color-coded status. Watch for drops, interference patterns, and roaming events.

### HTML Report
Professional **dark-theme dashboard** with interactive Chart.js visualizations. Signal history, AP comparison, channel congestion charts.

### Best AP Finder
Ranks every AP by a **composite score**: signal strength minus congestion penalties. Shows if you're on the optimal AP.

</td>
</tr>
</table>

<br/>

---

## Quick Start

### Linux

```bash
git clone https://github.com/SanjuKumar-101/Wifi-Analyzer.git
cd Wifi-Analyzer
chmod +x wifi-diag
sudo ./wifi-diag full
```

### macOS

```bash
git clone https://github.com/SanjuKumar-101/Wifi-Analyzer.git
cd Wifi-Analyzer
chmod +x wifi-diag
python3 run.py full
```

### Windows

```powershell
git clone https://github.com/SanjuKumar-101/Wifi-Analyzer.git
cd Wifi-Analyzer
python run.py full
```

> **Note:** Linux requires `sudo` for WiFi scanning (`iw scan`). macOS and Windows don't need elevated privileges.

<br/>

---

## Commands

| Command | Description | What It Outputs |
|:--------|:------------|:----------------|
| `scan` | Scan all WiFi networks | Network list with signal, channel, band |
| `best` | Find best AP by signal + congestion | Ranked AP table with scores |
| `analyze` | Full channel congestion analysis | Channel map, interference issues, optimal channels |
| `speed` | Run speed tests | Download speed, latency, TCP stats |
| `monitor` | Real-time signal watch | Live signal strength with status |
| `report` | Generate HTML report | Interactive dashboard in browser |
| `full` | Run everything | Complete diagnostic suite |

```bash
# Monitor for 60 seconds, refresh every 3 seconds
sudo ./wifi-diag monitor 60 3
```

<br/>

---

## Report Preview

The generated HTML report is a **dark-themed dashboard** with:

<div align="center">

| Section | Visualization |
|:--------|:-------------|
| Signal Strength | Color-coded meter with quality % |
| Link Speed | RX/TX rates with MCS index |
| Power Save | Status indicator (ON/OFF) |
| Connected AP | BSSID, band, channel, state |
| Speed History | Line chart over time |
| AP Comparison | Horizontal bar chart |
| Channel Congestion | Grouped bar chart with utilization |
| AP Table | All detected APs with full details |
| Backhaul Analysis | ISP bottleneck investigation |

</div>

<br/>

---

## How It Works

### Signal Quality Scale

```
  -50 dBm  ████████████████████  100%  Excellent
  -60 dBm  ███████████████       85%   Good
  -67 dBm  █████████████         70%   Fair
  -73 dBm  ██████████            55%   Weak
  -80 dBm  ██████                35%   Bad
  -90 dBm  ██                    15%   Terrible
```

### AP Scoring Algorithm

Each AP is scored using:

```
score = signal_quality - (channel_utilization / 2.55) - (station_count * 2)
```

This accounts for both raw signal strength AND how busy the channel is. A strong AP with 20 clients on a saturated channel scores lower than a moderate AP with zero clients.

<br/>

---

## System Requirements

| Component | Linux | macOS | Windows |
|:----------|:------|:------|:--------|
| Python | 3.10+ | 3.10+ | 3.10+ |
| WiFi scan | `iw` (usually pre-installed) | `airport` (built-in) | `netsh` (built-in) |
| Speed test | `curl` (usually pre-installed) | `curl` (built-in) | `curl` (built-in) |
| Latency | `ping` (usually pre-installed) | `ping` (built-in) | `ping` (built-in) |
| Elevated privs | `sudo` needed for scan | Not needed | Not needed |

<br/>

---

## Contributing

1. Fork the repo
2. Create a branch (`git checkout -b feature/amazing`)
3. Commit (`git commit -m 'Add amazing feature'`)
4. Push (`git push origin feature/amazing`)
5. Open a Pull Request

<br/>

---

## License

Distributed under the MIT License. See `LICENSE` for more information.

<br/>

<div align="center">

**Built for campus networks that need better diagnostics**

![Star](https://img.shields.io/github/stars/SanjuKumar-101/Wifi-Analyzer?style=social)

</div>
