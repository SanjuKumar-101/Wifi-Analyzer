#!/bin/bash
# Smart WiFi connector: tries DHCP first, falls back to static if DHCP fails
# Usage: sudo ./smart-connect.sh

IFACE="wlp0s20f3"
STATIC_IP="10.65.30.200/19"
GATEWAY="10.65.0.1"
DNS="1.1.1.1,8.8.8.8"
TIMEOUT=40

echo "[*] Scanning for Secure Network..."
nmcli device wifi rescan 2>/dev/null
sleep 2

echo "[*] Disconnecting current connection..."
nmcli device disconnect "$IFACE" 2>/dev/null
sleep 2

echo "[*] Attempt 1: DHCP..."
nmcli connection modify "Secure Network" ipv4.method auto 2>/dev/null
nmcli connection up "Secure Network" 2>/dev/null &
PID=$!
sleep $TIMEOUT
kill $PID 2>/dev/null

if ping -c 2 -W 3 1.1.1.1 &>/dev/null; then
    echo "[+] DHCP worked! Internet is up."
    nmcli connection modify "Secure Network" connection.autoconnect yes 2>/dev/null
    exit 0
fi

echo "[-] DHCP failed. Attempt 2: Static IP..."
nmcli device disconnect "$IFACE" 2>/dev/null
sleep 2

nmcli connection modify "Secure Network" \
    ipv4.method manual \
    ipv4.addresses "$STATIC_IP" \
    ipv4.gateway "$GATEWAY" \
    ipv4.dns "$DNS" \
    2>/dev/null

nmcli connection up "Secure Network" 2>/dev/null &
PID=$!
sleep 20
kill $PID 2>/dev/null

if ping -c 2 -W 3 1.1.1.1 &>/dev/null; then
    echo "[+] Static IP worked! Internet is up."
    nmcli connection modify "Secure Network" connection.autoconnect yes 2>/dev/null
    exit 0
fi

echo "[-] Static IP failed. Attempt 3: Try other APs..."
nmcli device disconnect "$IFACE" 2>/dev/null
sleep 2

BEST_AP=$(nmcli -t -f BSSID,SSID,SIGNAL device wifi list 2>/dev/null | grep "Secure Network" | sort -t: -k3 -rn | head -1 | cut -d: -f1-6)

if [ -n "$BEST_AP" ]; then
    echo "[*] Trying AP: $BEST_AP"
    nmcli connection modify "Secure Network" \
        802-11-wireless.bssid "$BEST_AP" \
        ipv4.method auto \
        2>/dev/null
    nmcli connection up "Secure Network" 2>/dev/null &
    PID=$!
    sleep $TIMEOUT
    kill $PID 2>/dev/null

    if ping -c 2 -W 3 1.1.1.1 &>/dev/null; then
        echo "[+] AP switch worked! Internet is up."
        nmcli connection modify "Secure Network" 802-11-wireless.bssid "" 2>/dev/null
        nmcli connection modify "Secure Network" connection.autoconnect yes 2>/dev/null
        exit 0
    fi
fi

echo "[-] All attempts failed. Reverting to static IP..."
nmcli device disconnect "$IFACE" 2>/dev/null
sleep 2
nmcli connection modify "Secure Network" \
    802-11-wireless.bssid "" \
    ipv4.method manual \
    ipv4.addresses "$STATIC_IP" \
    ipv4.gateway "$GATEWAY" \
    ipv4.dns "$DNS" \
    2>/dev/null
nmcli connection up "Secure Network" 2>/dev/null
sleep 5

if ping -c 2 -W 3 1.1.1.1 &>/dev/null; then
    echo "[+] Fallback static IP connected."
else
    echo "[!] All failed. Falling back to It's Me..."
    nmcli connection up "It's Me" 2>/dev/null
fi
