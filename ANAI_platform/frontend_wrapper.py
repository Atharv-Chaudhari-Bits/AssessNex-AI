"""
Wrapper script to properly run Streamlit with correct Python path.
This ensures frontend modules can be imported correctly.
Includes automatic backend detection.
"""

import sys
import os
import subprocess
import socket

def find_backend_port(start_port=8000, max_attempts=20):
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
                result = s.connect_ex(('0.0.0.0', port))
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
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Add frontend directory to Python path
    frontend_dir = os.path.join(script_dir, "frontend")
    sys.path.insert(0, frontend_dir)
    
    # Detect backend port
    backend_port = find_backend_port(start_port=8000, max_attempts=20)
    
    # Get frontend port from start.bat environment variable, or find one
    frontend_port = os.environ.get("PORT", "8501")
    
    # Set environment variables
    os.environ["STREAMLIT_SERVER_PORT"] = frontend_port
    os.environ["STREAMLIT_SERVER_ADDRESS"] = "0.0.0.0"  # localhost only
    os.environ["STREAMLIT_LOGGER_LEVEL"] = "info"
    os.environ["API_BASE_URL"] = f"http://0.0.0.0:{backend_port}"
    
    print(f"[OK] Frontend will run on port: {frontend_port}")
    print(f"[OK] Backend API configured at: {os.environ['API_BASE_URL']}")
    
    # Run streamlit with PYTHONPATH set
    env = os.environ.copy()
    env["PYTHONPATH"] = frontend_dir + os.pathsep + env.get("PYTHONPATH", "")
    
    # Run the streamlit app from frontend directory
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", "app.py",
         "--logger.level=info",
         "--client.showErrorDetails=true"],
        cwd=frontend_dir,
        env=env
    )
