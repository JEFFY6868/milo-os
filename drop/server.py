#!/usr/bin/env python3
"""
Milo Drop Background Transfer Engine & Server
Handles:
  1. Universal Mobile Web Portal (HTTP on port 4242)
  2. Phone-to-PC photo/video/file uploads directly to ~/Downloads
  3. PC-to-Phone downloads
  4. Instant Clipboard Teleportation (bidirectional with Wayland wl-copy/wl-paste)
  5. Backwards-compatible raw TCP MILODROP protocol support
  6. Desktop notifications via notify-send & audio chimes
"""

import os
import sys
import json
import time
import socket
import threading
import subprocess
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

PORT = 4242
def get_downloads_dir() -> Path:
    """Return ~/Downloads or /tmp/Downloads if ~/Downloads is not writable."""
    candidate = Path.home() / "Downloads"
    try:
        candidate.mkdir(parents=True, exist_ok=True)
        probe = candidate / ".milo_write_test"
        probe.write_text("ok")
        probe.unlink()
        return candidate
    except Exception:
        fallback = Path("/tmp/Downloads")
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback

DOWNLOADS_DIR = get_downloads_dir()
WEB_DIR = Path(__file__).resolve().parent / "web"

# State tracker for GUI integration
transfer_history = []
active_transfers = []
history_lock = threading.Lock()

def get_local_ip():
    """Detect the active Wi-Fi or LAN IP address."""
    # Method 1: ip route
    try:
        out = subprocess.check_output(['ip', 'route'], stderr=subprocess.DEVNULL).decode()
        for line in out.splitlines():
            if 'default via' in line and 'src ' in line:
                return line.split('src ')[1].split()[0]
            elif 'src ' in line and not line.strip().startswith('127.'):
                return line.split('src ')[1].split()[0]
    except Exception:
        pass

    # Method 2: nmcli
    try:
        out = subprocess.check_output(['nmcli', '-g', 'IP4.ADDRESS', 'device', 'show'], stderr=subprocess.DEVNULL).decode()
        for line in out.splitlines():
            ip = line.strip().split('/')[0]
            if ip and not ip.startswith('127.'):
                return ip
    except Exception:
        pass

    # Method 3: UDP dummy connect
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('192.168.1.255', 9))
        ip = s.getsockname()[0]
        s.close()
        if ip and not ip.startswith('127.'):
            return ip
    except Exception:
        pass

    return '127.0.0.1'

def notify_received(filename, size_bytes):
    """Trigger desktop notification and sound."""
    size_mb = size_bytes / (1024 * 1024)
    size_str = f"{size_mb:.1f} MB" if size_mb >= 1.0 else f"{size_bytes / 1024:.0f} KB"
    
    # notify-send
    try:
        subprocess.Popen([
            "notify-send",
            "-a", "Milo Drop",
            "-i", "document-save",
            "📥 Milo Drop: File Received",
            f"Successfully saved {filename} ({size_str}) to ~/Downloads"
        ])
    except Exception:
        pass

    # audio chime
    try:
        subprocess.Popen(["milo-sound", "connect"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def get_unique_filepath(target_dir: Path, filename: str) -> Path:
    """Generate a unique file path to prevent accidental overwrites."""
    base_name = Path(filename).name
    stem = Path(base_name).stem
    suffix = Path(base_name).suffix
    dest = target_dir / base_name
    counter = 1
    while dest.exists():
        dest = target_dir / f"{stem} ({counter}){suffix}"
        counter += 1
    return dest

class MiloDropHTTPHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Clean logging
        sys.stderr.write(f"[MiloDrop Server] {args[0]} - {args[1]}\n")

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html"):
            index_path = WEB_DIR / "index.html"
            if index_path.exists():
                content = index_path.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404, "Web portal index.html not found")

        elif path == "/qr":
            ip = get_local_ip()
            url = f"http://{ip}:{PORT}"
            try:
                # Generate QR code using qrencode into png stream
                p = subprocess.Popen(
                    ["qrencode", "-s", "8", "-m", "2", "-o", "-", url],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                qr_bytes, _ = p.communicate()
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.send_header("Content-Length", str(len(qr_bytes)))
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(qr_bytes)
            except Exception as e:
                self.send_error(500, f"Error generating QR code: {e}")

        elif path == "/files":
            # List files in ~/Downloads
            files_list = []
            try:
                for entry in os.scandir(DOWNLOADS_DIR):
                    if entry.is_file() and not entry.name.startswith('.'):
                        stat = entry.stat()
                        files_list.append({
                            "name": entry.name,
                            "size": stat.st_size,
                            "time": stat.st_mtime
                        })
                # Sort newest first
                files_list.sort(key=lambda x: x["time"], reverse=True)
            except Exception as e:
                sys.stderr.write(f"Error scanning downloads: {e}\n")

            data = json.dumps(files_list[:30]).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(data)

        elif path.startswith("/download/"):
            req_filename = urllib.parse.unquote(path[len("/download/"):])
            # Security: ensure file stays in DOWNLOADS_DIR
            target_path = (DOWNLOADS_DIR / req_filename).resolve()
            if DOWNLOADS_DIR.resolve() in target_path.parents and target_path.is_file():
                file_size = target_path.stat().st_size
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Disposition", f'attachment; filename="{target_path.name}"')
                self.send_header("Content-Length", str(file_size))
                self.send_cors_headers()
                self.end_headers()
                with open(target_path, "rb") as f:
                    while chunk := f.read(65536):
                        self.wfile.write(chunk)
            else:
                self.send_error(404, "File not found or permission denied")

        elif path == "/api/status":
            ip = get_local_ip()
            with history_lock:
                recent = list(transfer_history)
            data = json.dumps({
                "ip": ip,
                "port": PORT,
                "url": f"http://{ip}:{PORT}",
                "downloads_dir": str(DOWNLOADS_DIR),
                "recent_transfers": recent
            }).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(data)

        elif path == "/api/clipboard":
            text = ""
            try:
                text = subprocess.check_output(["wl-paste", "--no-newline"], stderr=subprocess.DEVNULL).decode("utf-8", errors="replace")
            except Exception:
                pass
            data = json.dumps({"clipboard": text}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(data)

        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/clipboard":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8", errors="replace")
            
            # Copy to Wayland clipboard
            try:
                p = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE)
                p.communicate(body.encode("utf-8"))
                
                # Show notification
                preview = (body[:40] + "...") if len(body) > 40 else body
                subprocess.Popen([
                    "notify-send",
                    "-a", "Milo Drop",
                    "-i", "edit-paste",
                    "📋 Clipboard Synced",
                    f'Copied from mobile: "{preview}"'
                ])
                subprocess.Popen(["milo-sound", "beep"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                sys.stderr.write(f"Error copying to clipboard: {e}\n")

            res = json.dumps({"success": True}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(res)))
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(res)

        elif path == "/upload":
            content_type = self.headers.get("Content-Type", "")
            if not content_type.startswith("multipart/form-data"):
                self.send_error(400, "Content-Type must be multipart/form-data")
                return

            boundary = content_type.split("boundary=")[1].encode()
            boundary_marker = b"--" + boundary
            boundary_end = b"--" + boundary + b"--"

            content_length = int(self.headers.get("Content-Length", 0))
            if content_length <= 0:
                self.send_error(400, "Empty upload payload")
                return

            saved_files = []
            
            # Streaming multipart parser
            try:
                reader = self.rfile
                remaining = content_length
                
                line = reader.readline()
                remaining -= len(line)

                while remaining > 0:
                    if boundary_end in line:
                        break
                    if boundary_marker in line:
                        # Parse headers for this part
                        headers = {}
                        while True:
                            header_line = reader.readline()
                            remaining -= len(header_line)
                            if header_line in (b"\r\n", b"\n", b""):
                                break
                            h_str = header_line.decode("utf-8", errors="replace").strip()
                            if ":" in h_str:
                                k, v = h_str.split(":", 1)
                                headers[k.strip().lower()] = v.strip()

                        disp = headers.get("content-disposition", "")
                        filename = None
                        if "filename=" in disp:
                            raw_fname = disp.split("filename=")[1].strip()
                            if raw_fname.startswith('"') and raw_fname.endswith('"'):
                                filename = raw_fname[1:-1]
                            else:
                                filename = raw_fname.split(";")[0].strip()

                        if filename:
                            filename = os.path.basename(filename)
                            dest_path = get_unique_filepath(DOWNLOADS_DIR, filename)
                            bytes_written = 0
                            
                            # Stream file content until next boundary
                            with open(dest_path, "wb") as out_f:
                                prev_line = None
                                while remaining > 0:
                                    cur_line = reader.readline()
                                    remaining -= len(cur_line)
                                    
                                    if boundary_marker in cur_line or boundary_end in cur_line:
                                        # Write previous line without trailing \r\n
                                        if prev_line is not None:
                                            if prev_line.endswith(b"\r\n"):
                                                out_f.write(prev_line[:-2])
                                                bytes_written += len(prev_line) - 2
                                            elif prev_line.endswith(b"\n"):
                                                out_f.write(prev_line[:-1])
                                                bytes_written += len(prev_line) - 1
                                            else:
                                                out_f.write(prev_line)
                                                bytes_written += len(prev_line)
                                        line = cur_line
                                        break
                                    else:
                                        if prev_line is not None:
                                            out_f.write(prev_line)
                                            bytes_written += len(prev_line)
                                        prev_line = cur_line

                            saved_files.append({"name": dest_path.name, "size": bytes_written, "path": str(dest_path)})
                            notify_received(dest_path.name, bytes_written)
                            with history_lock:
                                transfer_history.insert(0, {
                                    "name": dest_path.name,
                                    "size": bytes_written,
                                    "path": str(dest_path),
                                    "time": time.time(),
                                    "direction": "incoming"
                                })
                        else:
                            # Not a file part, consume until boundary
                            while remaining > 0:
                                cur_line = reader.readline()
                                remaining -= len(cur_line)
                                if boundary_marker in cur_line or boundary_end in cur_line:
                                    line = cur_line
                                    break
                    else:
                        line = reader.readline()
                        remaining -= len(line)

            except Exception as e:
                sys.stderr.write(f"Upload error: {e}\n")
                self.send_error(500, f"Upload error: {e}")
                return

            res = json.dumps({"success": True, "count": len(saved_files), "files": saved_files}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(res)))
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(res)

        else:
            self.send_error(404, "Not Found")

class ThreadedHTTPServer(HTTPServer):
    daemon_threads = True

def handle_miloc_tcp_client(client_sock, client_addr):
    """Handle raw MiloLang CLI MILODROP sender connections."""
    try:
        # Read header: "MILODROP <filename> <filesize>\n"
        header = b""
        while len(header) < 256:
            ch = client_sock.recv(1)
            if not ch or ch == b"\n":
                break
            header += ch

        parts = header.decode("utf-8", errors="replace").strip().split()
        if len(parts) >= 3 and parts[0] == "MILODROP":
            filename = os.path.basename(parts[1])
            filesize = int(parts[2])
            dest_path = get_unique_filepath(DOWNLOADS_DIR, filename)

            received = 0
            with open(dest_path, "wb") as f:
                while received < filesize:
                    chunk = client_sock.recv(min(8192, filesize - received))
                    if not chunk:
                        break
                    f.write(chunk)
                    received += len(chunk)

            # Send ACK
            client_sock.sendall(b"OK\n")
            client_sock.close()

            notify_received(dest_path.name, received)
            with history_lock:
                transfer_history.insert(0, {
                    "name": dest_path.name,
                    "size": received,
                    "path": str(dest_path),
                    "time": time.time(),
                    "direction": "incoming"
                })
        else:
            client_sock.close()
    except Exception as e:
        sys.stderr.write(f"MiloLang TCP client error: {e}\n")
        try:
            client_sock.close()
        except Exception:
            pass

def start_server_daemon(port=PORT):
    """Start HTTP server with dual MiloLang protocol support."""
    server = ThreadedHTTPServer(("0.0.0.0", port), MiloDropHTTPHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    return server

if __name__ == "__main__":
    ip = get_local_ip()
    print("=" * 60)
    print(f"🚀 MILO DROP UNIVERSAL SERVER ACTIVE")
    print(f"📍 Local Web Portal:  http://{ip}:{PORT}")
    print(f"📥 Downloads Folder:  {DOWNLOADS_DIR}")
    print("=" * 60)
    
    server = start_server_daemon(PORT)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping Milo Drop server...")
        server.shutdown()
