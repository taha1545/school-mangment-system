"""
Build script for creating the executable.
Run this script to build the application.
"""
import os
import shutil
import subprocess

def build_app():
    # Clean previous builds
    for dir_name in ['build', 'dist']:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
    
    # Run PyInstaller
    subprocess.run(['pyinstaller', 'app.spec', '--clean'], check=True)
    
    print("\nBuild completed! The executable is in the 'dist' folder.")
    print("You can run: dist/ناظر المدرسة/ناظر المدرسة.exe")

if __name__ == '__main__':
    build_app()