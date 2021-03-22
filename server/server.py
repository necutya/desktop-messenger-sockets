import time
import pickle
import socket
import threading

from db.database import Room, User
from db.exceptions import UserAlreadyExistsError, AuthenticatedError, RoomAlreadyExistsError, RoomDoesNotExistsError, UserDoesNotExistsError


class Server:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port

        self.connected_clients = {}

        # Запускаем прослушивание соединений
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.ip, self.port))
        self.server.listen(0)

        threading.Thread(target=self.connect_handler).start()
        print('Server was run!')

    # Обрабатываем входящие соединения
    def connect_handler(self):
        while True:
            client, address = self.server.accept()
            print(client)
            payload = {
                'action': 'SERVER_OK',
                'data': "Successfully connected to server",
            }

            client.send(pickle.dumps(payload))
            print(f'{address} - Successfully connected to server')
            threading.Thread(target=self.message_handler, args=(client,)).start()

            time.sleep(2)

    # Обрабатываем отправленный текст
    def message_handler(self, client_socket: socket.socket):
        while True:
            try:
                message = client_socket.recv(1024)
                pickle_data = pickle.loads(message)
                print(pickle_data)
            except:
                client_socket.close()
                break

            # Exit from application and close connection
            if pickle_data['action'] == "EXIT":
                if pickle_data.get("auth_key"):
                    auth_key = pickle_data['auth_key']
                    Room.remove_user_from_rooms(User.get_by_auth_key(auth_key)['_id'])
                    User.logout(auth_key)
                    del self.connected_clients[auth_key]
                client_socket.close()
                break

            # Broadcast message to all chat users
            # Continue because user, who send a message, does not receive anything
            elif pickle_data['action'] == "SEND_MESSAGE" and pickle_data.get('auth_key', None):
                self.send_text_message_to_chat(pickle_data)
                continue

            # Login user
            elif pickle_data['action'] == "LOGIN":
                payload = self.login_user(pickle_data)
                # add to dict pair: user_auth_key -> socket object
                self.connected_clients[payload['data']] = client_socket

            # Register
            elif pickle_data['action'] == "REGISTER":
                payload = self.register_user(pickle_data)

            # Create new room
            elif pickle_data['action'] == "CREATE_ROOM" and pickle_data.get('auth_key', None):
                payload = self.create_room(pickle_data)

            # Get all available rooms
            elif pickle_data['action'] == "GET_ROOMS" and pickle_data.get('auth_key', None):
                payload = self.gel_all_available_rooms(pickle_data)

            elif pickle_data['action'] == "EXIT_ROOM" and pickle_data.get('auth_key', None):
                payload = self.exit_rooms(pickle_data)

            elif pickle_data['action'] == "TRY_TO_CONNECT_TO_ROOM" and pickle_data.get('auth_key', None):
                payload = self.try_to_connect_to_room(pickle_data)

            else:
                payload = {
                    'action': 'ERROR',
                    'data': 'Oopps, something went wrong and we lost yout auth key:( '
                            'Please, reconnect to fix this problem.'
                }

            print(f"Send:{payload}")
            client_socket.send(pickle.dumps(payload))

            time.sleep(1)

    def login_user(self, pickle_data: dict) -> dict:
        try:
            auth_key = User.authenticate(pickle_data['data'][0], pickle_data['data'][1])
            return {'action': 'AUTH_SUCCESS', 'data': auth_key}
        except AuthenticatedError as error:
            return {'action': 'ERROR', 'data': str(error)}

    def register_user(self, pickle_data: dict) -> dict:
        try:
            User.create(pickle_data['data'][0], pickle_data['data'][1])
            return {'action': 'REGISTER_SUCCESS', 'data': 'User has been created successfully', }

        except UserAlreadyExistsError as error:
            return {'action': 'ERROR', 'data': str(error)}

    def create_room(self, pickle_data: dict) -> dict:
        try:
            user = User.get_by_auth_key(pickle_data['auth_key'])
            room_id = Room.create(pickle_data['data'][0], pickle_data['data'][1], user['_id'])
            return {'action': 'CREATED_SUCCESS', 'data': Room.get_by_id(room_id).get('name', None)}

        except RoomAlreadyExistsError as error:
            return {'action': 'ERROR', 'data': str(error)}
        except UserDoesNotExistsError as error:
            return {'action': 'ERROR', 'data': str(error)}
        except RoomDoesNotExistsError as error:
            return {'action': 'ERROR', 'data': str(error)}

    def gel_all_available_rooms(self, pickle_data: dict) -> dict:
        text_rooms = self.get_all_text_rooms()
        voice_rooms = self.get_all_voice_rooms()
        return {'action': 'ALL_ROOMS', 'data': {'text_rooms': text_rooms, 'voice_rooms': voice_rooms}}

    def get_all_text_rooms(self) -> list:
        return [room['name'] for room in Room.get_by_type('text')]

    def get_all_voice_rooms(self) -> list:
        return [room['name'] for room in Room.get_by_type('voice')]

    def exit_rooms(self, pickle_data: dict) -> dict:
        user_id = User.get_by_auth_key(pickle_data['auth_key'])
        Room.remove_user_from_room(pickle_data['data'], user_id)

        text_rooms = self.get_all_text_rooms()
        voice_rooms = self.get_all_voice_rooms()
        return {'action': 'ALL_ROOMS', 'data': {'text_rooms': text_rooms, 'voice_rooms': voice_rooms}}

    def try_to_connect_to_room(self, pickle_data: dict) -> dict:
        try:
            user = User.get_by_auth_key(auth_key=pickle_data['auth_key'])
        except UserDoesNotExistsError as error:
            return {'action': 'ERROR', 'data': str(error)}

        try:
            room = Room.get_by_name(pickle_data['data'])
        except RoomDoesNotExistsError as error:
            return {'action': 'ERROR', 'data': str(error)}
        else:
            users_id = room['users']
            for u_id in users_id:
                room_user = User.get_by_id(u_id)
                payload = {
                    'action': 'RECEIVE_MESSAGE',
                    'data': ('ChatInfo', f"User {user['nickname']} has been connected to a room")
                }
                self.connected_clients[room_user['auth_key']].send(pickle.dumps(payload))

            Room.add_user_to_room(room_name=room['name'], user_id=user['id'])
            return {'action': 'CONNECTED_TO_ROOM_SUCCESSFULLY', 'data': (room['name'], room['messages'])}

    def send_text_message_to_chat(self, pickle_data: dict) -> dict:
        users_id = Room.get_by_name(pickle_data['data'][0])['users']
        for user_id in users_id:
            user = User.get_by_id(user_id)
            if user['auth_key'] != pickle_data['auth_key']:
                payload = {
                    'action': 'RECEIVE_MESSAGE',
                    'data': (
                        User.get_by_auth_key(pickle_data['auth_key'])['nickname'],
                        pickle_data['data'][1]
                    )
                }
                self.connected_clients[user['auth_key']].send(pickle.dumps(payload))




if __name__ == "__main__":
    myserver = Server('127.0.0.1', 5555)
