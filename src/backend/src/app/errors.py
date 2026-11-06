"""Define domain exceptions translated into HTTP JSON responses by `main.handle_app_error`."""
class AppError(Exception):
  """Represent a domain validation or business-rule error mapped to an HTTP status code."""

  status = 400

  def __init__(self, message : str) -> None:
    super().__init__(message)
    self.message = message

class NotFound(AppError) :
  status = 404

class Conflict(AppError):
  status = 409
