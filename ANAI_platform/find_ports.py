"""
Simple port finder utility for AssessNex AI
"""
import socket
import sys

def find_free_port(start_port, max_attempts=20):
    """Find a free port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    return None

if __name__ == "__main__":
    backend_port = find_free_port(8000)
    frontend_port = find_free_port(8501)
    
    if backend_port is None:
        print("ERROR_BACKEND")
        sys.exit(1)
    if frontend_port is None:
        print("ERROR_FRONTEND")
        sys.exit(1)
    
    print(f"{backend_port} {frontend_port}")
