from __future__ import annotations

import ipaddress
from collections.abc import Iterable

from starlette.datastructures import Headers
from starlette.responses import PlainTextResponse
from starlette.types import ASGIApp, Receive, Scope, Send


class HealthcheckAwareTrustedHostMiddleware:
    """Trusted host validation that permits private-IP load balancer health checks."""

    def __init__(
        self,
        app: ASGIApp,
        allowed_hosts: Iterable[str],
        healthcheck_paths: Iterable[str] = ("/health",),
    ) -> None:
        self.app = app
        self.allowed_hosts = [host.strip() for host in allowed_hosts if host.strip()]
        self.healthcheck_paths = set(healthcheck_paths)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in {"http", "websocket"}:
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        host = headers.get("host", "")
        hostname = self._hostname(host)

        if self._is_allowed_hostname(hostname) or self._is_allowed_healthcheck(scope, hostname):
            await self.app(scope, receive, send)
            return

        response = PlainTextResponse("Invalid host header", status_code=400)
        await response(scope, receive, send)

    def _is_allowed_healthcheck(self, scope: Scope, hostname: str) -> bool:
        return scope.get("path") in self.healthcheck_paths and self._is_private_ip(hostname)

    def _is_allowed_hostname(self, hostname: str) -> bool:
        if "*" in self.allowed_hosts:
            return True

        for allowed_host in self.allowed_hosts:
            if hostname == allowed_host:
                return True
            if allowed_host.startswith("*.") and hostname.endswith(allowed_host[1:]):
                return True
        return False

    @staticmethod
    def _hostname(host: str) -> str:
        if host.startswith("["):
            return host[1:].split("]", 1)[0].lower()
        return host.rsplit(":", 1)[0].lower()

    @staticmethod
    def _is_private_ip(hostname: str) -> bool:
        try:
            address = ipaddress.ip_address(hostname)
        except ValueError:
            return False
        return address.is_private or address.is_loopback or address.is_link_local
