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
