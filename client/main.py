import os
import sys
import time
import json
import socket
from typing import Union

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QColor, QFont

from ConnectThreadMonitor import message_monitor
from panels.login_panel import LoginPanel
from panels.register_panel import RegisterPanel
from panels.rooms_panel import RoomsPanel
from panels.create_room_panel import CreateRoomPanel
from panels.text_chat_panel import TextRoomPanel


# Интерфейс программы и обработчик событий внутри него
class Client(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)

        # Данные из конфига (симметричный ключ получаем в ответе от сервера)
        self.ip = '127.0.0.1'
        self.port = 5555
        self.connect_status = False
        self.auth_key = None
        self.room = None

        # окно без рамок и заголовка, не отображается на панели задач
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        # прозрачный фон окна
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        desktop = QtWidgets.QApplication.desktop()
        screen01 = desktop.primaryScreen()  # у меня 2 монитора, определяем главный
        # получаем разрешение нужного монитора
        res = desktop.screenGeometry(screen01)
        # устанавливаем размер откна по размеру монитора
        self.setFixedSize(res.width(), res.height())
        # перемещаем окно чтобы оно заняло весь монитор
        self.move(0, 0)
        self.show()

        # Экземпляр класса для обработки соединений и сигналов
        self.connect_monitor = message_monitor()
        self.connect_monitor.mysignal.connect(self.signal_handler)

        self.active_page = None
        self.login_win = LoginPanel(self, signal=self.connect_monitor.mysignal)
        self.register_win = RegisterPanel(self, signal=self.connect_monitor.mysignal)
        self.rooms_win = RoomsPanel(self, signal=self.connect_monitor.mysignal)
        self.create_room_win = CreateRoomPanel(self, signal=self.connect_monitor.mysignal)
        self.text_room_win = TextRoomPanel(self, signal=self.connect_monitor.mysignal)
        for win in (self.login_win, self.register_win, self.rooms_win,
                    self.create_room_win, self.text_room_win):
            win.setFixedSize(450, 600)

        self.connect_to_server()

    def signal_handler(self, value: dict):
        """
        Handle signal and process it
        :param value:
        :return:
        """
        action: str = value.get('action', None)
        if action == "SERVER_OK":
            self.connect_status = True
            self.active_page = self.login_win
            self.login_win.show()

        elif 'WIN' in action:
            window = eval('self.' + action.lower())
            self.change_active_window_to(window)

        elif action == "SEND_LOGIN_CREDENTIALS":
            self.send_message(action='LOGIN', data=value['data'])

        elif action == "SEND_REGISTER_CREDENTIALS":
            self.send_message(action='REGISTER', data=value['data'])

        elif action == "CREATE_ROOM":
            self.send_message(action=action, data=value['data'])

        elif action == "CREATED_SUCCESS":
            self.generate_error_window("Message", "Room was created successfully!")
            self.change_active_window_to(self.text_room_win)
            self.room = value['data']

        elif action == "ERROR":
            self.generate_error_window(title="ERROR", message=value['data'])

        elif action == "AUTH_SUCCESS":
            self.auth_key = value['data']
            self.change_active_window_to(self.rooms_win)
            self.send_message(action="GET_ROOMS", data="")

        elif action == "REGISTER_SUCCESS":
            self.change_active_window_to(self.login_win)

        elif action == "EXIT_ROOM":
            self.send_message(action=action, data=self.room)
            self.room = None

        elif action == "ALL_ROOMS":
            font = QFont()
            font.setPixelSize(20)

            if self.active_page != self.rooms_win:
                self.change_active_window_to(self.rooms_win)

            self.active_page.rooms_ui.text_chats.clear()
            self.active_page.rooms_ui.voice_chats.clear()

            for index, text_room in enumerate(value['data']['text_rooms']):
                room = QtWidgets.QListWidgetItem()
                room.setForeground(QColor.fromRgb(85, 0, 127))
                room.setFont(font)
                room.setText(f"{index + 1}.{text_room}")
                self.active_page.rooms_ui.text_chats.addItem(room)

            for index, voice_room in enumerate(value['data']['voice_rooms']):
                room = QtWidgets.QListWidgetItem()
                room.setForeground(QColor.fromRgb(85, 0, 127))
                room.setFont(font)
                room.setText(f"{index + 1}.{voice_room}")
                self.active_page.rooms_ui.voice_chats.addItem(room)

            self.active_page.rooms_ui.text_chats.itemDoubleClicked.connect(
                lambda item: self.signal_handler(
                    {
                        'action': 'TRY_TO_CONNECT_TO_ROOM',
                        'data': item.text().split('.')[-1]
                    }
                )
            )

        elif action == "TRY_TO_CONNECT_TO_ROOM":
            self.send_message(action=action, data=value['data'])

        elif action == "CONNECTED_TO_ROOM_SUCCESSFULLY":
            self.change_active_window_to(self.text_room_win)
            self.room = value['data'][0]

        elif action == "SEND_MESSAGE":
            item = QtWidgets.QListWidgetItem()
            item.setTextAlignment(QtCore.Qt.AlignRight)
            self.send_message(action=action, data=(self.room, value['data']))
            item.setText(f"You:\n{value['data']}")
            self.active_page.text_chat_ui.message_list.addItem(item)

        elif action == "RECEIVE_MESSAGE":
            item = QtWidgets.QListWidgetItem()
            if value['data'][0] == 'ChatInfo':
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                item.setForeground(QColor().fromRgb(255, 0, 0))
                item.setText(value['data'][1])
            else:
                item.setTextAlignment(QtCore.Qt.AlignLeft)
                item.setText(f"{value['data'][0]}:\n{value['data'][1]}")
            self.active_page.text_chat_ui.message_list.addItem(item)

        elif action == "EXIT":
            self.closeEvent()

    def send_message(self, action: str, data: Union[list, str]):
        """
        Send a message to server
        """
        if self.connect_status:
            payload = {'action': action, 'data': data, 'auth_key': self.auth_key}

            self.connect_monitor.send_encrypt(payload)
        else:
            message = "Check connection to a server!"
            QtWidgets.QMessageBox.about(self, "Error", message)

    def connect_to_server(self):
        """
        Connect user to a server
        """
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((self.ip, self.port))

            self.connect_status = True

            # Start message monitoring
            self.connect_monitor.server_socket = self.client
            self.connect_monitor.start()

        except Exception as err:
            message = f"Server connection error!\n{err}"
            title = f"Connection error"
            self.generate_error_window(title, message)
            exit(1)

    def generate_error_window(self, title, message):
        """
        Display error message
        """
        QtWidgets.QMessageBox.about(self, title, message)

    def change_active_window_to(self, window: QtWidgets.QMainWindow):
        """
        Change main window to
        """
        self.active_page.hide()
        self.active_page = window
        self.active_page.show()

    def closeEvent(self, *args, **kwargs) -> None:
        """
        Close enebt handlet
        """
        try:
            self.send_message(action='EXIT', data='')
            self.hide()
            self.client.close()
            self.active_page.hide()
            self.close()
            exit(0)
        except Exception as err:
            print(err)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    c = Client()
    sys.exit(app.exec_())
