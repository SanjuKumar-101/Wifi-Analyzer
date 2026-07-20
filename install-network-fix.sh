#!/bin/bash
# Run this once to install all network fixes permanently
# sudo ./install-network-fix.sh

echo "[1/4] Creating self-healing dispatcher..."
cat > /tmp/99-secure-lock << 'DISPATCHER'
#!/bin/bash
INTERFACE=$1
ACTION=$2
SCRIPT_DIR="$(dirname "$(realpath "$0")")"
SMART_CONNECT="/home/savi/wifi-analyzer/smart-connect.sh"

if [ "$INTERFACE" != "wlp0s20f3" ]; then exit 0; fi

case "$ACTION" in
    up)
        iw dev "$INTERFACE" set power_save off 2>/dev/null
        SSID=$(nmcli -t -f GENERAL.CONNECTION device show "$INTERFACE" 2>/dev/null | cut -d: -f2)
        if [ "$SSID" != "Secure Network" ]; then
            sleep 3
            nmcli connection up "Secure Network" 2>/dev/null &
            sleep 30
            if ! ping -c 1 -W 3 1.1.1.1 &>/dev/null; then
                nmcli connection up "Secure Network" 2>/dev/null
            fi
        fi
        ;;
    down|disconnect)
        iw dev "$INTERFACE" set power_save off 2>/dev/null
        sleep 3
        nmcli connection up "Secure Network" 2>/dev/null &
        ;;
esac
DISPATCHER
sudo cp /tmp/99-secure-lock /etc/NetworkManager/dispatcher.d/99-secure-lock
sudo chmod +x /etc/NetworkManager/dispatcher.d/99-secure-lock
echo "  [+] Self-healing dispatcher installed"

echo "[2/4] Configuring Secure Network profile..."
nmcli connection modify "Secure Network" \
    connection.autoconnect yes \
    connection.autoconnect-priority 999 \
    connection.autoconnect-retries -1 \
    wifi.powersave 2 \
    wifi.band a \
    802-1x.auth-timeout 60 \
    ipv4.dns "1.1.1.1,8.8.8.8" \
    ipv4.dns-priority -1 \
    2>/dev/null
echo "  [+] Profile configured"

echo "[3/4] Disabling auto-connect on other networks..."
for conn in $(nmcli -t -f NAME connection show | grep -v "Secure Network" | grep -v "lo"); do
    nmcli connection modify "$conn" connection.autoconnect no 2>/dev/null
done
echo "  [+] Other networks disabled"

echo "[4/4] Setting iwlwifi to continuous active mode..."
echo 'options iwlmvm power_scheme=1' | sudo tee /etc/modprobe.d/iwlwifi-opt.conf > /dev/null
echo "  [+] Driver config set"

echo ""
echo "=== ALL DONE ==="
echo "Secure Network will now:"
echo "  - Auto-connect with priority 999"
echo "  - Reconnect automatically if it drops"
echo "  - Stay on 5GHz band"
echo "  - Power save always OFF"
echo ""
echo "If DHCP fails in a room, run:"
echo "  sudo /home/savi/wifi-analyzer/smart-connect.sh"
