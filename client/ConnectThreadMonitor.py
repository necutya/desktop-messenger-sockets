import time
import pickle
from PyQt5 import QtCore


# Мониторинг входящих сообщений
class message_monitor(QtCore.QThread):
    mysignal = QtCore.pyqtSignal(dict)
    server_socket = None

    def __init__(self, parent=None):
        QtCore.QThread.__init__(self, parent)

    def run(self):
        print(f'server_socket: {self.server_socket}')

        while True:
            if self.server_socket != None:
                message = self.server_socket.recv(1024)
                pickle_dec = pickle.loads(message)
                print(pickle_dec)
                self.mysignal.emit(pickle_dec)

            time.sleep(2)

    # Отправить зашифрованное сообщение на сервер
    def send_encrypt(self, payload: dict):
        # if payload.get('action', None) in ['REGISTER', 'LOGIN']:
        #     payload['data'] = [credential for credential in payload['data']]

        self.server_socket.send(pickle.dumps(payload))

        # Если клиент разорвал соединение
        # ['EXIT', f'{self.nick}', 'вышел из чата!']
        # elif data_list[0] == "EXIT":
        #     encrypted_message = self.cipher.encrypt(data_list[-1])
        #     pickle_payload = ['EXIT', data_list[1], encrypted_message]
        #     self.server_socket.send(pickle.dumps(pickle_payload))
