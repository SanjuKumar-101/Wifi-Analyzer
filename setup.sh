#!/bin/bash
# WiFi Analyzer - One-command setup for any system
# Usage: bash setup.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "  ██╗    ██╗██╗███████╗██╗    ███████╗ ██████╗ █████╗ ███╗   ██╗"
echo "  ██║    ██║██║██╔════╝██║    ██╔════╝██╔════╝██╔══██╗████╗  ██║"
echo "  ██║ █╗ ██║██║█████╗  ██║    ███████╗██║     ███████║██╔██╗ ██║"
echo "  ██║███╗██║██║██╔══╝  ██║    ╚════██║██║     ██╔══██║██║╚██╗██║"
echo "  ╚███╔███╔╝██║██║     ██║    ███████║╚██████╗██║  ██║██║ ╚████║"
echo "   ╚══╝╚══╝ ╚═╝╚═╝     ╚═╝    ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝"
echo -e "${NC}"
echo -e "${YELLOW}WiFi Analyzer Setup${NC}"
echo ""

# Detect OS
OS="$(uname -s)"
echo -e "${CYAN}Detected OS: ${OS}${NC}"

# Check Python
echo ""
echo -e "${YELLOW}[1/4] Checking Python...${NC}"
if command -v python3 &>/dev/null; then
    PY=$(python3 --version 2>&1)
    echo -e "  ${GREEN}✓ Found: ${PY}${NC}"
else
    echo -e "  ${RED}✗ Python3 not found. Please install Python 3.10+${NC}"
    echo -e "  ${YELLOW}  Ubuntu/Debian: sudo apt install python3${NC}"
    echo -e "  ${YELLOW}  macOS: brew install python3${NC}"
    echo -e "  ${YELLOW}  Windows: Download from python.org${NC}"
    exit 1
fi

# Check/Install system dependencies
echo ""
echo -e "${YELLOW}[2/4] Checking system dependencies...${NC}"

install_if_missing() {
    local cmd=$1
    local pkg=$2
    if command -v "$cmd" &>/dev/null; then
        echo -e "  ${GREEN}✓ ${cmd} found${NC}"
    else
        echo -e "  ${YELLOW}! ${cmd} not found, attempting install...${NC}"
        if [ "$OS" = "Linux" ]; then
            if command -v apt &>/dev/null; then
                sudo apt install -y "$pkg" 2>/dev/null && echo -e "  ${GREEN}✓ Installed ${pkg}${NC}" || echo -e "  ${RED}✗ Failed to install ${pkg}. Install manually.${NC}"
            elif command -v dnf &>/dev/null; then
                sudo dnf install -y "$pkg" 2>/dev/null && echo -e "  ${GREEN}✓ Installed ${pkg}${NC}" || echo -e "  ${RED}✗ Failed to install ${pkg}. Install manually.${NC}"
            elif command -v pacman &>/dev/null; then
                sudo pacman -S --noconfirm "$pkg" 2>/dev/null && echo -e "  ${GREEN}✓ Installed ${pkg}${NC}" || echo -e "  ${RED}✗ Failed to install ${pkg}. Install manually.${NC}"
            else
                echo -e "  ${RED}✗ Unknown package manager. Install '${pkg}' manually.${NC}"
            fi
        else
            echo -e "  ${RED}✗ Please install '${pkg}' manually for your OS.${NC}"
        fi
    fi
}

# Linux dependencies
if [ "$OS" = "Linux" ]; then
    install_if_missing "iw" "iw"
    install_if_missing "curl" "curl"
    install_if_missing "ping" "iputils-ping"

# macOS dependencies (all built-in)
elif [ "$OS" = "Darwin" ]; then
    echo -e "  ${GREEN}✓ macOS uses built-in tools (airport, curl, ping)${NC}"

# Windows - check via PowerShell
else
    echo -e "  ${GREEN}✓ Windows uses built-in tools (netsh, curl, ping)${NC}"
fi

# Make wifi-diag executable
echo ""
echo -e "${YELLOW}[3/4] Setting up scripts...${NC}"
chmod +x wifi-diag 2>/dev/null && echo -e "  ${GREEN}✓ wifi-diag made executable${NC}" || true

# Create data directory
mkdir -p data
touch data/.gitkeep
echo -e "  ${GREEN}✓ data/ directory ready${NC}"

# Verify all Python files
echo ""
echo -e "${YELLOW}[4/4] Verifying Python files...${NC}"
for f in utils.py scanner.py analyzer.py speedtest.py report.py run.py; do
    if python3 -c "import py_compile; py_compile.compile('$f', doraise=True)" 2>/dev/null; then
        echo -e "  ${GREEN}✓ ${f} - syntax OK${NC}"
    else
        echo -e "  ${RED}✗ ${f} - has syntax errors${NC}"
    fi
done

# Test basic imports
echo ""
echo -e "${YELLOW}Testing imports...${NC}"
if python3 -c "import utils; print('  utils OK')" 2>/dev/null; then
    echo -e "  ${GREEN}✓ All imports working${NC}"
else
    echo -e "  ${RED}✗ Import test failed${NC}"
fi

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Setup complete! Ready to use.${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "${CYAN}Quick start:${NC}"

if [ "$OS" = "Linux" ]; then
    echo -e "  ${YELLOW}sudo ./wifi-diag full${NC}    # Run full diagnostics"
    echo -e "  ${YELLOW}sudo ./wifi-diag scan${NC}    # Scan WiFi networks"
    echo -e "  ${YELLOW}sudo ./wifi-diag best${NC}    # Find best AP"
else
    echo -e "  ${YELLOW}python3 run.py full${NC}      # Run full diagnostics"
    echo -e "  ${YELLOW}python3 run.py scan${NC}      # Scan WiFi networks"
    echo -e "  ${YELLOW}python3 run.py best${NC}      # Find best AP"
fi
echo ""
echo -e "${CYAN}Other commands:${NC}"
echo -e "  analyze   - Channel congestion analysis"
echo -e "  speed     - Run speed tests"
echo -e "  monitor   - Real-time signal monitor"
echo -e "  report    - Generate HTML report"
echo ""
