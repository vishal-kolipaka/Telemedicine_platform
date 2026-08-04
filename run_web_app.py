"""
TeleMed AI Healthcare Platform Launcher
========================================
Run this script to start the complete TeleMed platform (Web UI + Backend DocumentReader API).

Usage:
    python run_web_app.py

Then open your browser at:
    http://localhost:8000
"""

import os
import sys
import subprocess
import uvicorn

def main():
    # Build frontend if dist doesn't exist or needs rebuilding
    dist_dir = os.path.join(os.getcwd(), "frontend", "dist")
    if not os.path.exists(dist_dir):
        print("Building React frontend assets...")
        frontend_dir = os.path.join(os.getcwd(), "frontend")
        subprocess.run("npm run build", shell=True, cwd=frontend_dir, check=True)

    print("\n" + "="*70)
    print("  TELEMED AI HEALTHCARE PLATFORM IS RUNNING")
    print("="*70)
    print("\n  Open your web browser and navigate to:")
    print("     -> http://localhost:8000")
    print("     -> http://192.168.29.137:8000 (Local Network / Wi-Fi)\n")
    print("  Press Ctrl+C in this terminal to stop the server.")
    print("="*70 + "\n")

    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, log_level="info")

if __name__ == "__main__":
    main()
