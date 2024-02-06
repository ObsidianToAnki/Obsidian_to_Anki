import urllib.request
import sys
import subprocess
import os

SCRIPT_URL = [
    "https://github.com/ObsidianToAnki/Obsidian_to_Anki/releases/latest/download/obsidian_to_anki.py",
    "https://raw.githubusercontent.com/ObsidianToAnki/Obsidian_to_Anki/master/obsidian_to_anki.py",
]


REQUIRE_URL = [
    "https://github.com/ObsidianToAnki/Obsidian_to_Anki/releases/latest/download/requirements.txt",
    "https://raw.githubusercontent.com/ObsidianToAnki/Obsidian_to_Anki/master/requirements.txt",
]

def download_file(urls, filename) :
    for url in urls:
        try:
            with urllib.request.urlopen(url) as response:
                with open(filename, "wb") as f:
                    f.write(response.read())
            print(f"Successfully downloaded {filename}.")
            return True
        except Exception as e:
            print(f"An error occurred while downloading {filename} from {url}: {e}")

    print(f"Failed to download {filename} using all provided URLs.")
    return False

download_file(SCRIPT_URL, "obsidian_to_anki.py")

if download_file(REQUIRE_URL, "obstoankirequire.txt"):
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-r", "obstoankirequire.txt"]
    )
    os.remove("obstoankirequire.txt")