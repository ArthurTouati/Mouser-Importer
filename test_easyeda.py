import sys
import os
import subprocess

def test_easyeda():
    # easyeda2kicad is installed. Let's see its help
    python_exe = sys.executable
    try:
        res = subprocess.run([python_exe, "-m", "easyeda2kicad", "--help"], capture_output=True, text=True)
        print("Help output:", res.stdout)
    except Exception as e:
        print("Error running easyeda2kicad:", e)

if __name__ == "__main__":
    test_easyeda()
