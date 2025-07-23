"""Integration tests for /api/tags endpoint."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from ollama_openai_proxy.main import app
from ollama_openai_proxy.config import Settings
from ollama_openai_proxy.services.openai_service import OpenAIService


@pytest.fixture
def client(monkeypatch):
    """Create test client with mocked dependencies."""
    # Mock environment
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    
    # Create mock settings and service
    mock_settings = MagicMock(spec=Settings)
    mock_settings.openai_api_key = "test-key"
    mock_settings.openai_api_base_url = "https://api.openai.com/v1"
    mock_settings.proxy_port = 11434
    mock_settings.log_level = "INFO"
    mock_settings.request_timeout = 30
    
    mock_openai_service = MagicMock(spec=OpenAIService)
    
    # Set up app state
    with TestClient(app) as client:
        client.app.state.settings = mock_settings
        client.app.state.openai_service = mock_openai_service
        yield client


@pytest.fixture
def mock_openai_models():
    """Mock OpenAI models response."""
    from openai.types import Model
    
    return [
        Model(id="gpt-3.5-turbo", created=1234567890, object="model", owned_by="openai"),
        Model(id="gpt-4", created=1234567891, object="model", owned_by="openai"),
    ]


class TestTagsEndpoint:
    """Test /api/tags endpoint."""
    
    def test_list_models_success(self, client, mock_openai_models):
        """Test successful model listing."""
        # Mock the list_models method
        client.app.state.openai_service.list_models = AsyncMock(return_value=mock_openai_models)
        
        response = client.get("/api/tags")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "models" in data
        assert len(data["models"]) == 2
        assert data["models"][0]["name"] == "gpt-3.5-turbo"
        assert data["models"][1]["name"] == "gpt-4"
        
        # Check cache headers
        assert "Cache-Control" in response.headers
        assert response.headers["X-Model-Count"] == "2"
    
    def test_list_models_empty(self, client):
        """Test empty model list."""
        client.app.state.openai_service.list_models = AsyncMock(return_value=[])
        
        response = client.get("/api/tags")
        
        assert response.status_code == 200
        data = response.json()
        assert data["models"] == []
    
    def test_list_models_error(self, client):
        """Test error handling."""
        client.app.state.openai_service.list_models = AsyncMock(side_effect=Exception("API Error"))
        
        response = client.get("/api/tags")
        
        assert response.status_code == 500
        data = response.json()
        assert "error" in data["detail"]
        assert "Failed to fetch models" in data["detail"]["error"]
    
    def test_response_format(self, client, mock_openai_models):
        """Test response matches Ollama format exactly."""
        client.app.state.openai_service.list_models = AsyncMock(return_value=mock_openai_models)
        
        response = client.get("/api/tags")
        data = response.json()
        
        # Verify structure matches Ollama
        assert isinstance(data, dict)
        assert "models" in data
        assert isinstance(data["models"], list)
        
        # Verify model structure
        for model in data["models"]:
            assert "name" in model
            assert "modified_at" in model
            assert "size" in model
            assert isinstance(model["size"], int)
            assert model["modified_at"].endswith("Z")  # ISO format with Z