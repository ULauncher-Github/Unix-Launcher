import os
import subprocess
from PyQt5 import QtCore, QtGui, QtWidgets
import minecraft_launcher_lib
from uuid import uuid1
from random_username.generate import generate_username
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QIcon

class CenteredComboBox(QtWidgets.QProxyStyle):
    def drawItemText(self, painter, rect, flags, pal, enabled, text, textRole):
        flags |= QtCore.Qt.AlignCenter
        super(CenteredComboBox, self).drawItemText(painter, rect, flags, pal, enabled, text, textRole)

class LaunchThread(QtCore.QThread):
    launch_setup_signal = QtCore.pyqtSignal(str, str)
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

        self.launch_setup_signal.connect(self.launch_setup)
        self.stop_signal.connect(self.stop_launch)

    def launch_setup(self, version_id, username):
        self.version_id = version_id
        self.username = username
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

    def run(self):
        minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory().replace('minecraft', 'unixlauncher')
        self.state_update_signal.emit(True)

        try:
            minecraft_launcher_lib.install.install_minecraft_version(
                versionid=self.version_id,
                minecraft_directory=minecraft_directory,
                callback={
                    'setStatus': self.update_progress_label,
                    'setProgress': self.update_progress,
                    'setMax': self.update_progress_max
                }
            )

            if self.username == '':
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
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(740, 217)
        MainWindow.setFixedSize(740, 217)
        MainWindow.setStyleSheet("background-color: rgb(38, 38, 38);")
        MainWindow.setWindowTitle('Unix Launcher')
        icon_path = "assets/ico.png"
        icon = QtGui.QIcon(icon_path)
        MainWindow.setWindowIcon(icon)

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        self.start_button = QtWidgets.QPushButton(self.centralwidget)
        self.start_button.setGeometry(QtCore.QRect(80, 170, 276, 40))
        self.start_button.setStyleSheet("QPushButton {\n"
                                        "background: transparent;\n"
                                        "border: none;\n"
                                        "}")
        icon_start = QtGui.QIcon()
        icon_start.addPixmap(QtGui.QPixmap("assets/start_button.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.start_button.setIcon(icon_start)
        self.start_button.setIconSize(QtCore.QSize(276, 40))
        self.start_button.setObjectName("start_button")
        self.start_button.clicked.connect(self.launch_game)
        self.start_button.enterEvent = self.start_button_enter_event
        self.start_button.leaveEvent = self.start_button_leave_event

        self.stop_button = QtWidgets.QPushButton(self.centralwidget)
        self.stop_button.setGeometry(QtCore.QRect(80, 170, 276, 40))
        self.stop_button.setStyleSheet("QPushButton {\n"
                                       "background: transparent;\n"
                                       "border: none;\n"
                                       "}")
        icon_stop = QtGui.QIcon()
        icon_stop.addPixmap(QtGui.QPixmap("assets/stop_button.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.stop_button.setIcon(icon_stop)
        self.stop_button.setIconSize(QtCore.QSize(276, 40))
        self.stop_button.setObjectName("stop_button")
        self.stop_button.clicked.connect(self.stop_game)
        self.stop_button.setVisible(False)
        self.stop_button.enterEvent = self.stop_button_enter_event
        self.stop_button.leaveEvent = self.stop_button_leave_event

        self.mc_folder = QtWidgets.QPushButton(self.centralwidget)
        self.mc_folder.setGeometry(QtCore.QRect(30, 170, 40, 40))
        self.mc_folder.setStyleSheet("QPushButton {\n"
                                     "background: transparent;\n"
                                     "border: none;\n"
                                     "}")
        icon_mc_folder = QtGui.QIcon()
        icon_mc_folder.addPixmap(QtGui.QPixmap("assets/mc_folder.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.mc_folder.setIcon(icon_mc_folder)
        self.mc_folder.setIconSize(QtCore.QSize(40, 40))
        self.mc_folder.setObjectName("mc_folder")
        self.mc_folder.clicked.connect(self.open_directory)
        self.mc_folder.enterEvent = self.mc_folder_enter_event
        self.mc_folder.leaveEvent = self.mc_folder_leave_event

        self.username = QtWidgets.QLineEdit(self.centralwidget)
        self.username.setGeometry(QtCore.QRect(35, 120, 321, 40))
        self.username.setStyleSheet("QLineEdit {\n"
                                    "background: transparent;\n"
                                    "border: none;\n"
                                    "color: white;\n"
                                    "font-size: 18px;\n"
                                    "}\n"
                                    "")
        self.username.setObjectName("username")
        self.usernameBack = QtWidgets.QLabel(self.centralwidget)
        self.usernameBack.setGeometry(QtCore.QRect(30, 120, 325, 40))
        self.usernameBack.setText("")
        self.usernameBack.setPixmap(QtGui.QPixmap("assets/what_name_is_it.png"))
        self.usernameBack.setObjectName("usernameBack")
        self.username.setPlaceholderText('Username')

        self.logo = QtWidgets.QLabel(self.centralwidget)
        self.logo.setGeometry(QtCore.QRect(50, 10, 681, 94))
        self.logo.setText("")
        self.logo.setPixmap(QtGui.QPixmap("assets/logo.png"))
        self.logo.setObjectName("logo")

        self.version_select = QtWidgets.QComboBox(self.centralwidget)
        self.version_select.setGeometry(QtCore.QRect(390, 120, 325, 40))
        self.version_select.setStyleSheet("QComboBox {\n"
                                          "background: transparent;\n"
                                          "border: none;\n"
                                          "color: white;\n"
                                          "font-size: 18px;\n"
                                          "qproperty-alignment: \'AlignCenter\';\n"
                                          "}\n"
                                          "QComboBox::drop-down {\n"
                                          "background: transparent;\n"
                                          "border: none;\n"
                                          "}\n"
                                          "QComboBox QAbstractItemView {\n"
                                          "background: #403f3f; \n"
                                          "border: none;\n"
                                          "color: white;"
                                          "}")
        self.version_select.setObjectName("version_select")
        centered_style = CenteredComboBox()
        self.version_select.setStyle(centered_style)
        for version in minecraft_launcher_lib.utils.get_version_list():
            self.version_select.addItem(version['id'])

        self.version_selectBack = QtWidgets.QLabel(self.centralwidget)
        self.version_selectBack.setGeometry(QtCore.QRect(390, 120, 325, 40))
        self.version_selectBack.setText("")
        self.version_selectBack.setPixmap(QtGui.QPixmap("assets/version_selectBack.png"))
        self.version_selectBack.setObjectName("version_selectBack")

        self.progressBar = QtWidgets.QProgressBar(self.centralwidget)
        self.progressBar.setGeometry(QtCore.QRect(390, 170, 325, 40))
        self.progressBar.setStyleSheet("QProgressBar {\n"
                                       "border: 4px solid #1B1B1B;\n"
                                       "border-radius: 10px;\n"
                                       "text-align: center;\n"
                                       "background-color: #333333;\n"
                                       "color: white;\n"
                                       "}\n"
                                       "QProgressBar::chunk {\n"
                                       "background-color: #2196F3;\n"
                                       "border-radius: 10px;\n"
                                       "}")
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName("progressBar")
        self.progressBar.setVisible(False)

        self.usernameBack.raise_()
        self.version_selectBack.raise_()
        self.start_button.raise_()
        self.stop_button.raise_()
        self.mc_folder.raise_()
        self.username.raise_()
        self.logo.raise_()
        self.version_select.raise_()

        self.launch_thread = LaunchThread()
        self.launch_thread.progress_update_signal.connect(self.update_progress)
        self.launch_thread.state_update_signal.connect(self.state_update)

        self.timer = QTimer()
        self.timer.timeout.connect(self.hide_progress_bar)

        MainWindow.setCentralWidget(self.centralwidget)

        self.create_unixlauncher_directory()

        saved_username = self.load_username()
        if saved_username:
            self.username.setText(saved_username)

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
        self.stop_button.setVisible(True)
        self.start_button.setDisabled(True)

        username = self.username.text()
        if username:
            self.save_username(username)

        self.launch_thread.launch_setup_signal.emit(self.version_select.currentText(), username)
        self.launch_thread.start()

    def stop_game(self):
        self.progressBar.setVisible(False)
        self.stop_button.setVisible(False)
        self.start_button.setEnabled(True)
        self.launch_thread.stop_signal.emit()

    def state_update(self, value):
        self.start_button.setEnabled(not value)
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
        self.adjust_progress_bar_font(text)
        self.progressBar.setFormat(text)

    def adjust_progress_bar_font(self, text):
        """Adjust font size of the QProgressBar based on the length of the text."""
        font = self.progressBar.font()
        if len(text) > 20:
            font.setPointSize(8)
        elif len(text) > 15:
            font.setPointSize(10)
        elif len(text) > 10:
            font.setPointSize(12)
        else:
            font.setPointSize(14)
        self.progressBar.setFont(font)

    def start_button_leave_event(self, event):
        if not self.start_button.isEnabled():
            return
        self.start_button.setIcon(QtGui.QIcon("assets/start_button.png"))

    def start_button_enter_event(self, event):
        if not self.start_button.isEnabled():
            return
        self.start_button.setIcon(QtGui.QIcon("assets/start_buttonhover.png"))
    

    def mc_folder_leave_event(self, event):
        if not self.mc_folder.isEnabled():
            return
        self.mc_folder.setIcon(QtGui.QIcon("assets/mc_folder.png"))

    def mc_folder_enter_event(self, event):
        if not self.mc_folder.isEnabled():
            return
        self.mc_folder.setIcon(QtGui.QIcon("assets/mc_folderhover.png"))

    def stop_button_leave_event(self, event):
        if not self.stop_button.isEnabled():
            return
        self.stop_button.setIcon(QtGui.QIcon("assets/stop_button.png"))

    def stop_button_enter_event(self, event):
        if not self.stop_button.isEnabled():
            return
        self.stop_button.setIcon(QtGui.QIcon("assets/stop_buttonhover.png"))

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

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

