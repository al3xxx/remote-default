#!/bin/bash
#
# Remote Default Browser (Bash version)
# Opens URLs on a remote host via SSH instead of locally.
# Useful for headless servers without a GUI.
#

set -euo pipefail

# Config file loc
CFG="${XDG_CONFIG_HOME:-$HOME/.config}/remote-default/config"

# State
LOG_F=""
LOG_ON=false
LVL="INFO"

# Lvl map
declare -A LVLS=( ["DEBUG"]=0 ["INFO"]=1 ["WARNING"]=2 ["ERROR"]=3 ["CRITICAL"]=4 )

# SSH options
SSH_OPTS=(-o BatchMode=yes -o ConnectTimeout=10 -o ServerAliveInterval=5 -o ServerAliveCountMax=3)

# Log msg
log() {
    local l="$1" message="${*:2}"
    [[ "$LOG_ON" != "true" || -z "$LOG_F" ]] && return 0
    local cl="${LVLS[$LVL]:-1}" ml="${LVLS[$l]:-1}"
    [[ $ml -lt $cl ]] && return 0
    mkdir -p "$(dirname "$LOG_F")" 2>/dev/null
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $l - $message" >> "$LOG_F" 2>/dev/null
    [[ "$LVL" == "DEBUG" ]] && echo "$(date '+%Y-%m-%d %H:%M:%S') - $l - $message" >&2
}

# Err trap
err() { log "ERROR" "Failed at $1 with $?"; }
trap 'err $LINENO' ERR

# Load cfg
load() {
    HOST="" KEY="" BROW="xdg-open" LOG_ON=false LVL="INFO" LOG_F=""
    if [[ -f "$CFG" ]]; then
        while IFS='=' read -r k v; do
            [[ "$k" =~ ^#.*$ || -z "$k" ]] && continue
            v=$(echo "$v" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e 's/^["'\'']//' -e 's/["'\'']$//')
            case "$k" in
                remote_host) HOST="$v" ;;
                ssh_key) KEY="$v" ;;
                remote_browser) BROW="$v" ;;
                logging_enabled) [[ "$v" =~ ^(true|yes|1|on)$ ]] && LOG_ON=true || LOG_ON=false ;;
                log_level) LVL="${v^^}" ;;
                log_file) LOG_F="$v" ;;
            esac
        done < "$CFG"
    fi
    [[ "$LOG_ON" == "true" && -z "$LOG_F" ]] && LOG_F="$HOME/.local/share/remote-default/remote-default.log"
}

# Save cfg
save() {
    local h="$1" k="${2:-}" b="${3:-xdg-open}" o="${4:-false}" l="${5:-INFO}" f="${6:-}"
    mkdir -p "$(dirname "$CFG")"
    cat > "$CFG" <<EOF
remote_host=$h
ssh_key=$k
remote_browser=$b
logging_enabled=$o
log_level=${l^^}
log_file=$f
EOF
    echo "Saved: $CFG"
    load
}

# Open URL
open_url() {
    local url="$1"
    log "INFO" "Open: $url"
    load
    if [[ -z "$HOST" ]]; then
        echo "Err: Host req. Run: $0 -c" >&2
        return 1
    fi
    [[ -z "$url" ]] && return 1
    
    local opts=("${SSH_OPTS[@]}")
    if [[ -n "$KEY" ]]; then
        KEY="${KEY/#\~/$HOME}"
        [[ ! -f "$KEY" ]] && { echo "Err: Key not found: $KEY" >&2; return 1; }
        opts+=(-i "$KEY")
    fi
    
    local qurl
    qurl=$(printf '%q' "$url")
    log "DEBUG" "URL to remote: $qurl"
    local rcmd="$BROW $qurl"
    
    log "INFO" "Connecting to $HOST..."
    local out
    if out=$(ssh "${opts[@]}" "$HOST" "$rcmd" 2>&1); then
        log "INFO" "Success"
        return 0
    else
        local rc=$?
        log "ERROR" "Failed: $rc"
        [[ -n "$out" ]] && { log "ERROR" "stderr: $out"; echo "$out" >&2; }
        return $rc
    fi
}

# Install
inst() {
    log "INFO" "Install"
    local sp; sp="$(readlink -f "$0")"
    local dd="$HOME/.local/share/applications"
    local df="$dd/remote-default.desktop"
    mkdir -p "$dd"
    cat > "$df" <<EOF
[Desktop Entry]
Version=1.0
Name=Remote Default Browser
Exec=$sp %u
Type=Application
Terminal=false
MimeType=x-scheme-handler/http;x-scheme-handler/https;text/html;
EOF
    echo "Created: $df"
    command -v update-desktop-database &>/dev/null && update-desktop-database "$dd" &>/dev/null
    if command -v xdg-settings &>/dev/null; then
        xdg-settings set default-web-browser remote-default.desktop &>/dev/null && echo "Success"
    fi
}

# Uninstall
uninst() {
    local df="$HOME/.local/share/applications/remote-default.desktop"
    [[ -f "$df" ]] && rm -f "$df" && echo "Removed: $df"
    command -v update-desktop-database &>/dev/null && update-desktop-database "$(dirname "$df")" &>/dev/null
}

# Log show
show() {
    load
    local f="${LOG_F:-$HOME/.local/share/remote-default/remote-default.log}"
    echo -e "Log: $f\nOn: $LOG_ON\nLvl: $LVL\n"
    [[ -f "$f" ]] && tail -n 20 "$f"
}

# Help
help() {
    cat <<EOF
Remote Default Browser
Usage: $0 [URL] [OPTS]
Opts:
  -c, --configure     Config
  -i, --install       Install
  -u, --uninstall     Uninstall
  -s, --show-log      Show log
  -r, --remote-host   Host
  -k, --ssh-key       Key
  -b, --remote-browser Browser
  -E, --enable-logging On
  -D, --disable-logging Off
  -l, --log-level     Lvl
  -f, --log-file      File
EOF
}

# Main
main() {
    local url="" c=0 i=0 u=0 s=0 h="" k="" b="xdg-open" on="" l="" f=""
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -c|--configure) c=1; shift ;;
            -i|--install) i=1; shift ;;
            -u|--uninstall) u=1; shift ;;
            -s|--show-log) s=1; shift ;;
            -r|--remote-host) h="$2"; c=1; shift 2 ;;
            -k|--ssh-key) k="$2"; shift 2 ;;
            -b|--remote-browser) b="$2"; shift 2 ;;
            -E|--enable-logging) on="true"; c=1; shift ;;
            -D|--disable-logging) on="false"; c=1; shift ;;
            -l|--log-level) l="${2^^}"; c=1; shift 2 ;;
            -f|--log-file) f="$2"; shift 2 ;;
            --help|-h) help; exit 0 ;;
            -*) echo "Unknown: $1"; exit 1 ;;
            *) url="$1"; shift ;;
        esac
    done
    load
    [[ $s -eq 1 ]] && { show; exit 0; }
    if [[ $c -eq 1 ]]; then
        [[ -z "$h" ]] && h="$HOST"
        [[ -z "$k" ]] && k="$KEY"
        [[ -z "$on" ]] && on="$LOG_ON"
        [[ -z "$l" ]] && l="$LVL"
        [[ -z "$f" ]] && f="$LOG_F"
        [[ -z "$h" ]] && { read -rp "Host: " h; }
        [[ -n "$h" ]] && save "$h" "$k" "$b" "$on" "$l" "$f" || exit 1
    elif [[ $i -eq 1 ]]; then inst
    elif [[ $u -eq 1 ]]; then uninst
    elif [[ -n "$url" ]]; then open_url "$url"
    else help; fi
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
