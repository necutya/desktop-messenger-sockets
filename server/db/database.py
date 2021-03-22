import os
import pymongo

from dotenv import load_dotenv
from .exceptions import UserAlreadyExistsError, AuthenticatedError, RoomAlreadyExistsError, UserDoesNotExistsError, \
    RoomDoesNotExistsError
from .utils import generate_password_hash, check_password, generate_unique_auth_key

load_dotenv()

class SingletonMeta(type):
    """
    Singleton meta class
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class DataBase(metaclass=SingletonMeta):
    """
    Use singleton meta class in order to connect to db nly one time
    """

    def __init__(self):
        client = pymongo.MongoClient(os.getenv("MONGO_URI"))
        self._db = client.messenger

    def get_collection(self, collection_name):
        return self._db[collection_name]


class User:
    """
    Class for user model with fields:
    * _id - user id
    * nickname - user name
    * password - user password
    """
    __collection = DataBase().get_collection('users')

    @staticmethod
    def create(nickname: str, password: str) -> int:
        if User.__collection.find_one({"nickname": nickname}):
            raise UserAlreadyExistsError("User with this nickname already exists!")
        password_hash = generate_password_hash(password)
        created_user = User.__collection.insert_one({"nickname": nickname, "password": password_hash,
                                                     "auth_key": ""})
        return created_user.inserted_id

    @staticmethod
    def authenticate(nickname: str, password: str) -> str:
        user = User.__collection.find_one({"nickname": nickname})
        if not user or not check_password(password, user['password']):
            raise AuthenticatedError("Authenticated failed! Please check credentials!")
        if not user.get("auth_key", None):
            auth_key = generate_unique_auth_key()
            User.__collection.update_one({"_id": user["_id"]},
                                         {"$set": {"auth_key": auth_key}})
        else:
            auth_key = user["auth_key"]
        return auth_key

    @staticmethod
    def get_by_id(_id: str) -> dict:
        user = User.__collection.find_one({"_id": _id})
        if not user:
            raise UserDoesNotExistsError(f"User with {_id} does not exist!")
        return user

    @staticmethod
    def get_by_auth_key(auth_key: str) -> dict:
        user = User.__collection.find_one({"auth_key": auth_key})
        if not user:
            raise UserDoesNotExistsError("User does not exists")
        return user

    @staticmethod
    def logout(auth_key: str) -> None:
        User.__collection.update_one({"auth_key": auth_key}, {"$set": {"auth_key": ""}})


class Room:
    """
    Class for room model with fields:
    * room_name - rooms name
    * symmetric_key - hash key for room
    * users - list of users_id
    """
    __collection = DataBase().get_collection('rooms')

    @staticmethod
    def create(name: str, room_type: str, creator_id: int) -> int:
        if Room.__collection.find_one({"name": name}):
            raise RoomAlreadyExistsError("Room with such label already exists!")
        created_room = Room.__collection.insert_one(
            {
                "name": name,
                'type': room_type,
                'users': [creator_id, ],
                'messages': []
            }
        )
        return created_room.inserted_id

    @staticmethod
    def get_by_id(_id: int) -> dict:
        room = Room.__collection.find_one({"_id": _id})
        if not room:
            raise RoomDoesNotExistsError(f"Room with id {_id} does not exist!")
        return room

    @staticmethod
    def get_by_name(name: str) -> dict:
        room = Room.__collection.find_one({"name": name})
        if not room:
            raise RoomDoesNotExistsError(f"Room with name {name} does not exists!")
        return room

    @staticmethod
    def get_by_type(type: str) -> list:
        return Room.__collection.find({'type': type})

    @staticmethod
    def add_user_to_room(room_name, user_id) -> None:
        Room.__collection.update_one({"name": room_name}, {"$push": {"users": user_id}})

    @staticmethod
    def remove_user_from_room(room_name, user_id) -> None:
        Room.__collection.update_one({"name": room_name}, {"$pull": {"users": user_id}})

    @staticmethod
    def get_all_room_users(room_name) -> list:
        return Room.__collection.find({'name': room_name})['users']

    @staticmethod
    def get_user_rooms(user_id: int) -> list:
        user_rooms = Room.__collection.find(
            {'users': {'$elemMatch': {'$eq': user_id}}}
        )
        return user_rooms


    @staticmethod
    def remove_user_from_rooms(user_id: int) -> None:
        for room in Room.get_user_rooms(user_id):
            Room.remove_user_from_room(room['name'], user_id)