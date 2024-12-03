from PyQt5 import QtCore, QtGui, QtWidgets
import os
import requests
import zipfile
import shutil
import tempfile
import subprocess
from colorama import init, Fore, Style
from win32com.client import Dispatch
import pythoncom

class InstallationWorker(QtCore.QThread):
    progress = QtCore.pyqtSignal(int)
    installation_complete = QtCore.pyqtSignal()

    def __init__(self, install_path, create_shortcut, open_app):
        super().__init__()
        self.install_path = install_path
        self.create_shortcut = create_shortcut
        self.open_app = open_app

    def run(self):
        owner = "ULauncher-Github"
        repo = "Unix-Launcher"
        exe_name = "ULauncher.exe"

        install_path = self.install_path or os.getcwd()
        exe_path = self.find_exe_in_folder(install_path, exe_name)

        if exe_path:
            print(Fore.GREEN + f"{exe_name} already exists at {exe_path}.")
            if self.open_app and self.run_app_non_blocking(exe_path, os.path.dirname(exe_path)):
                print(Fore.GREEN + "Application launched successfully.")
                self.installation_complete.emit()
            else:
                print(Fore.RED + f"Failed to launch {exe_name}.")
            return 

        print(Fore.YELLOW + f"{exe_name} not found. Proceeding with installation...")

        release_data = self.get_latest_release(owner, repo)
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

        if not os.path.exists(install_path):
            print(Fore.CYAN + f"Creating installation directory: {install_path}")
            os.makedirs(install_path)

        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, asset_name)

        if not self.download_file(asset_url, zip_path):
            self.clean_up(temp_dir)
            return

        if not self.extract_zip(zip_path, install_path):
            self.clean_up(temp_dir)
            return

        exe_path = self.find_exe_in_folder(install_path, exe_name)
        if not exe_path:
            print(Fore.RED + f"Could not find {exe_name} in the extracted files.")
            self.clean_up(temp_dir)
            return

        exe_folder = os.path.dirname(exe_path)

        if self.create_shortcut:
            self.create_shortcut_function(exe_path)

        if self.open_app and not self.run_app_non_blocking(exe_path, exe_folder):
            self.clean_up(temp_dir)
            return

        self.clean_up(temp_dir)
        print(Fore.GREEN + "Installation completed successfully!")
        self.installation_complete.emit()

    def get_latest_release(self, owner, repo):
        url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
        try:
            response = requests.get(url)
            response.raise_for_status()
            release_data = response.json()
            return release_data
        except requests.RequestException as e:
            print(Fore.RED + f"Error fetching latest release: {e}")
        return None

    def download_file(self, url, dest_path):
        try:
            print(Fore.CYAN + f"Downloading file from {url}...")
            response = requests.get(url, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0

            with open(dest_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
                        downloaded_size += len(chunk)
                        progress_percentage = int((downloaded_size / total_size) * 100)
                        self.progress.emit(progress_percentage)

            print(Fore.GREEN + f"File downloaded to {dest_path}.")
        except requests.RequestException as e:
            print(Fore.RED + f"Error downloading file: {e}")
            return False
        return True

    def extract_zip(self, zip_path, extract_to):
        print(Fore.CYAN + f"Extracting {zip_path} to {extract_to}...")
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
            print(Fore.GREEN + f"Extraction complete. Files are now in {extract_to}.")
        except zipfile.BadZipFile as e:
            print(Fore.RED + f"Error extracting ZIP file: {e}")
            return False
        return True

    def find_exe_in_folder(self, folder_path, exe_name):
        for root, dirs, files in os.walk(folder_path):
            if exe_name in files:
                return os.path.join(root, exe_name)
        return None

    def run_app_non_blocking(self, exe_path, working_directory):
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

    def create_shortcut_function(self, exe_path):
        pythoncom.CoInitialize()

        try:
            shortcut_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop', "Unix Launcher.lnk")
            install_path = self.install_path or os.getcwd()
            exe_path = self.find_exe_in_folder(install_path, "ULauncher.exe")
            
            print(Fore.CYAN + f"Creating shortcut at {shortcut_path}...")
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            
            shortcut.TargetPath = exe_path
            shortcut.WorkingDirectory = os.path.dirname(exe_path)
            shortcut.save()
            
            print(Fore.GREEN + "Shortcut created.")
        
        finally:
            pythoncom.CoUninitialize()

    def clean_up(self, temp_folder):
        print(Fore.CYAN + "Cleaning up temporary files...")
        if os.path.exists(temp_folder):
            shutil.rmtree(temp_folder)
        print(Fore.GREEN + "Cleanup complete.")

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        self.install_path = os.getcwd()

        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(574, 185)
        MainWindow.setMinimumSize(QtCore.QSize(574, 185))
        MainWindow.setMaximumSize(QtCore.QSize(574, 185))
        MainWindow.setStyleSheet("background-color: rgb(41, 46, 49);")
        MainWindow.setWindowTitle("Unix-Setup")
        icon_path = "assets/Icon.png"
        icon = QtGui.QIcon(icon_path)
        MainWindow.setWindowIcon(icon)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        self.logo = QtWidgets.QLabel(self.centralwidget)
        self.logo.setGeometry(QtCore.QRect(32, 13, 523, 63))
        self.logo.setStyleSheet("background: transparent;")
        self.logo.setText("")
        self.logo.setPixmap(QtGui.QPixmap("assets/Logo.png"))
        self.logo.setObjectName("logo")

        self.installButton = QtWidgets.QPushButton(self.centralwidget)
        self.installButton.setGeometry(QtCore.QRect(29, 89, 246, 34))
        self.installButton.setStyleSheet("QPushButton {\n"
        "    background-color: rgba(70, 173, 226, 1);\n"
        "    border-radius: 7px;\n"
        "    border: 2px solid black;\n"
        "    font: 63 14pt \"Bahnschrift SemiBold\";\n"
        "    color: white;\n"
        "}\n"
        "\n"
        "QPushButton:Hover {\n"
        "    background-color: rgba(56, 139, 181, 1)\n"
        "}")
        self.installButton.setObjectName("installButton")
        self.installButton.clicked.connect(self.start_installation)

        self.pathButton = QtWidgets.QPushButton(self.centralwidget)
        self.pathButton.setGeometry(QtCore.QRect(287, 89, 34, 34))
        self.pathButton.setStyleSheet("QPushButton {\n"
        "    background-color: rgba(70, 173, 226, 1);\n"
        "    border-radius: 7px;\n"
        "    border: 2px solid black;\n"
        "    font: 63 16pt \"Bahnschrift SemiBold\";\n"
        "    color: white;\n"
        "}\n"
        "\n"
        "QPushButton:Hover {\n"
        "    background-color: rgba(56, 139, 181, 1)\n"
        "}")
        self.pathButton.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("assets/folderIcon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pathButton.setIcon(icon)
        self.pathButton.setIconSize(QtCore.QSize(19, 17))
        self.pathButton.setObjectName("pathButton")
        self.pathButton.clicked.connect(self.select_install_path)

        self.progressBar = QtWidgets.QProgressBar(self.centralwidget)
        self.progressBar.setGeometry(QtCore.QRect(29, 138, 292, 34))
        self.progressBar.setStyleSheet("QProgressBar {\n"
        "    border: 2px solid #fff;\n"
        "    border-radius: 9px;           \n"
        "    text-align: center; \n"
        "    color: white;           \n"
        "    background-color: transparent;\n"
        "    padding: 4px;           \n"
        "    font: 63 14pt \"Bahnschrift SemiBold\";\n"
        "}\n"
        "\n"
        "QProgressBar::chunk {\n"
        "    background-color: #00B051;\n"
        "    border-radius: 7px; \n"
        "}\n"
        "")
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName("progressBar")

        self.pathText = QtWidgets.QLabel(self.centralwidget)
        self.pathText.setGeometry(QtCore.QRect(277, 75, 59, 12))
        self.pathText.setStyleSheet("background: transparent; color: white;")
        self.pathText.setText("Select Path")

        self.shortcutCheckBox = QtWidgets.QCheckBox(self.centralwidget)
        self.shortcutCheckBox.setGeometry(QtCore.QRect(330, 93, 221, 31))
        self.shortcutCheckBox.setStyleSheet("""
            QCheckBox {
                font: 63 12pt "Bahnschrift SemiBold";
                background: transparent;
                padding: 2px;
                color: white;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid white;
                background-color: none;
                border-radius: 7px;                                            
            }
            QCheckBox::indicator:checked {
                border: 2px solid white;
                background-color: none;
                border-radius: 7px;
                image: url(assets/CheckMark.svg);
            }
        """)
        self.shortcutCheckBox.setObjectName("shortcutCheckBox")

        self.appCheckBox = QtWidgets.QCheckBox(self.centralwidget)
        self.appCheckBox.setGeometry(QtCore.QRect(330, 141, 231, 31))
        self.appCheckBox.setStyleSheet("""
            QCheckBox {
                font: 63 12pt "Bahnschrift SemiBold";
                background: transparent;
                padding: 2px;
                color: white;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid white;
                background-color: none;
                border-radius: 7px;                                            
            }
            QCheckBox::indicator:checked {
                border: 2px solid white;
                background-color: none;
                border-radius: 7px;
                image: url(assets/CheckMark.svg);
            }
        """)

        MainWindow.setCentralWidget(self.centralwidget)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        self.installButton.setText("Install")
        self.shortcutCheckBox.setText("Create a desktop shortcut")
        self.appCheckBox.setText("Open program after install")

    def select_install_path(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(
            None, "Select Installation Directory", os.getcwd()
        )
        if path:
            self.install_path = path

    def start_installation(self):
        self.installButton.setEnabled(False)
        self.installButton.setStyleSheet("background-color: grey; border-radius: 7px; border: 2px solid black; font: 63 14pt 'Bahnschrift SemiBold'; color: white;")
        self.pathButton.setEnabled(False)
        self.pathButton.setStyleSheet("background-color: grey; border-radius: 7px; border: 2px solid black; font: 63 14pt 'Bahnschrift SemiBold'; color: white;")
        create_shortcut = self.shortcutCheckBox.isChecked()
        open_app = self.appCheckBox.isChecked()
        self.worker = InstallationWorker(self.install_path or os.getcwd(), create_shortcut, open_app)
        self.worker.installation_complete.connect(self.close_application)
        self.worker.progress.connect(self.progressBar.setValue)
        self.worker.installation_complete.connect(self.enable_install_button)
        self.worker.start()

    def enable_install_button(self):
        self.installButton.setEnabled(True)
        self.installButton.setStyleSheet("background-color: rgba(70, 173, 226, 1); border-radius: 7px; border: 2px solid black; font: 63 14pt 'Bahnschrift SemiBold'; color: white;")
        self.pathButton.setEnabled(True)
        self.pathButton.setStyleSheet("background: transparent; color: white;")

    def close_application(self):
        MainWindow.close()

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
