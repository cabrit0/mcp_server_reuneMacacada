"""
Setup environment for MCP Server.
This script checks for Chrome installation and sets up environment variables.
It also installs required dependencies if they are missing.
"""

import os
import sys
import platform
import subprocess
from pathlib import Path
import importlib.util

def find_chrome_executable():
    """Find Chrome executable on the system."""
    print("Checking for Chrome installation...")

    system = platform.system()
    possible_paths = []

    if system == "Windows":
        possible_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ]
    elif system == "Linux":
        possible_paths = [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
        ]
    elif system == "Darwin":  # macOS
        possible_paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
        ]

    # Check if paths exist
    for path in possible_paths:
        if os.path.exists(path):
            print(f"Found Chrome at: {path}")
            return path

    # Try to find using 'which' command on Unix-like systems
    if system != "Windows":
        try:
            chrome_path = subprocess.check_output(["which", "google-chrome"], text=True).strip()
            if chrome_path:
                print(f"Found Chrome at: {chrome_path}")
                return chrome_path
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        try:
            chromium_path = subprocess.check_output(["which", "chromium"], text=True).strip()
            if chromium_path:
                print(f"Found Chromium at: {chromium_path}")
                return chromium_path
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

    print("Chrome not found on the system.")
    return None

def check_and_install_dependencies():
    """Check for required dependencies and install them if missing."""
    print("Checking for required dependencies...")

    # Check for pyppeteer-stealth
    try:
        importlib.util.find_spec('pyppeteer_stealth')
        print("pyppeteer-stealth is already installed.")
    except ImportError:
        print("pyppeteer-stealth is not installed. Attempting to install...")
        try:
            # Try to install pyppeteer-stealth
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyppeteer-stealth"])
            print("Successfully installed pyppeteer-stealth.")

            # Verify installation
            try:
                importlib.util.find_spec('pyppeteer_stealth')
                print("Verified pyppeteer-stealth installation.")
            except ImportError:
                print("Warning: pyppeteer-stealth was installed but could not be imported.")
                print("This might be due to a dependency issue.")

                # Try alternative installation
                try:
                    print("Trying alternative installation method...")
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "git+https://github.com/pyppeteer/pyppeteer-stealth.git"])
                    print("Successfully installed pyppeteer-stealth from GitHub.")
                except subprocess.SubprocessError as alt_e:
                    print(f"Failed alternative installation: {str(alt_e)}")
        except subprocess.SubprocessError as e:
            print(f"Failed to install pyppeteer-stealth: {str(e)}")
            print("You may need to install it manually with: pip install pyppeteer-stealth")

    # Check for pyppeteer
    try:
        importlib.util.find_spec('pyppeteer')
        print("pyppeteer is already installed.")
    except ImportError:
        print("pyppeteer is not installed. Attempting to install...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyppeteer"])
            print("Successfully installed pyppeteer.")
        except subprocess.SubprocessError as e:
            print(f"Failed to install pyppeteer: {str(e)}")
            print("You may need to install it manually with: pip install pyppeteer")

def setup_environment():
    """Set up environment variables for MCP Server."""
    # Check and install dependencies
    check_and_install_dependencies()

    # Find Chrome executable
    chrome_path = find_chrome_executable()

    if chrome_path:
        # Set environment variable for Chrome executable path
        os.environ["CHROME_EXECUTABLE_PATH"] = chrome_path
        print(f"Set CHROME_EXECUTABLE_PATH={chrome_path}")

        # Skip Chromium download since we have Chrome installed
        os.environ["PYPPETEER_SKIP_CHROMIUM_DOWNLOAD"] = "1"
        os.environ["PUPPETEER_SKIP_CHROMIUM_DOWNLOAD"] = "1"
        os.environ["PUPPETEER_DOWNLOAD_CHROMIUM"] = "False"
        print("Set PYPPETEER_SKIP_CHROMIUM_DOWNLOAD=1")
    else:
        # If Chrome is not found, we'll try to use the downloaded Chromium
        os.environ["PUPPETEER_DOWNLOAD_CHROMIUM"] = "True"
        print("Chrome not found. Will attempt to download Chromium.")

        # Try to set a custom Chromium revision that is known to work
        os.environ["PYPPETEER_CHROMIUM_REVISION"] = "1263111"  # Use a newer revision
        print("Set PYPPETEER_CHROMIUM_REVISION=1263111")

    # Create .env file if it doesn't exist
    env_file = Path(".env")
    if not env_file.exists():
        with open(env_file, "w") as f:
            f.write(f"# Generated by setup_environment.py\n")
            if chrome_path:
                f.write(f"CHROME_EXECUTABLE_PATH={chrome_path}\n")
                f.write(f"PYPPETEER_SKIP_CHROMIUM_DOWNLOAD=1\n")
                f.write(f"PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=1\n")
                f.write(f"PUPPETEER_DOWNLOAD_CHROMIUM=False\n")
            else:
                f.write(f"PUPPETEER_DOWNLOAD_CHROMIUM=True\n")
                f.write(f"PYPPETEER_CHROMIUM_REVISION=1263111\n")
        print(f"Created .env file with Chrome configuration")

if __name__ == "__main__":
    setup_environment()
    print("Environment setup complete.")
