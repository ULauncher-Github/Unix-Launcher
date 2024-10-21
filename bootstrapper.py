import os
import requests
import zipfile
import shutil
import tempfile
import subprocess
from colorama import init, Fore, Style

init(autoreset=True)

def get_latest_release(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    try:
        response = requests.get(url)
        response.raise_for_status()
        release_data = response.json()
        return release_data
    except requests.RequestException as e:
        print(Fore.RED + f"Error fetching latest release: {e}")
        return None

def download_file(url, dest_path):
    try:
        print(Fore.CYAN + f"Downloading file from {url}...")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(dest_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(Fore.GREEN + f"File downloaded to {dest_path}.")
    except requests.RequestException as e:
        print(Fore.RED + f"Error downloading file: {e}")
        return False
    return True

def extract_zip(zip_path, extract_to):
    print(Fore.CYAN + f"Extracting {zip_path} to {extract_to}...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(Fore.GREEN + f"Extraction complete. Files are now in {extract_to}.")
    except zipfile.BadZipFile as e:
        print(Fore.RED + f"Error extracting ZIP file: {e}")
        return False
    return True

def find_exe_in_folder(folder_path, exe_name):
    for root, dirs, files in os.walk(folder_path):
        if exe_name in files:
            return os.path.join(root, exe_name)
    return None

def run_app_non_blocking(exe_path, working_directory):
    if not os.path.exists(exe_path):
        print(Fore.RED + f"Executable {exe_path} not found.")
        return False
    try:
        print(Fore.CYAN + f"Running application: {exe_path} from {working_directory}")
        subprocess.Popen([exe_path], cwd=working_directory)
        print(Fore.GREEN + "Application started successfully.")
    except Exception as e:
        print(Fore.RED + f"Error running the application: {e}")
        return False
    return True

def clean_up(temp_folder):
    print(Fore.CYAN + "Cleaning up temporary files...")
    if os.path.exists(temp_folder):
        shutil.rmtree(temp_folder)
    print(Fore.GREEN + "Cleanup complete.")

def main():
    owner = "ULauncher-Github"
    repo = "Unix-Launcher"
    exe_name = "ULauncher.exe"

    release_data = get_latest_release(owner, repo)
    if not release_data:
        return

    assets = release_data.get('assets', [])
    if not assets:
        print(Fore.RED + "No assets found in the latest release.")
        return
    
    asset_url = assets[0]['browser_download_url']
    asset_name = assets[0]['name']

    print(Fore.YELLOW + f"Latest release: {release_data['name']}")
    print(Fore.YELLOW + f"Downloading asset: {asset_name}")

    install_path = input(Fore.YELLOW + "Enter the installation path (default: current directory): ")
    if not install_path:
        install_path = os.getcwd()
    
    if not os.path.exists(install_path):
        print(Fore.CYAN + f"Creating installation directory: {install_path}")
        os.makedirs(install_path)

    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, asset_name)

    if not download_file(asset_url, zip_path):
        clean_up(temp_dir)
        return

    if not extract_zip(zip_path, install_path):
        clean_up(temp_dir)
        return

    exe_path = find_exe_in_folder(install_path, exe_name)
    if not exe_path:
        print(Fore.RED + f"Could not find {exe_name} in the extracted files.")
        clean_up(temp_dir)
        return

    exe_folder = os.path.dirname(exe_path)
    if not run_app_non_blocking(exe_path, exe_folder):
        clean_up(temp_dir)
        return

    clean_up(temp_dir)
    print(Fore.GREEN + "Installation completed successfully!")

if __name__ == "__main__":
    main()
