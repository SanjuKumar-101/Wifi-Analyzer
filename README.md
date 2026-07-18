# WiFi Analyzer

WiFi diagnostic toolkit for analyzing campus/university networks. Scans access points, analyzes channel congestion, tracks speed history, and generates professional HTML reports with visualizations.

## Features

- **AP Scanner** — Discovers all access points with signal strength, channel, band, and BSS load data
- **Channel Congestion Analyzer** — Identifies the least congested channel with interference mapping
- **Speed Test Tracker** — Logs download/upload speeds, latency, and jitter over time
- **Real-time Monitor** — Live signal strength watch with continuous updates
- **HTML Report Generator** — Interactive charts (Chart.js) for signal, speed, channel utilization, and AP comparison
- **Best AP Ranker** — Ranks all APs by signal quality + congestion score

## Requirements

- Linux with `iw`, `nmcli`, `speedtest-cli` (optional)
- Python 3.10+
- Root/sudo access for WiFi scanning (`iw scan`)

## Usage

```bash
# Quick launcher
./wifi-diag scan        # Scan all APs
./wifi-diag best        # Rank APs by signal + congestion
./wifi-diag analyze     # Channel congestion analysis
./wifi-diag speed       # Run speed test with history
./wifi-diag monitor     # Real-time signal monitor
./wifi-diag report      # Generate HTML report
./wifi-diag full        # Run everything
```

Or run individual scripts directly:

```bash
python3 scanner.py      # Scan networks
python3 analyzer.py     # Analyze channels
python3 speedtest.py    # Speed test
python3 report.py       # Generate report
python3 run.py full     # Run all
```

## Report Preview

The HTML report includes:
- Live signal strength and link speed
- Speed history over time (line chart)
- AP signal comparison (bar chart)
- Channel congestion (bar chart with utilization overlay)
- All detected Secure Network APs table

## License

MIT
