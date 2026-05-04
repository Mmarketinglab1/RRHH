from uuid import UUID

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.security import decode_access_token


class TenantContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.company_id = None
        authorization = request.headers.get("authorization", "")
        if authorization.lower().startswith("bearer "):
            token = authorization.split(" ", 1)[1]
            try:
                payload = decode_access_token(token)
                request.state.company_id = UUID(payload["company_id"])
            except (KeyError, ValueError):
                request.state.company_id = None
        return await call_next(request)
