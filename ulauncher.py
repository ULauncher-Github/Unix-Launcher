from PyQt5 import QtCore, QtGui, QtWidgets
import os
import subprocess
from uuid import uuid1
from random_username.generate import generate_username
import minecraft_launcher_lib
from PyQt5.QtCore import QTimer, Qt
#LOADER SELECT DOESN'T WORKING
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
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(980, 538)
        MainWindow.setMinimumSize(QtCore.QSize(980, 538))
        MainWindow.setMaximumSize(QtCore.QSize(980, 538))
        MainWindow.setWindowTitle("Unix Launcher")
        self.setWindowFlags(Qt.FramelessWindowHint)
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
                                        "    border: 2px solid #fff; /* Белая граница шириной 2px */\n"
                                        "    border-radius: 9px;    /* Закругленные углы радиусом 7px */\n"
                                        "    text-align: center;     /* Выравнивание текста по центру */\n"
                                        "    font-size: 12px;        /* Размер шрифта */\n"
                                        "    font-weight: bold;      /* Жирный шрифт */\n"
                                        "    color: white;           /* Цвет текста */\n"
                                        "    background-color: transparent; /* Прозрачный фон */\n"
                                        "    padding: 4px;           /* Отступы внутри прогресс-бара */\n"
                                        "    font-family: \"Play\";    /* Шрифт Play */\n"
                                        "}\n"
                                        "\n"
                                        "QProgressBar::chunk {\n"
                                        "    background-color: #00B051; /* Цвет заливки прогресса */\n"
                                        "    border-radius: 7px;        /* Закругленные углы для заливки радиусом 7px */\n"
                                        "}\n"
                                        "")
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
                                        "            }"
                                        "")
        self.versionSelect.setObjectName("versionSelect")
        for version in minecraft_launcher_lib.utils.get_version_list():
            self.versionSelect.addItem(version['id'])
        self.versionSelect.setCurrentText(latest_version["release"])

        self.nameEdit = QtWidgets.QLineEdit(self.centralwidget)
        self.nameEdit.setGeometry(QtCore.QRect(707, 409, 246, 38))
        self.nameEdit.setStyleSheet("QLineEdit {\n"
                                        "    background-color: rgba(0,0,0,0);\n"
                                        "    color: white;\n"
                                        "    font: \"Play\"; \n"
                                        "    border: 2px solid #cccccc;\n"
                                        "    border-radius: 9px;\n"
                                        "    padding: 4px;\n"
                                        "    font-size:  18px;\n"
                                        "}\n"
                                        "")
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
                                        "\n"
                                        "            text-align: center;  \n"
                                        "            font-size: 32px;\n"
                                        "\n"
                                        "        }")
        self.versionInfo.setAlignment(QtCore.Qt.AlignCenter)
        self.versionInfo.setObjectName("versionInfo")

        self.loaderInfo = QtWidgets.QLabel(self.centralwidget)
        self.loaderInfo.setGeometry(QtCore.QRect(700, 250, 261, 20))
        self.loaderInfo.setStyleSheet("QLabel {\n"
                                        "    color: white;\n"
                                        "    font-size: 16px;\n"
                                        "                  display: flex;\n"
                                        "                justify-content: center;\n"
                                        "                align-items: center;\n"
                                        "                text-align: center;\n"
                                        "                height: 100%;\n"
                                        "}")
        self.loaderInfo.setAlignment(QtCore.Qt.AlignCenter)
        self.loaderInfo.setObjectName("loaderInfo")
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

        self.nameEdit.setPlaceholderText("Введите никнейм")
        self.versionInfo.setText(self.versionSelect.currentText())
        self.loaderInfo.setText("Загрузчик: Vanilla")
        
        self.launch_thread = LaunchThread()
        self.launch_thread.progress_update_signal.connect(self.update_progress)
        self.launch_thread.state_update_signal.connect(self.state_update)
        self.timer = QTimer()
        self.timer.timeout.connect(self.hide_progress_bar)

        self.create_unixlauncher_directory()

        saved_username = self.load_username()
        if saved_username:
            self.nameEdit.setText(saved_username)
        self.stop_button.raise_()
        self.versionSelect.currentIndexChanged.connect(self.update_version_info)

        self.is_dragging = False
        self.drag_start_pos = None

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
        username = self.nameEdit.text()
        if username:
            self.save_username(username)
        loader_type = self.loaderInfo.text().split(": ")[-1]  # Получение типа загрузчика из loaderInfo
        self.launch_thread.launch_setup_signal.emit(self.versionSelect.currentText(), username, loader_type)
        self.launch_thread.start()
        self.stop_button.setVisible(True)
        self.playButton.setDisabled(True)

    def state_update(self, value):
        self.playButton.setDisabled(value)
        self.playButton.setEnabled(not value)
        self.stop_button.setVisible(value)
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
        selected_version = self.versionSelect.currentText()
        self.versionInfo.setText(selected_version)

    def select_forge(self):
        self.loaderInfo.setText('Загрузчик: Forge')

    def select_quilt(self):
        self.loaderInfo.setText('Загрузчик: Quilt')

    def select_fabric(self):
        self.loaderInfo.setText('Загрузчик: Fabric')

    def select_Vanilla(self):
        self.loaderInfo.setText('Загрузчик: Vanilla')

    def close_window(self):
        self.close()

    def minimize_window(self):
        self.showMinimized()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.is_dragging = True
            self.drag_start_pos = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            self.move(event.globalPos() - self.drag_start_pos)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.is_dragging = False
            
    def stop_game(self):
        self.progressBar.setVisible(False)
        self.stop_button.setVisible(False)
        self.playButton.setEnabled(True)
        self.launch_thread.stop_signal.emit()

    def playButton_leave_event(self, event):
        if not self.playButton.isEnabled():
            return
        self.playButton.setIcon(QtGui.QIcon("assets/PlayButton.png"))

    def playButton_enter_event(self, event):
        if not self.playButton.isEnabled():
            return
        self.playButton.setIcon(QtGui.QIcon("assets/PlayButtonHover.png"))
        
    def stop_button_leave_event(self, event):
        if not self.stop_button.isEnabled():
            return
        self.stop_button.setIcon(QtGui.QIcon("assets/StopButton.png"))

    def stop_button_enter_event(self, event):
        if not self.stop_button.isEnabled():
            return
        self.stop_button.setIcon(QtGui.QIcon("assets/StopButtonHover.png"))
    def folderButton_leave_event(self, event):
        if not self.folderButton.isEnabled():
            return
        self.folderButton.setIcon(QtGui.QIcon("assets/FolderButton.png.png"))

    def folderButton_enter_event(self, event):
        if not self.folderButton.isEnabled():
            return
        self.folderButton.setIcon(QtGui.QIcon("assets/FolderButtonHover.png"))

    def closeButton_leave_event(self, event):
        if not self.stop_button.isEnabled():
            return
        self.closeButton.setIcon(QtGui.QIcon("assets/Close.png"))

    def closeButton_enter_event(self, event):
        if not self.closeButton.isEnabled():
            return
        self.closeButton.setIcon(QtGui.QIcon("assets/CloseHover.png"))

    def svernutButton_leave_event(self, event):
        if not self.svernutButton.isEnabled():
            return
        self.svernutButton.setIcon(QtGui.QIcon("assets/Svernut.png"))

    def svernutButton_enter_event(self, event):
        if not self.svernutButton.isEnabled():
            return
        self.svernutButton.setIcon(QtGui.QIcon("assets/SvernutHover.png"))

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
#LOADER SELECT DOESN'T WORKING
