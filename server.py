#!/usr/bin/env python3
"""
Technocore Web Client Local Server & CORS Proxy.
Provides static file serving for index.html and a secure local reverse-proxy for the Technocore API.
"""

import http.server
import urllib.request
import urllib.error
import socketserver
import json
import sys

PORT = 8000
TARGET_BASE_URL = "https://technocore.chat"

class ProxyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Prevent caching for proxy endpoints and enable CORS
        if self.path.startswith("/api/"):
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Accept, User-Agent")
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        super().end_headers()

    def do_OPTIONS(self):
        # Handle CORS preflight requests
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Accept, User-Agent")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        if self.path.startswith("/api/"):
            self.proxy_request("GET")
        else:
            super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api/"):
            self.proxy_request("POST")
        else:
            self.send_error(404, "Endpoint not found")

    def proxy_request(self, method):
        # Extract target path after /api/
        target_path = self.path[len("/api/"):]
        target_url = f"{TARGET_BASE_URL}/{target_path}"
        
        # Read the request body if present
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else None
        
        # Prepare headers for target request (excluding host/connection headers)
        headers = {}
        for key, val in self.headers.items():
            key_lower = key.lower()
            if key_lower not in ('host', 'content-length', 'connection', 'accept-encoding', 'origin', 'referer'):
                headers[key] = val
        
        # Add custom User-Agent
        headers["User-Agent"] = f"technocore-webui-proxy/1.0.0"
        
        print(f"[Proxy] {method} -> {target_url}", flush=True)
        
        req = urllib.request.Request(target_url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=15.0) as response:
                resp_body = response.read()
                
                # Send status and headers
                self.send_response(response.status)
                for key, val in response.headers.items():
                    key_lower = key.lower()
                    if key_lower not in ('transfer-encoding', 'connection', 'content-length', 'access-control-allow-origin', 'access-control-allow-methods', 'access-control-allow-headers'):
                        self.send_header(key, val)
                
                self.send_header("Content-Length", str(len(resp_body)))
                self.end_headers()
                self.wfile.write(resp_body)
                
        except urllib.error.HTTPError as e:
            print(f"[Proxy Error] HTTP {e.code} for {target_url}", flush=True)
            try:
                resp_body = e.read()
            except Exception:
                resp_body = str(e).encode('utf-8')
                
            self.send_response(e.code)
            for key, val in e.headers.items():
                key_lower = key.lower()
                if key_lower not in ('transfer-encoding', 'connection', 'content-length', 'access-control-allow-origin', 'access-control-allow-methods', 'access-control-allow-headers'):
                    self.send_header(key, val)
            
            self.send_header("Content-Length", str(len(resp_body)))
            self.end_headers()
            self.wfile.write(resp_body)
            
        except urllib.error.URLError as e:
            print(f"[Proxy Error] Connect failed to {target_url}: {e.reason}", flush=True)
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            err_msg = json.dumps({"error": f"Failed to connect to Technocore: {e.reason}"}).encode('utf-8')
            self.send_header("Content-Length", str(len(err_msg)))
            self.end_headers()
            self.wfile.write(err_msg)
            
        except Exception as e:
            print(f"[Proxy Exception] {str(e)}", flush=True)
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            err_msg = json.dumps({"error": f"Proxy exception: {str(e)}"}).encode('utf-8')
            self.send_header("Content-Length", str(len(err_msg)))
            self.end_headers()
            self.wfile.write(err_msg)

if __name__ == "__main__":
    # Ensure double bindings are allowed on address reuse
    socketserver.TCPServer.allow_reuse_address = True
    
    print("=" * 60)
    print("      Technocore Web Client Helper - Running Local Server")
    print("=" * 60)
    print(f" - Web App URL:      http://localhost:{PORT}")
    print(f" - CORS Proxy URL:   http://localhost:{PORT}/api/")
    print(f" - Target Host:      {TARGET_BASE_URL}")
    print("Press Ctrl+C to terminate.")
    print("=" * 60)
    
    try:
        with socketserver.TCPServer(("", PORT), ProxyHTTPRequestHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down local server. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\nServer error: {e}", file=sys.stderr)
        sys.exit(1)
