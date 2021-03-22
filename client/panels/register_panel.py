import os
import re
import json
import sys

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QAction, QMessageBox
from windows.register import Ui_Register


# Окно с настройками клиента
class RegisterPanel(QtWidgets.QMainWindow):
    def __init__(self, parent=None, signal=None):
        super().__init__(parent)
        self.register_ui = Ui_Register()
        self.register_ui.setupUi(self)
        self.setWindowTitle("Register")
        # self.setWindowModality(2)

        # Сигнал для возврата в интерфейс
        self.signal = signal

        # Обработчики кнопок
        self.register_ui.login_btn.clicked.connect(self.login)
        self.register_ui.register_btn.clicked.connect(self.register)

        finish = QAction("Quit", self)
        finish.triggered.connect(self.closeEvent)

    def login(self):
        self.signal.emit({'action': 'LOGIN_WIN', 'data': ""})

    def register(self):
        login_data = self.register_ui.login.text()
        password_data = self.register_ui.password.text()
        password_conformation = self.register_ui.password_2.text()
        if not all((login_data, password_data, password_conformation)):
            message = "Enter all fields!"
            QtWidgets.QMessageBox.about(self, "Error", message)
        elif not password_data == password_conformation:
            message = "Passwords do not not match!"
            QtWidgets.QMessageBox.about(self, "Error", message)
        else:
            self.signal.emit({'action': 'SEND_REGISTER_CREDENTIALS', 'data': [login_data, password_data]})


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
