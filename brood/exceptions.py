class RestrictedTokenUnauthorized(Exception):
    pass


class AccessTokenUnauthorized(Exception):
    pass


class UserGroupLimitExceeded(Exception):
    pass


class UnhandledException(Exception):
    """
    Raised when unexpected behavior occurs.
    """


class ApplicationsNotFound(Exception):
    """
    Raised when application with the given parameters is not found in the database.
    """
