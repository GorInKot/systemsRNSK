class AppError(Exception):
    """Ошибка предметной области с сообщением, которое можно показать пользователю."""

    def __init__(self, status_code: int, message: str, errors: list[dict] | None = None, code: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.errors = errors or []
        self.code = code


def not_found(what: str = "Запись не найдена") -> AppError:
    return AppError(404, what, code="not_found")


def forbidden(message: str = "Недостаточно прав для этого действия") -> AppError:
    return AppError(403, message, code="forbidden")


def field_error(path: str, message: str, status_code: int = 422) -> AppError:
    return AppError(status_code, "Проверьте заполнение анкеты", errors=[{"path": path, "message": message}], code="validation")
