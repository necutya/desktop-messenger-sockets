import sys

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QAction, QMessageBox
from windows.text_chat import Ui_TextChat


# Окно с настройками клиента
class TextRoomPanel(QtWidgets.QMainWindow):
    def __init__(self, parent=None, signal=None):
        super().__init__(parent)
        self.text_chat_ui = Ui_TextChat()
        self.text_chat_ui.setupUi(self)
        self.setWindowTitle("Text chat")

        # Сигнал для возврата в интерфейс
        self.signal = signal

        self.text_chat_ui.exit_btn.clicked.connect(self.exit_room)
        self.text_chat_ui.send_btn.clicked.connect(self.send_message_to_chat)

        finish = QAction("Quit", self)
        finish.triggered.connect(self.closeEvent)

    def exit_room(self):
        self.signal.emit({'action': 'EXIT_ROOM', 'data': ""})

    def send_message_to_chat(self):
        message_text = self.text_chat_ui.message.text()
        if message_text:
            self.signal.emit({'action': 'SEND_MESSAGE', 'data': message_text})
        else:
            message = "Enter smth to send!"
            QtWidgets.QMessageBox.about(self, "Error", message)

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
    login_panel = TextRoomPanel()
    login_panel.show()
    sys.exit(app.exec_())
