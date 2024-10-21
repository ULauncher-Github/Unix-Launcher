from PyQt5 import QtCore, QtGui, QtWidgets
import os
import subprocess
from uuid import uuid1
from random_username.generate import generate_username
import minecraft_launcher_lib
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QApplication, QComboBox, QStyledItemDelegate, QVBoxLayout, QWidget, QLineEdit
from PyQt5.QtCore import Qt, QPoint

class CenterDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = Qt.AlignCenter

class LaunchThread(QtCore.QThread):
    launch_setup_signal = QtCore.pyqtSignal(str, str, str)  
    progress_update_signal = QtCore.pyqtSignal(int, int, str)
    state_update_signal = QtCore.pyqtSignal(bool)
    stop_signal = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.version_id = ''
        self.username = ''
        self.progress = 0
        self.progress_max = 0
        self.progress_label = ''
        self.stopping = False
        self.loader_type = 'Vanilla'  
        self.launch_setup_signal.connect(self.launch_setup)
        self.stop_signal.connect(self.stop_launch)

    def launch_setup(self, version_id, username, loader_type='Vanilla'):
        self.version_id = version_id
        self.username = username
        self.loader_type = loader_type  
        self.stopping = False

    def update_progress_label(self, value):
        self.progress_label = value
        self.progress_update_signal.emit(self.progress, self.progress_max, self.progress_label)

    def update_progress(self, value):
        self.progress = value
        self.progress_update_signal.emit(self.progress, self.progress_max, self.progress_label)

    def update_progress_max(self, value):
        self.progress_max = value
        self.progress_update_signal.emit(self.progress, self.progress_max, self.progress_label)

    def stop_launch(self):
        self.stopping = True
        self.terminate()

    def install_forge(self, minecraft_directory):
        self.update_progress_label("Fetching Forge versions")
        try:
            forge_version = minecraft_launcher_lib.forge.find_forge_version(self.version_id)
            

            if forge_version is None:
                print("This Minecraft Version is not supported by Forge")
                return


            print(f"Available Forge versions: {forge_version}")
            print(f"Installing Forge version: {forge_version}")


            minecraft_launcher_lib.forge.install_forge_version(
                forge_version,
                minecraft_directory,
                callback={
                    'setStatus': self.update_progress_label,
                    'setProgress': self.update_progress,
                    'setMax': self.update_progress_max
                }
            )
        except Exception as e:
            print(f"Error during Forge installation: {str(e)}")
            return False
        return True

    def run(self):

        minecraft_version = self.version_id

        minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory().replace('minecraft', 'unixlauncher')
        self.state_update_signal.emit(True)

        try:

            minecraft_launcher_lib.install.install_minecraft_version(
                versionid=minecraft_version,
                minecraft_directory=minecraft_directory,
                callback={
                    'setStatus': self.update_progress_label,
                    'setProgress': self.update_progress,
                    'setMax': self.update_progress_max
                }
            )


            if self.loader_type == 'Forge':
                forge_installed = self.install_forge(minecraft_directory)
                if not forge_installed:
                    return


                forge_version_id = minecraft_launcher_lib.forge.find_forge_version(minecraft_version)
                if forge_version_id:
                    self.version_id = forge_version_id
                else:
                    raise Exception("Could not find Forge version")

            if not self.username:
                self.username = generate_username()[0]

            options = {
                'username': self.username,
                'uuid': str(uuid1()),
                'token': ""
            }


            command = minecraft_launcher_lib.command.get_minecraft_command(
                version=self.version_id,
                minecraft_directory=minecraft_directory,
                options=options
            )


            if not self.stopping:
                subprocess.Popen(command, creationflags=subprocess.CREATE_NO_WINDOW)

        except Exception as e:
            print(f"Error during Minecraft launch: {str(e)}")

        finally:
            self.state_update_signal.emit(False)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        latest_version = minecraft_launcher_lib.utils.get_latest_version()

        MainWindow.setWindowTitle("Unix Launcher")
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(980, 538)
        MainWindow.setMinimumSize(QtCore.QSize(980, 538))
        MainWindow.setMaximumSize(QtCore.QSize(980, 538))
        MainWindow.setStyleSheet("background-color: rgb(41, 46, 49);")
        MainWindow.setUnifiedTitleAndToolBarOnMac(False)
        MainWindow.setWindowFlags(Qt.FramelessWindowHint)
        icon_path = "assets/Icon.png"
        icon = QtGui.QIcon(icon_path)
        MainWindow.setWindowIcon(icon)

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.TopbarBG = QtWidgets.QLabel(self.centralwidget)
        self.TopbarBG.setGeometry(QtCore.QRect(0, 0, 980, 56))
        self.TopbarBG.setStyleSheet("background-color: rgba(33, 36, 41, 1)")
        self.TopbarBG.setText("")
        self.TopbarBG.setObjectName("TopbarBG")
        self.TopbarBG.mousePressEvent = self.mousePressEvent
        self.TopbarBG.mouseMoveEvent = self.mouseMoveEvent
        self.TopbarBG.mouseReleaseEvent = self.mouseReleaseEvent

        self.Logo = QtWidgets.QLabel(self.centralwidget)
        self.Logo.setGeometry(QtCore.QRect(10, 10, 306, 37))
        self.Logo.setStyleSheet("background-color: rgba(255, 255, 255, 0);")
        self.Logo.setText("")
        self.Logo.setPixmap(QtGui.QPixmap("assets/Logo.png"))
        self.Logo.setObjectName("Logo")

        self.closeButton = QtWidgets.QPushButton(self.centralwidget)
        self.closeButton.setGeometry(QtCore.QRect(931, 8, 40, 40))
        self.closeButton.setStyleSheet("background-color: rgba(255, 255, 255, 0);")
        self.closeButton.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("assets/CloseButton.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.closeButton.setIcon(icon)
        self.closeButton.setIconSize(QtCore.QSize(40, 40))
        self.closeButton.setFlat(False)
        self.closeButton.setObjectName("closeButton")
        self.closeButton.enterEvent=self.CloseButtonEnterEvent
        self.closeButton.leaveEvent=self.CloseButtonLeaveEvent
        self.closeButton.clicked.connect(self.close_window)

        self.collapseButton = QtWidgets.QPushButton(self.centralwidget)
        self.collapseButton.setGeometry(QtCore.QRect(891, 26, 24, 4))
        self.collapseButton.setStyleSheet("background-color: rgba(255, 255, 255, 0);")
        self.collapseButton.setText("")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap("assets/CollapseButton.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.collapseButton.setIcon(icon1)
        self.collapseButton.setIconSize(QtCore.QSize(24, 4))
        self.collapseButton.setObjectName("collapseButton")
        self.collapseButton.enterEvent=self.CollapseButtonEnterEvent
        self.collapseButton.leaveEvent=self.CollapseButtonLeaveEvent
        self.collapseButton.clicked.connect(self.minimize_window) 

        self.playButton = QtWidgets.QPushButton(self.centralwidget)
        self.playButton.setGeometry(QtCore.QRect(708, 468, 246, 38))
        self.playButton.setStyleSheet("QPushButton {\n"
                                        "    background-color: rgba(70, 173, 226, 1);\n"
                                        "    border-radius: 7px;\n"
                                        "    font: 63 20pt \"Bahnschrift SemiBold\";\n"
                                        "    color: white;\n"
                                        "}\n"
                                        "\n"
                                        "QPushButton:Hover {\n"
                                        "    background-color: rgba(56, 139, 181, 1)\n"
                                        "}")
        self.playButton.setIconSize(QtCore.QSize(16, 16))
        self.playButton.setObjectName("playButton")
        self.playButton.clicked.connect(self.launch_game)

        self.folderButton = QtWidgets.QPushButton(self.centralwidget)
        self.folderButton.setGeometry(QtCore.QRect(948, 509, 22, 22))
        self.folderButton.setStyleSheet("background-color: rgba(255, 255, 255, 0);background-color: rgba(255, 255, 255, 0);")
        self.folderButton.setText("")
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap("assets/FolderButton.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.folderButton.setIcon(icon2)
        self.folderButton.setIconSize(QtCore.QSize(22, 22))
        self.folderButton.setObjectName("folderButton")
        self.folderButton.enterEvent=self.folderButtonEnterEvent
        self.folderButton.leaveEvent=self.folderButtonLeaveEvent
        self.folderButton.clicked.connect(self.open_directory)

        self.GeneralBG = QtWidgets.QLabel(self.centralwidget)
        self.GeneralBG.setGeometry(QtCore.QRect(686, 60, 290, 474))
        self.GeneralBG.setFocusPolicy(QtCore.Qt.NoFocus)
        self.GeneralBG.setStyleSheet("QLabel{\n"
                                        "    background-color: rgba(35, 39, 43, 1);\n"
                                        "    border-radius: 9px;\n"
                                        "}\n"
                                        "")
        self.GeneralBG.setText("")
        self.GeneralBG.setObjectName("GeneralBG")

        self.stopButton = QtWidgets.QPushButton(self.centralwidget)
        self.stopButton.setEnabled(True)
        self.stopButton.setGeometry(QtCore.QRect(708, 468, 246, 38))
        self.stopButton.setStyleSheet("QPushButton {\n"
                                        "    background-color: rgba(226, 70, 70, 1);\n"
                                        "    border-radius: 7px;\n"
                                        "    font: 63 20pt \"Bahnschrift SemiBold\";\n"
                                        "    color: white\n"
                                        "}\n"
                                        "\n"
                                        "QPushButton:Hover {\n"
                                        "    background-color:rgba(157, 54, 54, 1)\n"
                                        "}")
        self.stopButton.setIconSize(QtCore.QSize(16, 16))
        self.stopButton.setObjectName("stopButton")
        self.stopButton.setVisible(False)
        self.stopButton.clicked.connect(self.stop_game)

        self.previewImage = QtWidgets.QLabel(self.centralwidget)
        self.previewImage.setGeometry(QtCore.QRect(705, 70, 256, 144))
        self.previewImage.setStyleSheet("background-color: rgba(0, 0, 0,0);")
        self.previewImage.setText("")
        self.previewImage.setPixmap(QtGui.QPixmap("assets/PreviewImg_1.png"))
        self.previewImage.setObjectName("previewImage")

        self.nicknameEdit = QtWidgets.QLineEdit(self.centralwidget)
        self.nicknameEdit.setGeometry(QtCore.QRect(708, 420, 246, 38))
        self.nicknameEdit.setStyleSheet("QLineEdit {\n"
                                        "    background-color: rgba(255, 255, 255, 0);\n"
                                        "    border-radius: 7px;\n"
                                        "    border: 2px solid white;\n"
                                        "    color: white;\n"
                                        "    font: 63 12pt \"Bahnschrift SemiBold\";\n"
                                        "    text-align: center;\n"
                                        "}")
        self.nicknameEdit.setAlignment(QtCore.Qt.AlignCenter)
        self.nicknameEdit.setObjectName("nicknameEdit")

        self.versionSelectBox = QtWidgets.QComboBox(self.centralwidget)
        self.versionSelectBox.setGeometry(QtCore.QRect(708, 370, 246, 38))
        self.versionSelectBox.setStyleSheet("""
        QComboBox {
                background-color: rgba(255, 255, 255, 0);
                border-radius: 7px;
                border: 2px solid white;
                color: white;
                font: 63 12pt "Bahnschrift SemiBold";
                text-align: center;
                padding: 5px;
        }
            QComboBox::drop-down {
                background: transparent;
                border: none;
            }

            QComboBox::down-arrow {
                width: 14px;
                height: 14px;
            }

            QComboBox::down-arrow:on { /* Arrow styling when clicked */
                top: 1px;  /* Adjust to simulate arrow movement */
            }

            QAbstractItemView {
                background: rgba(44, 44, 44, 1);
                border: none;
                color: white;
                selection-background-color: #555555;  /* Selected item background */
                selection-color: white;  /* Text color for selected item */
                border-radius: 5px;  /* Smooth corners for the dropdown */
                padding: 5px;
            }

            QScrollBar:vertical {
                border: none;
                background: #2f2f2f;  /* Dark background for the scrollbar */
                width: 12px;
                margin: 0px;
                border-radius: 6px;  /* Rounded scrollbar for modern design */
            }

            QScrollBar::handle:vertical {
                background-color: #888888;  /* Mid-gray color for the handle */
                min-height: 20px;
                border-radius: 6px;  /* Rounded handle */
            }

            QScrollBar::handle:vertical:hover {
                background-color: #555555;  /* Darker handle on hover */
            }

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;  /* Hide the up/down buttons */
            }

            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;  /* Transparent background behind the handle */
            }
        """)
        self.versionSelectBox.setEditable(True)
        line_edit = self.versionSelectBox.lineEdit()
        line_edit.setAlignment(Qt.AlignCenter)
        line_edit.setReadOnly(True)
        delegate = CenterDelegate(self.versionSelectBox)
        self.versionSelectBox.setItemDelegate(delegate)
        self.versionSelectBox.setObjectName("versionSelectBox")

        for version in minecraft_launcher_lib.utils.get_version_list():
            self.versionSelectBox.addItem(version["id"])
        
        self.versionInfo = QtWidgets.QLabel(self.centralwidget)
        self.versionInfo.setGeometry(QtCore.QRect(705, 220, 256, 31))
        self.versionInfo.setStyleSheet("QLabel{\n"
                                        "    background-color: rgba(255, 255, 255, 0);\n"
                                        "    color: white;\n"
                                        "    font: 63 20pt \"Bahnschrift SemiBold\";\n"
                                        "    text-align: center;\n"
                                        "}")
        self.versionInfo.setAlignment(QtCore.Qt.AlignCenter)
        self.versionInfo.setObjectName("versionInfo")
        self.versionInfo.setText(self.versionSelectBox.currentText())

        self.loaderInfo = QtWidgets.QLabel(self.centralwidget)
        self.loaderInfo.setGeometry(QtCore.QRect(705, 250, 256, 21))
        self.loaderInfo.setStyleSheet("QLabel{\n"
                                        "    background-color: rgba(255, 255, 255, 0);\n"
                                        "    color: white;\n"
                                        "    font: 63 14pt \"Bahnschrift SemiBold\";\n"
                                        "    text-align: center;\n"
                                        "}")
        self.loaderInfo.setAlignment(QtCore.Qt.AlignCenter)
        self.loaderInfo.setObjectName("loaderInfo")
        self.loaderInfo.setText("Loader: Vanilla")

        self.progressBar = QtWidgets.QProgressBar(self.centralwidget)
        self.progressBar.setGeometry(QtCore.QRect(708, 320, 246, 38))
        self.progressBar.setStyleSheet("""
        QProgressBar {
                background-color: rgba(255, 255, 255, 0);
                border-radius: 7px;
                border: 2px solid white;
                color: white;
                font: 63 12pt "Bahnschrift SemiBold";
                text-align: center;
                padding: 4px;
        }
        QProgressBar::chunk {
                background-color: #00B051;
                border-radius: 7px; 
        }
        """)
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName("progressBar")
        self.progressBar.setVisible(False)

        self.notWorkingWarn=QtWidgets.QLabel(self.centralwidget)
        self.notWorkingWarn.setGeometry(QtCore.QRect(20, 50, 300, 60))
        self.notWorkingWarn.setText("Warning! Loader select are not working correctly.")
        self.notWorkingWarn.setStyleSheet("""
                    color: white;                      
        """)

        self.forgeButton = QtWidgets.QPushButton(self.centralwidget)
        self.forgeButton.setGeometry(QtCore.QRect(20, 100, 100, 40))
        self.forgeButton.setStyleSheet("QPushButton {\n"
                                       "    background-color: rgba(0,0,0,0);\n"
                                       "    color: white;\n"
                                       "    border: 2px solid #cccccc;\n"
                                       "    border-radius: 9px;\n"
                                       "    padding: 5px;\n"
                                       "    font-size: 18px;\n"
                                       "}\n"
                                       "QPushButton:hover {\n"
                                       "    background-color: #555;\n"
                                       "}")
        self.forgeButton.setText("Forge")
        self.forgeButton.setObjectName("forgeButton")
        self.forgeButton.clicked.connect(self.select_forge)

        self.quiltButton = QtWidgets.QPushButton(self.centralwidget)
        self.quiltButton.setGeometry(QtCore.QRect(20, 150, 100, 40))
        self.quiltButton.setStyleSheet("QPushButton {\n"
                                       "    background-color: rgba(0,0,0,0);\n"
                                       "    color: white;\n"
                                       "    border: 2px solid #cccccc;\n"
                                       "    border-radius: 9px;\n"
                                       "    padding: 5px;\n"
                                       "    font-size: 18px;\n"
                                       "}\n"
                                       "QPushButton:hover {\n"
                                       "    background-color: #555;\n"
                                       "}")
        self.quiltButton.setText("Quilt")
        self.quiltButton.setObjectName("quiltButton")
        self.quiltButton.clicked.connect(self.select_quilt)

        self.fabricButton = QtWidgets.QPushButton(self.centralwidget)
        self.fabricButton.setGeometry(QtCore.QRect(20, 200, 100, 40))
        self.fabricButton.setStyleSheet("QPushButton {\n"
                                        "    background-color: rgba(0,0,0,0);\n"
                                        "    color: white;\n"
                                        "    border: 2px solid #cccccc;\n"
                                        "    border-radius: 9px;\n"
                                        "    padding: 5px;\n"
                                        "    font-size: 18px;\n"
                                        "}\n"
                                        "QPushButton:hover {\n"
                                        "    background-color: #555;\n"
                                        "}")
        self.fabricButton.setText("Fabric")
        self.fabricButton.setObjectName("fabricButton")
        self.fabricButton.clicked.connect(self.select_fabric)

        self.VanillaButton = QtWidgets.QPushButton(self.centralwidget)
        self.VanillaButton.setGeometry(QtCore.QRect(20, 250, 100, 40))
        self.VanillaButton.setStyleSheet("QPushButton {\n"
                                        "    background-color: rgba(0,0,0,0);\n"
                                        "    color: white;\n"
                                        "    border: 2px solid #cccccc;\n"
                                        "    border-radius: 9px;\n"
                                        "    padding: 5px;\n"
                                        "    font-size: 18px;\n"
                                        "}\n"
                                        "QPushButton:hover {\n"
                                        "    background-color: #555;\n"
                                        "}")
        self.VanillaButton.setText("Vanilla")
        self.VanillaButton.setObjectName("VanillaButton")
        self.VanillaButton.clicked.connect(self.select_Vanilla)

        self.dropdownarrowicon = QtWidgets.QLabel(self.centralwidget)
        self.dropdownarrowicon.setGeometry(QtCore.QRect(935, 374, 16, 31))
        self.dropdownarrowicon.setText("")
        self.dropdownarrowicon.setPixmap(QtGui.QPixmap("assets/arrow_down.png"))
        self.dropdownarrowicon.setStyleSheet("""
        background-color: rgba(255,255,255,0);

                                             """)
        self.dropdownarrowicon.setAlignment(QtCore.Qt.AlignCenter)
        self.dropdownarrowicon.setObjectName("dropdownarrowicon")

        self.GeneralBG.raise_()
        self.TopbarBG.raise_()
        self.Logo.raise_()
        self.dropdownarrowicon.raise_()
        self.closeButton.raise_()
        self.VanillaButton.raise_()
        self.forgeButton.raise_()
        self.quiltButton.raise_()
        self.fabricButton.raise_()
        self.collapseButton.raise_()
        self.playButton.raise_()
        self.folderButton.raise_()
        self.stopButton.raise_()
        self.previewImage.raise_()
        self.nicknameEdit.raise_()
        self.versionSelectBox.raise_()
        self.versionInfo.raise_()
        self.loaderInfo.raise_()
        self.progressBar.raise_()

        self.playButton.setText("Play")
        self.stopButton.setText("Stop")
        self.nicknameEdit.setPlaceholderText("Enter nickname")

        MainWindow.setCentralWidget(self.centralwidget)

        self.launch_thread = LaunchThread()
        self.launch_thread.progress_update_signal.connect(self.update_progress)
        self.launch_thread.state_update_signal.connect(self.state_update)
        self.timer = QTimer()
        self.timer.timeout.connect(self.hide_progress_bar)

        self.create_unixlauncher_directory()

        saved_username = self.load_username()
        if saved_username:
            self.nicknameEdit.setText(saved_username)

        self.versionSelectBox.currentIndexChanged.connect(self.update_version_info)

        self.is_dragging = False
        self.drag_start_pos = None
        
    #Main Functions:
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.is_dragging = True
            self.drag_start_pos = event.globalPos() - MainWindow.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            MainWindow.move(event.globalPos() - self.drag_start_pos)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.is_dragging = False

    def hide_progress_bar(self):
        self.progressBar.setVisible(False)

    def save_username(self, username):
        with open("saved_username.txt", "w") as file:
            file.write(username)

    def load_username(self):
        if os.path.exists("saved_username.txt"):
            with open("saved_username.txt", "r") as file:
                return file.read().strip()
        return None

    def launch_game(self):
        self.progressBar.setVisible(True)
        username = self.nicknameEdit.text()
        if username:
            self.save_username(username)
        loader_type = self.loaderInfo.text().split(": ")[-1]  # Получение типа загрузчика из loaderInfo
        self.launch_thread.launch_setup_signal.emit(self.versionSelectBox.currentText(), username, loader_type)
        self.launch_thread.start()
        self.stopButton.setVisible(True)
        self.playButton.setDisabled(True)

    def state_update(self, value):
        self.playButton.setDisabled(value)
        self.playButton.setEnabled(not value)
        self.stopButton.setVisible(value)
        self.progressBar.setVisible(value)
        if not value and self.progressBar.value() == 100:
            self.progressBar.setVisible(False)

    def update_progress(self, progress, max_progress, label):
        if max_progress > 0:
            percentage = int(progress / max_progress * 100)
        else:
            percentage = 0
        self.progressBar.setValue(progress)
        self.progressBar.setMaximum(max_progress)
        text = f"{percentage}% - {label}"
        self.progressBar.setFormat(text)

    def open_directory(self):
        roaming_directory = os.path.join(os.getenv('APPDATA'), '.unixlauncher')
        if os.path.exists(roaming_directory):
            subprocess.Popen(['explorer', roaming_directory])
        else:
            QtWidgets.QMessageBox

    def create_unixlauncher_directory(self):
        roaming_directory = os.path.join(os.getenv('APPDATA'), '.unixlauncher')
        if not os.path.exists(roaming_directory):
            os.makedirs(roaming_directory)

    def update_version_info(self):
        selected_version = self.versionSelectBox.currentText()
        self.versionInfo.setText(selected_version)

    def select_forge(self):
        self.loaderInfo.setText('Loader: Forge')

    def select_quilt(self):
        self.loaderInfo.setText('Loader: Quilt')

    def select_fabric(self):
        self.loaderInfo.setText('Loader: Fabric')

    def select_Vanilla(self):
        self.loaderInfo.setText('Loader: Vanilla')

    def close_window(self):
        MainWindow.close()

    def minimize_window(self):
        MainWindow.showMinimized()
            
    def stop_game(self):
        self.progressBar.setVisible(False)
        self.stopButton.setVisible(False)
        self.playButton.setEnabled(True)
        self.launch_thread.stop_signal.emit()

    #Hover Events:
    def CloseButtonEnterEvent(self, event):
        self.closeButton.setIcon(QtGui.QIcon("assets/CloseButtonHover.png"))

    def CloseButtonLeaveEvent(self, event):
        self.closeButton.setIcon(QtGui.QIcon("assets/CloseButton.png"))

    def CollapseButtonEnterEvent(self, event):
        self.collapseButton.setIcon(QtGui.QIcon("assets/CollapseButtonHover.png"))

    def CollapseButtonLeaveEvent(self, event):
        self.collapseButton.setIcon(QtGui.QIcon("assets/CollapseButton.png"))

    def folderButtonEnterEvent(self, event):
        self.folderButton.setIcon(QtGui.QIcon("assets/FolderButtonHover.png"))

    def folderButtonLeaveEvent(self, event):
        self.folderButton.setIcon(QtGui.QIcon("assets/FolderButton.png"))

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
