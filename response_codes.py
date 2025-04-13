# response_codes.py
from enum import IntEnum

class UserResponseCode(IntEnum):
    REGISTER_TAKEN = 10128
    LOGIN_FAILED = 10020
    USER_NOT_FOUND = 10404
    GENERIC_ERROR = 50000
