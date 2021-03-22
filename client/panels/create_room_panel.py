import sys

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QAction, QMessageBox
from windows.create_room import Ui_CreateRoom


# Окно с настройками клиента
class CreateRoomPanel(QtWidgets.QMainWindow):
    def __init__(self, parent=None, signal=None):
        super().__init__(parent)
        self.create_room_ui = Ui_CreateRoom()
        self.create_room_ui.setupUi(self)
        self.setWindowTitle("Create room")

        # Сигнал для возврата в интерфейс
        self.signal = signal

        # Обработчики кнопок
        self.create_room_ui.create_chat_btn.clicked.connect(self.create_chat)

        finish = QAction("Quit", self)
        finish.triggered.connect(self.closeEvent)

    def create_chat(self):
        room_name_data = self.create_room_ui.name.text()
        is_text_room = self.create_room_ui.text_chat_type.isChecked()
        is_voice_room = self.create_room_ui.voice_chat_type.isChecked()
        if room_name_data and (is_voice_room or is_text_room):
            data = (room_name_data, 'text' if is_text_room else 'voice')
            self.signal.emit({'action': 'CREATE_ROOM', 'data': data})
        else:
            message = "Enter all fields!"
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
    login_panel = CreateRoomPanel()
    login_panel.show()
    sys.exit(app.exec_())
