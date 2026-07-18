.PHONY: setup scan analyze speed report monitor best full clean help

PYTHON ?= python3
SUDO := $(shell command -v sudo >/dev/null 2>&1 && echo sudo || echo)
ECHO = @echo

help:
	$(ECHO) "WiFi Analyzer - Available commands:"
	$(ECHO) ""
	$(ECHO) "  make setup    - Install dependencies & verify project"
	$(ECHO) "  make scan     - Scan WiFi networks"
	$(ECHO) "  make analyze  - Channel congestion analysis"
	$(ECHO) "  make speed    - Run speed tests"
	$(ECHO) "  make report   - Generate HTML report"
	$(ECHO) "  make monitor  - Real-time signal monitor"
	$(ECHO) "  make best     - Find best access point"
	$(ECHO) "  make full     - Run complete diagnostic suite"
	$(ECHO) "  make clean    - Remove generated files"
	$(ECHO) ""
	$(ECHO) "  Override python: make full PYTHON=python3.12"

setup:
	bash setup.sh

scan:
	$(SUDO) $(PYTHON) run.py scan

analyze:
	$(SUDO) $(PYTHON) run.py analyze

speed:
	$(PYTHON) run.py speed

report:
	$(PYTHON) run.py report

monitor:
	$(SUDO) $(PYTHON) run.py monitor $(or $(DURATION),30) $(or $(INTERVAL),2)

best:
	$(SUDO) $(PYTHON) run.py best

full:
	$(SUDO) $(PYTHON) run.py full

clean:
	rm -rf __pycache__ data/scan_*.json data/analysis_*.json data/speed_history.json report.html
	$(ECHO) "Cleaned generated files"
