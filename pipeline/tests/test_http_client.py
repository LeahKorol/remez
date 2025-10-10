import pytest
import httpx
from core.http_client import HTTPClient


@pytest.fixture
def mock_httpx_client(mocker):
    """Fixture to create a mock AsyncClient."""
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.aclose = mocker.AsyncMock()
    return mock_client


@pytest.fixture
def http_client_instance():
    """Fixture to create a fresh HTTPClient instance."""
    return HTTPClient()


@pytest.fixture
def mock_response(mocker):
    """Fixture to create a mock HTTP response."""
    response = mocker.MagicMock(spec=httpx.Response)
    response.status_code = 200
    return response


@pytest.fixture
def setup_mock_client(mocker, mock_response):
    """Fixture to setup a mock client with HTTP methods."""
    def _setup(http_client_instance):
        mock_client = mocker.AsyncMock()
        for method in ["get", "post", "put", "delete", "patch"]:
            setattr(mock_client, method, mocker.AsyncMock(return_value=mock_response))
        
        mock_get_or_create = mocker.patch.object(
            http_client_instance, "get_or_create", return_value=mock_client
        )
        return mock_client, mock_get_or_create
    return _setup


class TestHTTPClientInitialization:
    """Test HTTPClient initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        client = HTTPClient()
        assert client.timeout == 10.0
        assert client.max_connections == 100
        assert client.max_keepalive_connections == 20
        assert client.keepalive_expiry == 5.0
        assert client._client is None

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        client = HTTPClient(
            timeout=30.0,
            max_connections=200,
            max_keepalive_connections=50,
            keepalive_expiry=10.0,
        )
        assert client.timeout == 30.0
        assert client.max_connections == 200
        assert client.max_keepalive_connections == 50
        assert client.keepalive_expiry == 10.0

    def test_init_with_injected_client(self, mock_httpx_client):
        """Test initialization with an injected client."""
        client = HTTPClient(client=mock_httpx_client)
        assert client._client is mock_httpx_client

    @pytest.mark.parametrize("timeout,max_conn", [
        (0.0, 0),
        (-1.0, -10),
        (100.0, 1000),
    ])
    def test_init_with_edge_case_values(self, timeout, max_conn):
        """Test initialization with edge case values."""
        client = HTTPClient(timeout=timeout, max_connections=max_conn)
        assert client.timeout == timeout
        assert client.max_connections == max_conn


class TestGetOrCreate:
    """Test the get_or_create method."""

    @pytest.mark.asyncio
    async def test_get_or_create_lazy_initialization(self, http_client_instance, mocker):
        """Test that get_or_create lazily initializes the client."""
        assert http_client_instance._client is None
        
        mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
        mock_async_client_class = mocker.patch("httpx.AsyncClient", return_value=mock_client)
        
        result = await http_client_instance.get_or_create()
        
        assert result is mock_client
        assert http_client_instance._client is mock_client
        mock_async_client_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_or_create_returns_same_client(self, http_client_instance, mocker):
        """Test that calling get_or_create multiple times returns the same client."""
        mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
        mock_async_client_class = mocker.patch("httpx.AsyncClient", return_value=mock_client)
        
        client1 = await http_client_instance.get_or_create()
        client2 = await http_client_instance.get_or_create()
        client3 = await http_client_instance.get_or_create()
        
        assert client1 is client2 is client3
        assert mock_async_client_class.call_count == 1

    @pytest.mark.asyncio
    async def test_get_or_create_with_injected_client(self, mock_httpx_client):
        """Test that get_or_create returns injected client without creating new one."""
        client = HTTPClient(client=mock_httpx_client)
        result = await client.get_or_create()
        assert result is mock_httpx_client


class TestStop:
    """Test the stop method."""

    @pytest.mark.asyncio
    async def test_stop_closes_client(self, mock_httpx_client):
        """Test that stop closes the client."""
        client = HTTPClient(client=mock_httpx_client)
        await client.stop()
        
        mock_httpx_client.aclose.assert_called_once()
        assert client._client is None

    @pytest.mark.asyncio
    async def test_stop_with_no_client(self, http_client_instance):
        """Test that stop does nothing if client was never initialized."""
        await http_client_instance.stop()
        assert http_client_instance._client is None


class TestHTTPMethods:
    """Test HTTP request methods."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("method,url,kwargs", [
        ("get", "https://example.com", {}),
        ("post", "https://example.com", {"json": {"key": "value"}}),
        ("put", "https://example.com/resource", {}),
        ("delete", "https://example.com/resource", {}),
        ("patch", "https://example.com/resource", {"data": "test"}),
    ])
    async def test_http_methods(self, http_client_instance, setup_mock_client, method, url, kwargs):
        """Test all HTTP methods with various parameters."""
        mock_client, _ = setup_mock_client(http_client_instance)
        
        result = await getattr(http_client_instance, method)(url, **kwargs)
        
        assert result.status_code == 200
        getattr(mock_client, method).assert_called_once_with(url, **kwargs)

    @pytest.mark.asyncio
    async def test_request_with_headers(self, http_client_instance, setup_mock_client):
        """Test request with custom headers."""
        mock_client, _ = setup_mock_client(http_client_instance)
        headers = {"Authorization": "Bearer token123"}
        
        result = await http_client_instance.get("https://example.com", headers=headers)
        
        assert result.status_code == 200
        mock_client.get.assert_called_once_with("https://example.com", headers=headers)

    @pytest.mark.asyncio
    async def test_request_with_params(self, http_client_instance, setup_mock_client):
        """Test request with query parameters."""
        mock_client, _ = setup_mock_client(http_client_instance)
        params = {"key": "value", "page": 1}
        
        result = await http_client_instance.get("https://example.com", params=params)
        
        assert result.status_code == 200
        mock_client.get.assert_called_once_with("https://example.com", params=params)


class TestErrorHandling:
    """Test error handling in HTTP requests."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("method,exception_class,error_msg", [
        ("get", httpx.RequestError, "Connection failed"),
        ("post", httpx.TimeoutException, "Request timeout"),
        ("put", httpx.ConnectError, "Cannot connect"),
    ])
    async def test_request_raises_errors(
        self, http_client_instance, mocker, method, exception_class, error_msg
    ):
        """Test that various HTTP errors are properly raised."""
        mock_client = mocker.AsyncMock()
        setattr(mock_client, method, mocker.AsyncMock(side_effect=exception_class(error_msg)))
        mocker.patch.object(http_client_instance, "get_or_create", return_value=mock_client)
        
        with pytest.raises(exception_class):
            await getattr(http_client_instance, method)("https://example.com")


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_multiple_requests_use_same_client(self, http_client_instance, setup_mock_client):
        """Test that multiple requests use the same underlying client."""
        _, mock_get_or_create = setup_mock_client(http_client_instance)
        
        await http_client_instance.get("https://example.com")
        await http_client_instance.post("https://example.com")
        await http_client_instance.get("https://example.com/other")
        
        assert mock_get_or_create.call_count == 3

    @pytest.mark.asyncio
    async def test_stop_and_restart(self, http_client_instance, mocker):
        """Test that client can be stopped and restarted."""
        mock_client1 = mocker.AsyncMock(spec=httpx.AsyncClient)
        mock_client1.aclose = mocker.AsyncMock()
        mock_client2 = mocker.AsyncMock(spec=httpx.AsyncClient)
        mocker.patch("httpx.AsyncClient", side_effect=[mock_client1, mock_client2])
        
        client1 = await http_client_instance.get_or_create()
        assert client1 is mock_client1
        
        await http_client_instance.stop()
        assert http_client_instance._client is None
        
        client2 = await http_client_instance.get_or_create()
        assert client2 is mock_client2
        assert client1 is not client2