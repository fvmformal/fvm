import os
import sys
import zipfile
import urllib.request
import shutil
import argparse
from pathlib import Path

ALLURE_VERSION = "2.32.0"
ALLURE_DOWNLOAD_URL = f"https://github.com/allure-framework/allure2/releases/download/{ALLURE_VERSION}/allure-{ALLURE_VERSION}.zip"

def download_allure(install_dir):
    print(f"Downloading Allure {ALLURE_VERSION}...")
    allure_zip_path = os.path.join(install_dir, "allure.zip")
    urllib.request.urlretrieve(ALLURE_DOWNLOAD_URL, allure_zip_path)

def extract_allure(install_dir):
    print("Extracting Allure...")
    with zipfile.ZipFile(os.path.join(install_dir, "allure.zip"), "r") as zip_ref:
        zip_ref.extractall(install_dir)

    allure_dir = os.path.join(install_dir, 'allure')

    # If a previous installation exists, remove it
    if Path(allure_dir).exists():
        shutil.rmtree(allure_dir)

    shutil.move(os.path.join(install_dir, f'allure-{ALLURE_VERSION}'), os.path.join(install_dir, 'allure'))
    os.remove(os.path.join(install_dir, "allure.zip"))

def make_allure_executable(install_dir):
    # Make the allure binary executable if necessary
    allure_bin = os.path.join(install_dir, f'allure', "bin", "allure")
    if sys.platform != "win32":
        os.chmod(allure_bin, 0o755)

def main():
    parser = argparse.ArgumentParser(description="Install Allure CLI.")
    parser.add_argument(
        "install_dir",
        nargs="?",
        default=os.getcwd(),
        help="Directory to install Allure (default: .)",
    )

    args = parser.parse_args()
    print(f'{args.install_dir=}')
    install_dir = args.install_dir

    if not os.path.exists(install_dir):
        os.makedirs(install_dir)

    download_allure(install_dir)
    extract_allure(install_dir)
    make_allure_executable(install_dir)
    print(f"Allure installed at {install_dir}/allure-{ALLURE_VERSION}/bin/allure")

if __name__ == "__main__":
    main()

