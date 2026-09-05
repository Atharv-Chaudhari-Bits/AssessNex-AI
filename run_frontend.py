"""
Frontend run script for Streamlit application.

Use this to start the Streamlit server for AssessNex AI frontend.
Includes port conflict handling with fallback to random ports.
Also auto-detects backend port for proper API communication.
"""

import subprocess
import sys
import os
import socket

def find_free_port(preferred_port=8501):
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

def find_backend_port(start_port=8000, max_attempts=10):
    """
    Find which port the backend is running on.
    Tries to connect to ports starting from start_port.
    
    Args:
        start_port: The port to start checking from
        max_attempts: Maximum number of ports to check
        
    Returns:
        int: The port the backend is running on, or start_port if not found
    """
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('127.0.0.1', port))
                if result == 0:
                    print(f"[OK] Backend detected on port {port}")
                    return port
        except Exception:
            pass
    
    # If not found, return default
    print(f"[!] Backend not found, using default port {start_port}")
    return start_port

if __name__ == "__main__":
    from backend.app.config import get_settings
    if not get_settings().ENABLE_LEGACY_STREAMLIT_FRONTEND:
        raise SystemExit("Legacy Streamlit frontend is disabled. Set ENABLE_LEGACY_STREAMLIT_FRONTEND=true to enable it.")
    # Find free port for frontend
    preferred_frontend_port = 8501
    frontend_port = find_free_port(preferred_frontend_port)
    
    # Detect backend port
    backend_port = find_backend_port(start_port=8000, max_attempts=10)
    
    # Set environment variables
    os.environ["STREAMLIT_SERVER_PORT"] = str(frontend_port)
    os.environ["STREAMLIT_SERVER_ADDRESS"] = "127.0.0.1"  # localhost only
    os.environ["STREAMLIT_LOGGER_LEVEL"] = "info"
    os.environ["API_BASE_URL"] = f"http://localhost:{backend_port}"
    
    # Get frontend directory
    root_dir = os.path.dirname(__file__)
    frontend_dir = os.path.join(root_dir, "frontend")
    
    # Add frontend directory to Python path so modules can be imported
    sys.path.insert(0, frontend_dir)

    print("=" * 60)
    print("Starting AssessNex AI Frontend (Streamlit)...")
    print("=" * 60)
    print(f"Access the app at: http://localhost:{frontend_port}")
    if frontend_port != preferred_frontend_port:
        print(f"(Preferred port {preferred_frontend_port} was in use, using {frontend_port})")
    print(f"Backend API: http://localhost:{backend_port}")
    print("=" * 60)
    print()

    # Run streamlit app from frontend directory
    env = os.environ.copy()
    env["PYTHONPATH"] = frontend_dir + os.pathsep + env.get("PYTHONPATH", "")
    
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", "app.py",
         "--logger.level=info",
         "--client.showErrorDetails=true"],
        cwd=frontend_dir,
        env=env,
    )
