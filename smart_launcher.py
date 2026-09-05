"""Development launcher for the active FastAPI + React stack."""

import argparse
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def free_port(start: int) -> int:
    for port in range(start, 65535):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError("No free port available")


def main() -> None:
    parser = argparse.ArgumentParser(description="Start AssessNex AI locally")
    parser.add_argument("--backend", action="store_true", help="Start backend only")
    parser.add_argument("--frontend", action="store_true", help="Start React frontend only")
    parser.add_argument("--backend-port", type=int, default=8000)
    parser.add_argument("--frontend-port", type=int, default=5173)
    args = parser.parse_args()

    backend_only = args.backend and not args.frontend
    frontend_only = args.frontend and not args.backend
    start_both = not args.backend and not args.frontend

    backend_port = free_port(args.backend_port) if start_both else args.backend_port
    frontend_port = free_port(args.frontend_port) if start_both or frontend_only else args.frontend_port

    env = os.environ.copy()
    env.update(
        {
            "LLM_PROVIDER": "google",
            "ENABLE_PROVIDER_GEMINI": "true",
            "ENABLE_PROVIDER_OPENAI": "false",
            "ENABLE_PROVIDER_GROK": "false",
            "ENABLE_PROVIDER_GROQ": "false",
            "SERVER_HOST": "127.0.0.1",
            "SERVER_PORT": str(backend_port),
            "RELOAD": "true",
        }
    )

    processes = []
    try:
        if not frontend_only:
            print(f"Backend:  http://127.0.0.1:{backend_port}")
            processes.append(
                subprocess.Popen(
                    [
                        sys.executable,
                        "-m",
                        "uvicorn",
                        "backend.app.main:app",
                        "--host",
                        "127.0.0.1",
                        "--port",
                        str(backend_port),
                        "--reload",
                    ],
                    cwd=ROOT,
                    env=env,
                )
            )
            time.sleep(1)

        if not backend_only:
            frontend_env = env.copy()
            frontend_env["VITE_API_BASE_URL"] = f"http://127.0.0.1:{backend_port}/api/v1"
            print(f"React:    http://127.0.0.1:{frontend_port}")
            processes.append(
                subprocess.Popen(
                    ["npm", "run", "dev", "--", "--host", "127.0.0.1", "--port", str(frontend_port)],
                    cwd=ROOT.parent.parent / "ANAI_reactapp",
                    env=frontend_env,
                )
            )

        print("\nAssessNex AI is running. Press Ctrl+C to stop.")
        while True:
            if any(process.poll() is not None for process in processes):
                break
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopping AssessNex AI...")
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()


if __name__ == "__main__":
    main()
