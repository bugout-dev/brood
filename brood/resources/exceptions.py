class ResourceNotFound(Exception):
    """
    Raised when resource with the given parameters is not found in the database.
    """


class PermissionsNotFound(Exception):
    """
    Raised when permission with the given parameters is not found in the database.
    """


class HolderNotFound(Exception):
    """
    Raised when holder with the given parameters is not found in the database.
    """


class HolderPermissionsNotFound(Exception):
    """
    Raised when holder permission with the given parameters is not found in the database.
    """


class ResourceInvalidParameters(ValueError):
    """
    Raised when operations are applied to a resource but invalid parameters are provided.
    """
