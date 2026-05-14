from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse

from .exceptions import AppException


async def app_exception_manager(request: Request, exc: AppException) -> JSONResponse:
    """
    Handles application-specific exceptions and returns a JSON response.

    Args:
        request: The incoming Starlette/FastAPI request object.
        exc: The raised AppException instance containing message and status code.

    Returns:
        A JSONResponse containing the error message and the appropriate status code.
    """
    return JSONResponse(content={"error": exc.message}, status_code=exc.status_code)


async def default_exception_manager(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all handler for unexpected internal server errors.

    Args:
        request: The incoming Starlette/FastAPI request object.
        exc: The unhandled Exception instance.

    Returns:
        A generic 500 Internal Server Error JSON response.
    """
    return JSONResponse(
        content={"error": "Something went wrong."},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


async def sqlalchemy_exception_manager(
    request: Request,
    exc: SQLAlchemyError,
) -> JSONResponse:
    """
    Handles generic SQLAlchemy errors.
    """

    return JSONResponse(
        content={"error": "Database error occurred."},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


async def sqlalchemy_integrity_exception_manager(
    request: Request,
    exc: IntegrityError,
) -> JSONResponse:
    """
    Handles integrity constraint violations.
    """

    return JSONResponse(
        content={"error": "Resource already exists or constraint violated."},
        status_code=status.HTTP_400_BAD_REQUEST,
    )
