"""
Standalone .exe builder using PyInstaller
Usage: python build_exe.py
"""
import os
import sys
import subprocess

def build():
    print("🚀 Packaging My Cool Browser Pro into a standalone Windows .exe...")

    # Ensure pyinstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("📦 Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name", "MyCoolBrowser",
        "--add-data", f"src{os.pathsep}src",
        "main.py"
    ]

    print(f"Executing: {' '.join(cmd)}")
    subprocess.check_call(cmd)
    print("\n✨ Build successful!")
    print("📁 Output location: dist/MyCoolBrowser/MyCoolBrowser.exe")

if __name__ == "__main__":
    build()
