class AppError(Exception):
    """Uygulama seviyesi hataların ortak tabanı."""


class NotFoundError(AppError):
    """İstenen kayıt bulunamadı (-> HTTP 404)."""


class ConflictError(AppError):
    """İşlem bir kısıt nedeniyle yapılamadı, ör. FK ihlali (-> HTTP 409)."""
