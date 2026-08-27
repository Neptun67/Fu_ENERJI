class AppError(Exception):
    """Base class for application-level errors."""


class NotFoundError(AppError):
    """The requested record does not exist (-> HTTP 404)."""


class ConflictError(AppError):
    """The operation violates a constraint, e.g. a foreign key (-> HTTP 409)."""
