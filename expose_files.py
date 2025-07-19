import http.server
import socketserver
import threading
import subprocess
import time
import requests
import os
import atexit
import urllib.parse

class DownloadHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        filename = urllib.parse.unquote(os.path.basename(self.path))
        if not os.path.exists(filename):
            self.send_error(404, "File Not Found")
            return
            
        self.send_response(200)
        self.send_header('Content-Type', 'application/octet-stream')
        self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
        self.end_headers()
        
        with open(filename, 'rb') as file:
            self.wfile.write(file.read())

def container(name):
    # Validate filename
    if not all(32 <= ord(c) < 127 for c in name):
        raise ValueError("Filename contains invalid characters (only standard ASCII allowed)")
    
    os.chdir("C:/Users/dwiwe/Documents/Html & CSS/Stock analyst MCP server/")

    # Start server
    port = 8000
    httpd = socketserver.TCPServer(("", port), DownloadHandler)
    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    # Start ngrok
    ngrok = subprocess.Popen([
        "C://Users//dwiwe//Documents//Html & CSS//MCP server//images//ngrok.exe",
        "http",
        str(port)
    ], stdout=subprocess.PIPE)
    time.sleep(3)  # Wait for ngrok

    # Get URL
    resp = requests.get("http://localhost:4040/api/tunnels")
    public_url = resp.json()["tunnels"][0]["public_url"]
    download_url = f"{public_url}/{urllib.parse.quote(name)}"
    
    # Setup cleanup to run on program exit
    def cleanup():
        httpd.shutdown()
        ngrok.terminate()
    atexit.register(cleanup)

    # Start timeout thread
    def timeout_thread():
        time.sleep(300)  # 10 minutes
        cleanup()
    threading.Thread(target=timeout_thread, daemon=True).start()

    return download_url  # Returns immediately