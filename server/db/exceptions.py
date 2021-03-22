class UserAlreadyExistsError(Exception):
    pass


class AuthenticatedError(Exception):
    pass


class UserDoesNotExistsError(Exception):
    pass


class RoomAlreadyExistsError(Exception):
    pass


class RoomDoesNotExistsError(Exception):
    pass
