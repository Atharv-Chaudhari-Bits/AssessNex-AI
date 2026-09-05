"""
Backend run script for FastAPI application.

Use this to start the FastAPI server for AssessNex AI backend.
Includes port conflict handling with fallback to random ports.
"""

import subprocess
import sys
import os
import socket

def find_free_port(preferred_port=8000):
    """
    Find a free port, starting with preferred_port.
    
    Args:
        preferred_port: The preferred port to use
        
    Returns:
        int: An available port number
    """
    port = preferred_port
    while port < 65535:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('0.0.0.0', port))
                return port
        except OSError:
            port += 1
    raise RuntimeError("No available ports found")

if __name__ == "__main__":
    # Find free port for backend
    preferred_backend_port = 8000
    backend_port = find_free_port(preferred_backend_port)
    
    # Set environment variables
    os.environ["DEBUG"] = "True"
    os.environ["ENVIRONMENT"] = "development"
    os.environ["SERVER_HOST"] = os.getenv("SERVER_HOST", "127.0.0.1")  # localhost by default
    os.environ["SERVER_PORT"] = str(backend_port)
    os.environ["LOG_LEVEL"] = "INFO"

    print("=" * 60)
    print("Starting AssessNex AI Backend (FastAPI)...")
    print("=" * 60)
    print(f"Access the API at: http://localhost:{backend_port}")
    print(f"API Documentation: http://localhost:{backend_port}/docs")
    if backend_port != preferred_backend_port:
        print(f"(Port {preferred_backend_port} in use, using {backend_port})")
    print("=" * 60)
    print()

    # Run FastAPI app with output visible
    subprocess.run(
        [sys.executable, "-m", "uvicorn", "backend.app.main:app", 
         "--host", "127.0.0.1",
         "--port", str(backend_port), 
         "--reload",
         "--log-level", "info"],
        cwd=os.path.dirname(__file__),
    )
