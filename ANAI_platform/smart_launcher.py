"""
Smart launcher for AssessNex AI.

Automatically detects available ports and launches backend + frontend
without requiring manual port configuration or process killing.

Features:
- Dynamic port detection for both services
- Automatic cross-service configuration
- Clean startup without port conflicts
- No process killing needed

Usage:
    python smart_launcher.py              # Launch both services
    python smart_launcher.py --backend    # Backend only
    python smart_launcher.py --frontend   # Frontend only
"""

import subprocess
import sys
import os
import socket
import time
import argparse
from typing import Tuple, List

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def find_free_ports(start_port: int = 8000, count: int = 1) -> List[int]:
    """
    Find N free ports starting from start_port.
    
    Args:
        start_port: Starting port number
        count: Number of free ports to find
        
    Returns:
        List[int]: List of available port numbers
    """
    free_ports = []
    port = start_port
    
    while len(free_ports) < count and port < 65535:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                free_ports.append(port)
        except OSError:
            pass
        port += 1
    
    if len(free_ports) < count:
        raise RuntimeError(f"Could not find {count} free ports")
    
    return free_ports

def get_script_directory() -> str:
    """Get the directory of this script."""
    return os.path.dirname(os.path.abspath(__file__))

def print_banner(title: str):
    """Print a formatted banner."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}\n")

def print_success(message: str):
    """Print success message."""
    print(f"{Colors.GREEN}[OK] {message}{Colors.RESET}")

def print_info(message: str):
    """Print info message."""
    print(f"{Colors.BLUE}[*] {message}{Colors.RESET}")

def print_warning(message: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}[!] {message}{Colors.RESET}")

def launch_backend(backend_port: int) -> subprocess.Popen:
    """
    Launch the FastAPI backend.
    
    Args:
        backend_port: Port to run backend on
        
    Returns:
        Popen: Process object
    """
    script_dir = get_script_directory()
    
    print_info(f"Starting backend on port {backend_port}...")
    
    env = os.environ.copy()
    env["DEBUG"] = "True"
    env["ENVIRONMENT"] = "development"
    env["SERVER_HOST"] = "127.0.0.1"
    env["SERVER_PORT"] = str(backend_port)
    env["LOG_LEVEL"] = "INFO"
    
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.app.main:app",
         "--host", "127.0.0.1",
         "--port", str(backend_port),
         "--reload",
         "--log-level", "info"],
        cwd=script_dir,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Wait for backend to start
    max_retries = 30
    for i in range(max_retries):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('127.0.0.1', backend_port))
                if result == 0:
                    print_success(f"Backend started on port {backend_port}")
                    return process
        except Exception:
            pass
        time.sleep(0.5)
    
    print_warning("Backend startup validation timeout (may still be starting...)")
    return process

def launch_frontend(frontend_port: int, backend_port: int) -> subprocess.Popen:
    """
    Launch the Streamlit frontend.
    
    Args:
        frontend_port: Port to run frontend on
        backend_port: Port the backend is running on
        
    Returns:
        Popen: Process object
    """
    script_dir = get_script_directory()
    frontend_dir = os.path.join(script_dir, "frontend")
    
    print_info(f"Starting frontend on port {frontend_port}...")
    print_info(f"Frontend will connect to backend at http://localhost:{backend_port}")
    
    env = os.environ.copy()
    env["STREAMLIT_SERVER_PORT"] = str(frontend_port)
    env["STREAMLIT_SERVER_ADDRESS"] = "127.0.0.1"
    env["STREAMLIT_LOGGER_LEVEL"] = "info"
    env["API_BASE_URL"] = f"http://localhost:{backend_port}"
    env["PYTHONPATH"] = frontend_dir + os.pathsep + env.get("PYTHONPATH", "")
    
    process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "app.py",
         "--logger.level=info",
         "--client.showErrorDetails=true"],
        cwd=frontend_dir,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Wait for frontend to start
    max_retries = 60
    for i in range(max_retries):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('127.0.0.1', frontend_port))
                if result == 0:
                    print_success(f"Frontend started on port {frontend_port}")
                    return process
        except Exception:
            pass
        time.sleep(0.5)
    
    print_warning("Frontend startup validation timeout (may still be starting...)")
    return process

def monitor_process(process: subprocess.Popen, name: str):
    """
    Monitor a process and print its output.
    
    Args:
        process: Process to monitor
        name: Name of the process (for logging)
    """
    try:
        while True:
            output = process.stdout.readline()
            if not output:
                break
            print(f"[{name}] {output.rstrip()}")
    except Exception:
        pass

def main():
    """Main launcher function."""
    parser = argparse.ArgumentParser(
        description="Smart launcher for AssessNex AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python smart_launcher.py              # Launch both backend + frontend
  python smart_launcher.py --backend    # Backend only
  python smart_launcher.py --frontend   # Frontend only
        """
    )
    
    parser.add_argument(
        "--backend",
        action="store_true",
        help="Launch backend only"
    )
    parser.add_argument(
        "--frontend",
        action="store_true",
        help="Launch frontend only"
    )
    parser.add_argument(
        "--backend-port",
        type=int,
        default=8000,
        help="Starting port for backend (default: 8000)"
    )
    parser.add_argument(
        "--frontend-port",
        type=int,
        default=8501,
        help="Starting port for frontend (default: 8501)"
    )
    
    args = parser.parse_args()
    
    # Determine what to launch
    launch_backend_flag = args.backend or (not args.backend and not args.frontend)
    launch_frontend_flag = args.frontend or (not args.backend and not args.frontend)
    
    print_banner("Smart Launcher - AssessNex AI")
    
    processes = []
    backend_process = None
    frontend_process = None
    backend_port = None
    frontend_port = None
    
    try:
        # Launch backend if needed
        if launch_backend_flag:
            print_info("Finding available ports...")
            backend_port = find_free_ports(args.backend_port, 1)[0]
            
            if backend_port != args.backend_port:
                print_warning(f"Port {args.backend_port} in use, using {backend_port}")
            
            backend_process = launch_backend(backend_port)
            processes.append(backend_process)
        
        # Launch frontend if needed
        if launch_frontend_flag:
            # If we didn't launch backend, try to detect it
            if backend_port is None:
                print_info("Detecting backend port...")
                for port in range(args.backend_port, args.backend_port + 20):
                    try:
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                            s.settimeout(1)
                            result = s.connect_ex(('127.0.0.1', port))
                            if result == 0:
                                backend_port = port
                                print_success(f"Found backend on port {backend_port}")
                                break
                    except Exception:
                        pass
                
                if backend_port is None:
                    print_warning("Could not detect backend port, using default 8000")
                    backend_port = args.backend_port
            
            frontend_port = find_free_ports(args.frontend_port, 1)[0]
            
            if frontend_port != args.frontend_port:
                print_warning(f"Port {args.frontend_port} in use, using {frontend_port}")
            
            frontend_process = launch_frontend(frontend_port, backend_port)
            processes.append(frontend_process)
        
        # Print startup summary
        print_banner("SERVICES STARTED SUCCESSFULLY")
        
        if backend_port:
            print_success(f"Backend API: {Colors.BOLD}http://localhost:{backend_port}{Colors.RESET}")
            print_info(f"  Documentation: http://localhost:{backend_port}/docs")
            print_info(f"  Health Check: http://localhost:{backend_port}/health")
        
        if frontend_port:
            print_success(f"Frontend App: {Colors.BOLD}http://localhost:{frontend_port}{Colors.RESET}")
        
        print_info("\nPress Ctrl+C to stop all services")
        
        # Monitor processes
        import threading
        
        if backend_process:
            backend_thread = threading.Thread(
                target=monitor_process,
                args=(backend_process, "Backend"),
                daemon=True
            )
            backend_thread.start()
        
        if frontend_process:
            frontend_thread = threading.Thread(
                target=monitor_process,
                args=(frontend_process, "Frontend"),
                daemon=True
            )
            frontend_thread.start()
        
        # Keep the script running
        while True:
            time.sleep(1)
            
            # Check if any process died
            if backend_process and backend_process.poll() is not None:
                print_warning("Backend process exited")
                break
            
            if frontend_process and frontend_process.poll() is not None:
                print_warning("Frontend process exited")
                break
    
    except KeyboardInterrupt:
        print_info("\nShutting down services...")
        
        for process in processes:
            try:
                process.terminate()
                process.wait(timeout=5)
                print_success("Process terminated")
            except subprocess.TimeoutExpired:
                process.kill()
                print_warning("Process force-killed")
            except Exception as e:
                print_warning(f"Error terminating process: {e}")
        
        print_success("All services stopped")
        sys.exit(0)
    
    except Exception as e:
        print(f"{Colors.RED}[ERROR] {str(e)}{Colors.RESET}")
        
        for process in processes:
            try:
                process.terminate()
            except Exception:
                pass
        
        sys.exit(1)

if __name__ == "__main__":
    main()
