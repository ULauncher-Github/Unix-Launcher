from PyQt5 import QtCore, QtGui, QtWidgets
import os
import subprocess
from uuid import uuid1
from random_username.generate import generate_username
import minecraft_launcher_lib
from PyQt5.QtCore import QTimer, Qt

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
                return False

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

    def install_fabric(self, minecraft_directory):
        try:
            self.update_progress_label("Installing Fabric")
            minecraft_launcher_lib.fabric.install_fabric(
                self.version_id,
                minecraft_directory,
                callback={
                    'setStatus': self.update_progress_label,
                    'setProgress': self.update_progress,
                    'setMax': self.update_progress_max
                }
            )
        except Exception as e:
            print(f"Error during Fabric installation: {str(e)}")
            return False
        return True

    def install_quilt(self, minecraft_directory):
        try:
            self.update_progress_label("Installing Quilt")
            minecraft_launcher_lib.quilt.install_quilt(
                self.version_id,
                minecraft_directory,
                callback={
                    'setStatus': self.update_progress_label,
                    'setProgress': self.update_progress,
                    'setMax': self.update_progress_max
                }
            )
        except Exception as e:
            print(f"Error during Quilt installation: {str(e)}")
            return False
        return True

    def run(self):
        minecraft_version = self.version_id.split('-')[0]
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

            elif self.loader_type == 'Fabric':
                fabric_installed = self.install_fabric(minecraft_directory)
                if not fabric_installed:
                    return

            elif self.loader_type == 'Quilt':
                quilt_installed = self.install_quilt(minecraft_directory)
                if not quilt_installed:
                    return

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
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(980, 538)
        MainWindow.setMinimumSize(QtCore.QSize(980, 538))
        MainWindow.setMaximumSize(QtCore.QSize(980, 538))
        MainWindow.setWindowFlags(Qt.FramelessWindowHint)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("assets/icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MainWindow.setWindowIcon(icon)
        MainWindow.setUnifiedTitleAndToolBarOnMac(False)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.main = QtWidgets.QLabel(self.centralwidget)
        self.main.setGeometry(QtCore.QRect(0, 0, 980, 538))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.main.sizePolicy().hasHeightForWidth())
        self.main.setSizePolicy(sizePolicy)
        self.main.setText("")
        self.main.setPixmap(QtGui.QPixmap("assets/mainFrame.png"))
        self.main.setObjectName("main")

        self.stop_button = QtWidgets.QPushButton(self.centralwidget)
        self.stop_button.setGeometry(QtCore.QRect(707, 463, 246, 38))
        self.stop_button.setIcon(QtGui.QIcon("assets/StopButton.png"))
        self.stop_button.setIconSize(QtCore.QSize(246, 38))
        self.stop_button.setObjectName("stop_button")
        self.stop_button.clicked.connect(self.stop_game)
        self.stop_button.setVisible(False)
        self.stop_button.enterEvent = self.stop_button_enter_event
        self.stop_button.leaveEvent = self.stop_button_leave_event

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

        self.progressBar = QtWidgets.QProgressBar(self.centralwidget)
        self.progressBar.setGeometry(QtCore.QRect(706, 301, 246, 38))
        self.progressBar.setStyleSheet("QProgressBar {\n"
                                        "    border: 2px solid #fff;\n"
                                        "    border-radius: 9px;\n"
                                        "    text-align: center;\n"
                                        "    font-size: 12px;\n"
                                        "    font-weight: bold;\n"
                                        "    color: white;\n"
                                        "    background-color: transparent;\n"
                                        "    padding: 4px;\n"
                                        "    font-family: \"Play\";\n"
                                        "}\n"
                                        "\n"
                                        "QProgressBar::chunk {\n"
                                        "    background-color: #00B051;\n"
                                        "    border-radius: 7px;\n"
                                        "}")
        self.progressBar.setProperty("value", 0)
        self.progressBar.setTextVisible(True)
        self.progressBar.setObjectName("progressBar")
        self.progressBar.setVisible(False)
        
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(928, 365, 16, 21))
        self.label.setStyleSheet("QLabel {\n"
                                "    color: white;\n"
                                "    font: 18pt \"Arial\";\n"
                                "}")
        self.label.setText("")
        self.label.setPixmap(QtGui.QPixmap("assets/Down.png"))
        self.label.setObjectName("label")

        self.preview = QtWidgets.QLabel(self.centralwidget)
        self.preview.setGeometry(QtCore.QRect(701, 70, 256, 144))
        self.preview.setText("")
        self.preview.setPixmap(QtGui.QPixmap("assets/prev1.png"))
        self.preview.setObjectName("preview")
        self.versionSelect = QtWidgets.QComboBox(self.centralwidget)
        self.versionSelect.setGeometry(QtCore.QRect(707, 355, 246, 38))
        self.versionSelect.setStyleSheet("QComboBox {\n"
                                        "    background-color: rgba(0,0,0,0);\n"
                                        "    color: white;\n"
                                        "    border: 2px solid #cccccc;\n"
                                        "    border-radius: 9px;\n"
                                        "    padding: 5px;\n"
                                        "    font-size: 18px;\n"
                                        "    text-align: center;\n"
                                        "}\n"
                                        "QComboBox::drop-down {\n"
                                        "                background: transparent;\n"
                                        "                border: none;\n"
                                        "}\n"
                                        "QAbstractItemView {\n"
                                        "                background: #403f3f; \n"
                                        "                border: none;\n"
                                        "                color: white;"
                                        "            }")
        self.versionSelect.setObjectName("versionSelect")
        for version in minecraft_launcher_lib.utils.get_version_list():
            self.versionSelect.addItem(version['id'])
        self.versionSelect.setCurrentText(latest_version["release"])

        self.nameEdit = QtWidgets.QLineEdit(self.centralwidget)
        self.nameEdit.setGeometry(QtCore.QRect(707, 409, 246, 38))
        self.nameEdit.setStyleSheet("QLineEdit {\n"
                                        "    background-color: rgba(0,0,0,0);\n"
                                        "    color: white;\n"
                                        "    font: \"Play\";\n"
                                        "    border: 2px solid #cccccc;\n"
                                        "    border-radius: 9px;\n"
                                        "    padding: 4px;\n"
                                        "    font-size:  18px;\n"
                                        "}")
        self.nameEdit.setMaxLength(19)
        self.nameEdit.setObjectName("nameEdit")
        self.playButton = QtWidgets.QPushButton(self.centralwidget)
        self.playButton.setGeometry(QtCore.QRect(707, 463, 246, 38))
        self.playButton.setStyleSheet("QPushButton {\n"
                                        "    background-color: rgba(0,0,0,0);\n"
                                        "}\n"
                                        "")
        self.playButton.setText("")
        self.playButton.setObjectName("playButton")
        self.playButton.clicked.connect(self.launch_game)
        self.playButton.setIcon(QtGui.QIcon("assets/PlayButton.png"))
        self.playButton.setIconSize(QtCore.QSize(246, 38))
        self.playButton.enterEvent = self.playButton_enter_event
        self.playButton.leaveEvent = self.playButton_leave_event

        self.folderButton = QtWidgets.QPushButton(self.centralwidget)
        self.folderButton.setGeometry(QtCore.QRect(948, 506, 22, 22))
        self.folderButton.setStyleSheet("QPushButton {\n"
                                        "    background-color: rgba(0,0,0,0);\n"
                                        "}\n"
                                        "")
        self.folderButton.setText("")
        self.folderButton.setObjectName("folderButton")
        self.folderButton.clicked.connect(self.open_directory)
        self.folderButton.setIcon(QtGui.QIcon("assets/FolderButton.png"))
        self.folderButton.setIconSize(QtCore.QSize(22, 22))
        self.folderButton.enterEvent = self.folderButton_enter_event
        self.folderButton.leaveEvent = self.folderButton_leave_event

        self.svernutButton = QtWidgets.QPushButton(self.centralwidget)
        self.svernutButton.setGeometry(QtCore.QRect(888, 20, 31, 16))
        self.svernutButton.setStyleSheet("QPushButton {\n"
                                        "    background-color: rgba(0,0,0,0);\n"
                                        "}\n"
                                        "")
        self.svernutButton.setText("")
        self.svernutButton.setObjectName("svernutButton")
        self.svernutButton.clicked.connect(self.minimize_window) 
        self.svernutButton.setIcon(QtGui.QIcon("assets/Svernut.png"))
        self.svernutButton.setIconSize(QtCore.QSize(31, 16))
        self.svernutButton.enterEvent = self.svernutButton_enter_event
        self.svernutButton.leaveEvent = self.svernutButton_leave_event

        self.versionInfo = QtWidgets.QLabel(self.centralwidget)
        self.versionInfo.setGeometry(QtCore.QRect(732, 214, 196, 37))
        self.versionInfo.setStyleSheet("        QLabel {\n"
                                        "            color: white;\n"
                                        "            text-align: center;\n"
                                        "            font-size: 32px;\n"
                                        "}")
        self.versionInfo.setAlignment(QtCore.Qt.AlignCenter)
        self.versionInfo.setObjectName("versionInfo")

        self.closeButton = QtWidgets.QPushButton(self.centralwidget)
        self.closeButton.setGeometry(QtCore.QRect(931, 9, 40, 40))
        self.closeButton.setStyleSheet("QPushButton {\n"
                                        "    background-color: rgba(0,0,0,0);\n"
                                        "}\n"
                                        "")
        self.closeButton.setText("")
        self.closeButton.setObjectName("closeButton")
        self.closeButton.clicked.connect(self.close_window)
        self.closeButton.setIcon(QtGui.QIcon("assets/Close.png"))
        self.closeButton.setIconSize(QtCore.QSize(40, 40))
        self.closeButton.enterEvent = self.closeButton_enter_event
        self.closeButton.leaveEvent = self.closeButton_leave_event

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        # Инициализация потока запуска игры
        self.launch_thread = LaunchThread()
        self.launch_thread.progress_update_signal.connect(self.update_progress)
        self.launch_thread.state_update_signal.connect(self.set_launch_controls_state)

        # Установка начального состояния
        self.selected_loader = 'Vanilla'
        self.update_loader_info()

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "UnixLauncher"))
        self.nameEdit.setPlaceholderText(_translate("MainWindow", "Имя игрока"))
        self.versionInfo.setText(_translate("MainWindow", self.versionSelect.currentText()))

    def update_loader_info(self):
        self.loaderInfo.setText(f"Loader: {self.selected_loader}")

    def select_forge(self):
        self.selected_loader = 'Forge'
        self.update_loader_info()

    def select_fabric(self):
        self.selected_loader = 'Fabric'
        self.update_loader_info()

    def select_quilt(self):
        self.selected_loader = 'Quilt'
        self.update_loader_info()

    def select_Vanilla(self):
        self.selected_loader = 'Vanilla'
        self.update_loader_info()

    def update_progress(self, progress, progress_max, label):
        self.progressBar.setVisible(True)
        self.progressBar.setMaximum(progress_max)
        self.progressBar.setValue(progress)
        self.progressBar.setFormat(label)

    def set_launch_controls_state(self, state):
        self.playButton.setEnabled(not state)
        self.stop_button.setVisible(state)
        self.progressBar.setVisible(state)

    def playButton_enter_event(self, event):
        self.playButton.setIcon(QtGui.QIcon("assets/PlayButtonHover.png"))

    def playButton_leave_event(self, event):
        self.playButton.setIcon(QtGui.QIcon("assets/PlayButton.png"))

    def stop_button_enter_event(self, event):
        self.stop_button.setIcon(QtGui.QIcon("assets/StopButtonHover.png"))

    def stop_button_leave_event(self, event):
        self.stop_button.setIcon(QtGui.QIcon("assets/StopButton.png"))

    def folderButton_enter_event(self, event):
        self.folderButton.setIcon(QtGui.QIcon("assets/FolderButtonHover.png"))

    def folderButton_leave_event(self, event):
        self.folderButton.setIcon(QtGui.QIcon("assets/FolderButton.png"))

    def svernutButton_enter_event(self, event):
        self.svernutButton.setIcon(QtGui.QIcon("assets/SvernutHover.png"))

    def svernutButton_leave_event(self, event):
        self.svernutButton.setIcon(QtGui.QIcon("assets/Svernut.png"))

    def closeButton_enter_event(self, event):
        self.closeButton.setIcon(QtGui.QIcon("assets/CloseHover.png"))

    def closeButton_leave_event(self, event):
        self.closeButton.setIcon(QtGui.QIcon("assets/Close.png"))

    def open_directory(self):
        minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory().replace('minecraft', 'unixlauncher')
        os.startfile(minecraft_directory)

    def minimize_window(self):
        MainWindow.showMinimized()

    def close_window(self):
        MainWindow.close()

    def launch_game(self):
        version_id = self.versionSelect.currentText()
        username = self.nameEdit.text()
        self.launch_thread.launch_setup_signal.emit(version_id, username, self.selected_loader)
        self.launch_thread.start()

    def stop_game(self):
        self.launch_thread.stop_signal.emit()

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())