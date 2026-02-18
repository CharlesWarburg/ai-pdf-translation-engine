from fastapi.responses import JSONResponse


def error_response(status_code: int, code: str, message: str) -> JSONResponse:
    """Return a client-facing JSON error response with flat { code, message } shape."""

    return JSONResponse(
        status_code=status_code,
        content={"code": code, "message": message},
    )


class UserInputError(RuntimeError):
    """
    Errors caused by invalid user input.

    These should surface as 4xx responses rather than 5xx.
    """


class TransientUpstreamError(RuntimeError):
    """Errors that might succeed on retry (e.g. network flakiness)."""


class PermanentUpstreamError(RuntimeError):
    """Errors that are unlikely to succeed on retry."""

