import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class HTTPClient:
    """
    HTTP client wrapper for making async requests.
    Supports optional client injection for testing.
    """

    def __init__(
        self,
        timeout: float = 10.0,
        max_connections: int = 100,
        max_keepalive_connections: int = 20,
        keepalive_expiry: float = 5.0,
        client: Optional[httpx.AsyncClient] = None,
    ):
        self.timeout = timeout
        self.max_connections = max_connections
        self.max_keepalive_connections = max_keepalive_connections
        self.keepalive_expiry = keepalive_expiry
        self._client: Optional[httpx.AsyncClient] = client

        if client:
            logger.info("HTTPClient initialized with injected client")
        else:
            logger.info(
                f"HTTPClient initialized "
                f"timeout={timeout}s, max_connections={max_connections}"
            )

    async def get_or_create(self) -> httpx.AsyncClient:
        """
        Lazily initialize the HTTP client if not already started,
        or return the existing client.
        """
        if self._client is None:
            logger.info("Initializing HTTP client lazily...")
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                limits=httpx.Limits(
                    max_connections=self.max_connections,
                    max_keepalive_connections=self.max_keepalive_connections,
                    keepalive_expiry=self.keepalive_expiry,
                ),
            )
            logger.info("HTTP client started successfully")
        return self._client

    async def stop(self) -> None:
        """
        Stop the HTTP client and close connections.
        """
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            logger.info("HTTP client stopped and all connections closed")

    async def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """
        Internal helper to handle requests and exceptions.
        """
        client = await self.get_or_create()
        try:
            resp = await getattr(client, method)(url, **kwargs)
            logger.debug(f"{method.upper()} {url} - status {resp.status_code}")
            return resp
        except httpx.HTTPError as e:
            logger.error(f"{method.upper()} {url} failed: {e}")
            raise

    async def get(self, url: str, **kwargs) -> httpx.Response:
        return await self._request("get", url, **kwargs)

    async def post(self, url: str, **kwargs) -> httpx.Response:
        return await self._request("post", url, **kwargs)

    async def put(self, url: str, **kwargs) -> httpx.Response:
        return await self._request("put", url, **kwargs)

    async def delete(self, url: str, **kwargs) -> httpx.Response:
        return await self._request("delete", url, **kwargs)

    async def patch(self, url: str, **kwargs) -> httpx.Response:
        return await self._request("patch", url, **kwargs)


# Global client instance
http_client = HTTPClient()
