import sys

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QAction, QMessageBox
from windows.login import Ui_Login


# Окно с настройками клиента
class LoginPanel(QtWidgets.QMainWindow):
    def __init__(self, parent=None, signal=None):
        super().__init__(parent)
        self.login_ui = Ui_Login()
        self.login_ui.setupUi(self)
        self.setWindowTitle("Login")

        # Сигнал для возврата в интерфейс
        self.signal = signal

        # Обработчики кнопок
        self.login_ui.login_btn.clicked.connect(self.login)
        self.login_ui.register_btn.clicked.connect(self.register)

        finish = QAction("Quit", self)
        finish.triggered.connect(self.closeEvent)

    def login(self):
        login_data = self.login_ui.login.text()
        password_data = self.login_ui.password.text()
        if login_data and password_data:
            self.signal.emit({'action': 'SEND_LOGIN_CREDENTIALS', 'data': [login_data, password_data]})
        else:
            message = "Enter both login and password!"
            QtWidgets.QMessageBox.about(self, "Error", message)

    def register(self):
        self.signal.emit({'action': 'REGISTER_WIN', 'data': ""})

    def closeEvent(self, event):
        close = QMessageBox.question(self,
                                     "QUIT",
                                     "Are u sure? All your data will be lost!",
                                     QMessageBox.Yes | QMessageBox.No)
        if close == QMessageBox.Yes:
            event.accept()
            self.signal.emit({'action': 'EXIT', 'data': ""})
        else:
            event.ignore()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    login_panel = LoginPanel()
    login_panel.show()
    sys.exit(app.exec_())
