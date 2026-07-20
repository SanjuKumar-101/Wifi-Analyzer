#!/bin/bash
# WiFi Keepalive — runs via cron, no loops
# Best AP: 78:9F:6A:89:D6:B1 (ch149, 5GHz) — 26 Mbps, 0% loss
# Static IP: 10.65.31.199/19, GW: 10.65.0.1, DNS: 1.1.1.1

IFACE="wlp0s20f3"
PROFILE="Secure Network"
BEST_AP="78:9F:6A:89:D6:B1"
STATIC_IP="10.65.31.199/19"
STATIC_GW="10.65.0.1"
STATIC_DNS="1.1.1.1 8.8.8.8"
LOCK="/tmp/wifi-keepalive.lock"
LOG="/tmp/wifi-keepalive.log"

# Prevent concurrent runs
if [ -f "$LOCK" ]; then
    PID=$(cat "$LOCK")
    if kill -0 "$PID" 2>/dev/null; then
        exit 0
    fi
fi
echo $$ > "$LOCK"
trap "rm -f $LOCK" EXIT

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" >> "$LOG"
    tail -50 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
}

is_connected() {
    iw dev "$IFACE" link 2>/dev/null | grep -q "^.*Connected to"
}

has_ip() {
    ip addr show "$IFACE" 2>/dev/null | grep -q "inet 10\."
}

ping_ok() {
    ping -c 1 -W 3 1.1.1.1 &>/dev/null
}

# Already good
if is_connected && has_ip && ping_ok; then
    exit 0
fi

log "WiFi issue detected. Connected=$(is_connected) IP=$(has_ip)"

# Try DHCP first (works outside hostel)
if ! is_connected; then
    nmcli connection up "$PROFILE" &>/dev/null
    sleep 8
fi

# If connected but no IP, try DHCP
if is_connected && ! has_ip; then
    log "No IP — trying DHCP release/renew"
    sudo dhclient -r "$IFACE" 2>/dev/null
    sudo dhclient "$IFACE" 2>/dev/null
    sleep 5
fi

# Still no IP — apply static (hostel room fix)
if is_connected && ! has_ip; then
    log "DHCP failed — applying static IP"
    nmcli connection modify "$PROFILE" ipv4.method manual \
        ipv4.addresses "$STATIC_IP" \
        ipv4.gateway "$STATIC_GW" \
        ipv4.dns "$STATIC_DNS" 2>/dev/null
    nmcli connection up "$PROFILE" &>/dev/null
    sleep 5
fi

# Final check
if is_connected && has_ip && ping_ok; then
    log "WiFi restored"
else
    log "WiFi restore FAILED — manual intervention needed"
fi
