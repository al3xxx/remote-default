#!/usr/bin/env python3
"""
Remote Default Browser
Opens URLs on a remote host via SSH instead of locally.
Useful for headless servers without a GUI.
"""

import sys
import subprocess
import shlex
import os
import argparse
import logging
import re
import urllib.parse
from pathlib import Path
from datetime import datetime


class RemoteDefaultBrowser:
    LVLS = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    CFG_MAP = {
        'remote_host': 'host',
        'ssh_key': 'key',
        'remote_browser': 'browser',
        'logging_enabled': 'log_on',
        'log_level': 'lvl',
        'log_file': 'log_f'
    }
    
    def __init__(self, cfg_f=None):
        if cfg_f is None:
            cfg_f = Path.home() / '.config' / 'remote-default' / 'config'
        self.cfg_f = Path(cfg_f)
        self.cfg = self.load_cfg()
        self.log = self.setup_log()
    
    def setup_log(self):
        """Setup logging based on configuration."""
        l = logging.getLogger('remote-default')
        l.handlers.clear()
        
        if not self.cfg.get('log_on', False):
            l.addHandler(logging.NullHandler())
            l.setLevel(logging.CRITICAL)
            return l
        
        lvl_s = self.cfg.get('lvl', 'INFO').upper()
        lvl = self.LVLS.get(lvl_s, logging.INFO)
        l.setLevel(lvl)
        
        f = self.cfg.get('log_f', '')
        if f:
            p = Path(f).expanduser()
        else:
            d = Path.home() / '.local' / 'share' / 'remote-default'
            d.mkdir(parents=True, exist_ok=True)
            p = d / 'remote-default.log'
        
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            h = logging.FileHandler(p, mode='a', encoding='utf-8')
            fmt = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', '%Y-%m-%d %H:%M:%S')
            h.setFormatter(fmt)
            l.addHandler(h)
            
            if lvl == logging.DEBUG:
                ch = logging.StreamHandler(sys.stderr)
                ch.setFormatter(fmt)
                l.addHandler(ch)
            
            l.info(f"Log init - Level: {lvl_s}, File: {p}")
            
        except Exception as e:
            l.addHandler(logging.NullHandler())
            print(f"Warn: Log setup failed: {e}", file=sys.stderr)
        
        return l
    
    def load_cfg(self):
        """Load configuration from file."""
        c = {
            'host': None,
            'key': None,
            'browser': 'remlib',
            'log_on': False,
            'lvl': 'INFO',
            'log_f': ''
        }
        
        if not self.cfg_f.exists():
            return c
        
        try:
            with open(self.cfg_f, 'r') as f:
                for ln in f:
                    ln = ln.strip()
                    if not ln or ln.startswith('#'): continue
                    if '=' in ln:
                        k, v = ln.split('=', 1)
                        k, v = k.strip(), v.strip().strip('"').strip("'")
                        
                        rk = self.CFG_MAP.get(k, k)
                        if rk in c:
                            if rk == 'log_on':
                                c[rk] = v.lower() in ('true', 'yes', '1', 'on')
                            else:
                                c[rk] = v
        except Exception as e:
            print(f"Warn: Config load failed: {e}", file=sys.stderr)
        
        return c
    
    def save_cfg(self, host, key=None, browser='remlib',
                 log_on=False, lvl='INFO', log_f=''):
        """Save configuration to file."""
        try:
            self.cfg_f.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cfg_f, 'w') as f:
                f.write("# Remote Default Browser Config\n")
                f.write(f"remote_host={host}\n")
                if key: f.write(f"ssh_key={key}\n")
                f.write(f"remote_browser={browser}\n")
                f.write("\n# Log Config\n")
                f.write(f"logging_enabled={'true' if log_on else 'false'}\n")
                f.write(f"log_level={lvl.upper()}\n")
                if log_f: f.write(f"log_file={log_f}\n")
            
            self.cfg = self.load_cfg()
            self.log = self.setup_log()
            print(f"Config saved: {self.cfg_f}")
            self.log.info("Config updated")
        except Exception as e:
            print(f"Error saving config: {e}", file=sys.stderr)
            return 1
        return 0
    
    def open_url(self, url):
        """Open URL on remote host via SSH."""
        self.log.info(f"Open URL: {url}")
        
        if not self.cfg['host']:
            print("Err: Host not set. Run: remote-default -c", file=sys.stderr)
            return 1
        
        if not url:
            self.log.error("Empty URL provided")
            return 1
        
        # Check for callback port
        port = None
        if 'callback' in url.lower():
            d_url = urllib.parse.unquote(url)
            m = re.search(r'(?:localhost|127\.0\.0\.1):([0-9]+)', d_url)
            if m:
                port = m.group(1)
                self.log.info(f"Callback port detected: {port}")
        
        cmd = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10',
               '-o', 'ServerAliveInterval=5', '-o', 'ServerAliveCountMax=3']
        
        if self.cfg['key']:
            kp = Path(self.cfg['key']).expanduser()
            if not kp.exists():
                print(f"Err: Key not found: {kp}", file=sys.stderr)
                return 1
            cmd.extend(['-i', str(kp)])
        
        # Start tunnel if port found
        if port:
            t_cmd = cmd + ['-TnNR', f'{port}:localhost:{port}', self.cfg['host']]
            self.log.debug(f"Tunnel cmd: {shlex.join(t_cmd)}")
            subprocess.Popen(t_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        cmd.append(self.cfg['host'])
        
        qurl = shlex.quote(url)
        self.log.debug(f"URL passed to remote: {qurl}")
        
        rcmd = f"{self.cfg['browser']} {qurl}"
        cmd.append(rcmd)
        
        self.log.debug(f"SSH cmd: {shlex.join(cmd)}")
        
        try:
            self.log.info(f"Connecting to {self.cfg['host']}...")
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if r.returncode == 0:
                self.log.info("Success")
                return 0
            
            print(f"Err: SSH failed ({r.returncode})", file=sys.stderr)
            if r.stderr: self.log.error(f"stderr: {r.stderr.strip()}")
            return r.returncode
            
        except Exception as e:
            self.log.exception(f"Err: {e}")
            print(f"Err: {e}", file=sys.stderr)
            return 1
    
    def install(self):
        """Install as default browser on Linux."""
        self.log.info("Install default browser")
        
        try:
            sp = Path(__file__).resolve()
            
            if not os.access(sp, os.X_OK):
                print(f"Err: Not executable: {sp}", file=sys.stderr)
                return 1
            
            # .desktop content
            cnt = f"""[Desktop Entry]
Version=1.0
Name=Remote Default Browser
Comment=Opens URLs on remote host via SSH
Exec={sp} %u
Type=Application
Terminal=false
MimeType=x-scheme-handler/http;x-scheme-handler/https;text/html;
"""
            
            dd = Path.home() / '.local' / 'share' / 'applications'
            dd.mkdir(parents=True, exist_ok=True)
            df = dd / 'remote-default.desktop'
            
            with open(df, 'w') as f: f.write(cnt)
            print(f"Created: {df}")
            
            # Update DB
            subprocess.run(['update-desktop-database', str(dd)], capture_output=True)
            
            # Set default
            subprocess.run(['xdg-settings', 'set', 'default-web-browser', 'remote-default.desktop'], check=True)
            print("Set default browser success")
            return 0
            
        except Exception as e:
            self.log.exception(f"Install failed: {e}")
            print(f"Err: {e}", file=sys.stderr)
            return 1
    
    def uninstall(self):
        """Remove desktop file."""
        self.log.info("Uninstall")
        df = Path.home() / '.local' / 'share' / 'applications' / 'remote-default.desktop'
        if df.exists():
            df.unlink()
            print(f"Removed: {df}")
            subprocess.run(['update-desktop-database', str(df.parent)], capture_output=True)
        return 0


def main():
    p = argparse.ArgumentParser(description='Remote Default Browser')
    p.add_argument('url', nargs='?', help='URL to open')
    p.add_argument('-c', '--configure', action='store_true', help='Configure remote settings (interactive if no host provided)')
    p.add_argument('-i', '--install', action='store_true', help='Install as the system default browser')
    p.add_argument('-u', '--uninstall', action='store_true', help='Uninstall and remove desktop integration')
    p.add_argument('-r', '--remote-host', dest='host', help='Set remote host (e.g., user@hostname)')
    p.add_argument('-k', '--ssh-key', dest='key', help='Set path to SSH private key')
    p.add_argument('-b', '--remote-browser', dest='browser', default='xdg-open', help='Set browser command on remote host')
    
    # Log args
    p.add_argument('-E', '--enable-logging', action='store_true', help='Enable persistent logging')
    p.add_argument('-D', '--disable-logging', action='store_true', help='Disable persistent logging')
    p.add_argument('-l', '--log-level', dest='lvl', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help='Set logging verbosity level')
    p.add_argument('-f', '--log-file', dest='log_f', help='Set path to log file')
    p.add_argument('-s', '--show-log', action='store_true', help='Display log location and recent entries')
    
    a = p.parse_args()
    b = RemoteDefaultBrowser()
    
    if a.show_log:
        f = Path(b.cfg.get('log_f') or (Path.home() / '.local/share/remote-default/remote-default.log'))
        print(f"Log: {f}\nOn: {b.cfg.get('log_on')}\nLvl: {b.cfg.get('lvl')}\n")
        if f.exists():
            with open(f, 'r') as file:
                for ln in file.readlines()[-20:]: print(ln.rstrip())
        return 0
    
    if a.configure or a.host or a.key or a.browser or a.enable_logging or a.disable_logging or a.lvl or a.log_f:
        host = a.host or b.cfg.get('host')
        key = a.key or b.cfg.get('key')
        brow = a.browser or b.cfg.get('browser')
        on = a.enable_logging if a.enable_logging else (False if a.disable_logging else b.cfg.get('log_on', False))
        lvl = a.lvl or b.cfg.get('lvl', 'INFO')
        f = a.log_f or b.cfg.get('log_f', '')
        
        if not host and a.configure:
            host = input("Remote host (user@host): ").strip()
        
        if host: return b.save_cfg(host, key, brow, on, lvl, f)
        print("Err: Host req", file=sys.stderr)
        return 1
    
    if a.install: return b.install()
    if a.uninstall: return b.uninstall()
    if a.url: return b.open_url(a.url)
    
    p.print_help()
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Unexpected error: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)
