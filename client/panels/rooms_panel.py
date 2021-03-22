import sys

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QAction, QMessageBox
from windows.rooms import Ui_Selection


# Окно с настройками клиента
class RoomsPanel(QtWidgets.QMainWindow):
    def __init__(self, parent=None, signal=None):
        super().__init__(parent)
        self.rooms_ui = Ui_Selection()
        self.rooms_ui.setupUi(self)
        self.setWindowTitle("Select a room")

        # Сигнал для возврата в интерфейс
        self.signal = signal

        self.rooms_ui.create_chat_btn.clicked.connect(self.go_to_create_chat)

        finish = QAction("Quit", self)
        finish.triggered.connect(self.closeEvent)


    def go_to_create_chat(self):
        self.signal.emit({'action': 'CREATE_ROOM_WIN', 'data': ""})


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
    login_panel = RoomsPanel()
    login_panel.show()
    sys.exit(app.exec_())
