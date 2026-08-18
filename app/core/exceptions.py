class AppException(Exception):
    """Base application exception."""


class UserAlreadyExistsException(AppException):
    """Raised when a user already exists."""


class InvalidCredentialsException(AppException):
    """Raised when login credentials are invalid."""


class UserNotFoundException(AppException):
    """Raised when a user cannot be found."""


class InactiveUserException(AppException):
    """Raised when an inactive user attempts to authenticate."""


class RoleNotFoundException(AppException):
    """Raised when a required role does not exist."""
