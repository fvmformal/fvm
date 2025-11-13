"""
Manage allure as external non-python dependency.

This module manages the installation of Allure Report, and only installs it if
it is not already in the target installation directory. Both allure version and
installation directory can be specified.
"""
import os
import sys
import zipfile
import urllib.request
import shutil
import argparse
import importlib.resources
from pathlib import Path

DEFAULT_ALLURE_VERSION = "2.32.0"

def get_allure_zip_path(allure_version, install_dir):
    """"Get the path to the downloaded zip file"""
    return os.path.join(install_dir, f"allure-{allure_version}.zip")

def get_allure_dir(allure_version, install_dir):
    """Get the path to the allure directory"""
    return os.path.join(install_dir, f'allure-{allure_version}')

def get_allure_bin_path(allure_version, install_dir):
    """Get the path to the allure executable"""
    return os.path.join(install_dir, f'allure-{allure_version}', "bin", "allure")

def download_allure(allure_version, install_dir):
    """Download a specific allure release"""
    allure_download_url = f"https://github.com/allure-framework/allure2/releases/download/{allure_version}/allure-{allure_version}.zip"
    allure_zip_path = get_allure_zip_path(allure_version, install_dir)
    allure_dir = get_allure_dir(allure_version, install_dir)
    print(f"""  Downloading Allure {allure_version} from {allure_download_url}, writing it to {allure_zip_path}""")
    Path(install_dir).mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(allure_download_url, allure_zip_path)

def extract_allure(allure_version, install_dir):
    """Extract the allure zip file"""
    # If a previous installation exists, remove it
    allure_dir = get_allure_dir(allure_version, install_dir)
    if Path(allure_dir).exists():
        shutil.rmtree(allure_dir)

    print("  Extracting Allure...")
    allure_zip_path = get_allure_zip_path(allure_version, install_dir)
    with zipfile.ZipFile(allure_zip_path, "r") as zip_ref:
        zip_ref.extractall(install_dir)

    os.remove(allure_zip_path)

def make_allure_executable(allure_version, install_dir):
    """Make the allure binary executable if necessary"""
    allure_bin = get_allure_bin_path(allure_version, install_dir)
    if sys.platform != "win32":
        os.chmod(allure_bin, 0o755)

def change_logo(allure_version, install_dir):
    """Change Allure logo to FVM logo"""
    # TODO: FVM logo path could change?
    allure_yml = os.path.join(install_dir, f'allure-{allure_version}', 'config', 'allure.yml')
    styles_css = os.path.join(install_dir, f'allure-{allure_version}', 'plugins', 'custom-logo-plugin', 'static', 'styles.css')
    package_data_dir = importlib.resources.files('fvm')
    logo_src = os.path.join(package_data_dir, 'assets', 'FVM_logo_192x192.png')
    logo_dst = os.path.join(install_dir, f'allure-{allure_version}', 'plugins', 'custom-logo-plugin', 'static', 'fvm_logo.png')
    shutil.copy2(logo_src, logo_dst)
    with open(allure_yml, "a", encoding='utf-8') as f:
        print("  - custom-logo-plugin", file=f)
    with open(styles_css, "w", encoding='utf-8') as f:
        print(".side-nav__brand {   background: url('fvm_logo.png') no-repeat center center !important;", file=f)
        print("  margin: 0 auto !important;", file=f)
        print("  height: 40px;", file=f)
        print("  Background-size: contain !important; } ", file=f)
        print("", file=f)
        print(".side-nav__brand span{   display: none } ", file=f)

def create_parser():
    """Create argument parser"""
    parser = argparse.ArgumentParser(description="Install Allure CLI.")
    parser.add_argument(
        "-v", "--allure_version",
        default=DEFAULT_ALLURE_VERSION,
        help="Specific version to download (default: %(default)s)",
    )
    parser.add_argument(
        "-d", "--install_dir",
        default=os.getcwd(),
        help="Directory to install Allure (default: .)",
    )
    parser.add_argument('-f', '--force', default=False, action='store_true',
        help='Install Allure even if it exists in the target directory. (default: %(default)s)'
    )
    return parser

def install_allure(allure_version, install_dir):
    """Install allure"""
    download_allure(allure_version, install_dir)
    extract_allure(allure_version, install_dir)
    make_allure_executable(allure_version, install_dir)
    change_logo(allure_version, install_dir)

def ensure_allure(allure_version, install_dir):
    """Install allure, but only if it is not already installed in the specified
    directory"""
    allure_bin = Path(os.path.join(install_dir, f'allure-{allure_version}', 'bin', 'allure'))
    if not allure_bin.exists():
        install_allure(allure_version, install_dir)

def main():
    """Main function; to use when the python script is directly executed"""
    parser = create_parser()
    args = parser.parse_args()
    print(f'manage_allure.py: {args=}')
    allure_version = args.allure_version
    install_dir = args.install_dir
    force = args.force

    if not os.path.exists(install_dir):
        os.makedirs(install_dir)

    if force:
        print(f"  Installing Allure at {os.path.join(install_dir, f'allure-{allure_version}', 'bin', 'allure')}")
        install_allure(allure_version, install_dir)
    else:
        print(f"  Ensuring Allure is at {os.path.join(install_dir, f'allure-{allure_version}', 'bin', 'allure')}")
        ensure_allure(allure_version, install_dir)

if __name__ == "__main__":
    main()

