import urllib.request
import sys
import subprocess
import os

SCRIPT_URL = "".join(
    [
        "https://github.com/Pseudonium/Obsidian_to_Anki/releases/latest",
        "/download/obsidian_to_anki.py"
    ]
)

REQUIRE_URL = "".join(
    [
        "https://github.com/Pseudonium/Obsidian_to_Anki/releases/latest",
        "/download/requirements.txt"
    ]
)

with urllib.request.urlopen(SCRIPT_URL) as script:
    with open("obsidian_to_anki.py", "wb") as f:
        f.write(script.read())

with urllib.request.urlopen(REQUIRE_URL) as require:
    with open("obstoankirequire.txt", "wb") as f:
        f.write(require.read())
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-r", "obstoankirequire.txt"]
    )
    os.remove("obstoankirequire.txt")
