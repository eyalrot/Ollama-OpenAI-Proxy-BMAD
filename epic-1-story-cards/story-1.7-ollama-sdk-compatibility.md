# Story 1.7: Ollama SDK Compatibility Test Suite

**Story Points**: 3  
**Priority**: P0 (Proves core value)  
**Type**: Testing  
**Dependencies**: All previous stories complete

## Story Summary
**As an** Ollama SDK user,  
**I want to** verify that client.list() works exactly as expected,  
**So that** I know the proxy maintains full compatibility.

## Technical Implementation Guide

### Pre-Implementation Checklist
- [ ] Testing infrastructure (Story 1.6) in place
- [ ] /api/tags endpoint working (Story 1.4)
- [ ] Virtual environment activated
- [ ] Ollama Python SDK installed for testing

### Implementation Steps

#### Step 1: Install Ollama SDK for Testing
Update **requirements-dev.txt**:
```txt
# Existing dependencies...

# Ollama SDK for compatibility testing
ollama>=0.1.7
```

#### Step 2: Create SDK Compatibility Test Suite
**tests/integration/test_ollama_sdk_list.py**:
```python
"""Ollama SDK compatibility tests for list functionality."""
import os
import time
from typing import Dict, List
from unittest.mock import patch

import pytest

# Import ollama if available
ollama = pytest.importorskip("ollama", reason="ollama package required for SDK tests")

from ollama_openai_proxy.services.openai_service import OpenAIService


@pytest.mark.sdk
class TestOllamaSDKList:
    """Test Ollama SDK list() compatibility."""
    
    @pytest.fixture
    def ollama_client(self):
        """Create Ollama client pointing to test proxy."""
        # Use test server URL
        client = ollama.Client(host="http://localhost:11434")
        return client
    
    @pytest.fixture
    def mock_openai_models(self):
        """Mock OpenAI models for consistent testing."""
        from openai.types import Model
        
        return [
            Model(
                id="gpt-3.5-turbo",
                created=1680000000,
                object="model",
                owned_by="openai"
            ),
            Model(
                id="gpt-4",
                created=1680000001,
                object="model",
                owned_by="openai"
            ),
            Model(
                id="gpt-4-turbo",
                created=1680000002,
                object="model",
                owned_by="openai"
            ),
            Model(
                id="text-embedding-ada-002",
                created=1680000003,
                object="model",
                owned_by="openai"
            ),
            Model(
                id="text-embedding-3-small",
                created=1680000004,
                object="model",
                owned_by="openai"
            ),
        ]
    
    def test_list_models_basic(self, ollama_client, mock_openai_models, test_client):
        """Test basic model listing with Ollama SDK."""
        # Mock the OpenAI service
        with patch.object(OpenAIService, 'list_models', return_value=mock_openai_models):
            # Use Ollama SDK to list models
            response = ollama_client.list()
            
            # Verify response structure
            assert isinstance(response, dict)
            assert "models" in response
            assert isinstance(response["models"], list)
            assert len(response["models"]) > 0
    
    def test_list_models_format(self, ollama_client, mock_openai_models, test_client):
        """Test model format matches Ollama expectations."""
        with patch.object(OpenAIService, 'list_models', return_value=mock_openai_models):
            response = ollama_client.list()
            
            # Check each model
            for model in response["models"]:
                # Required fields
                assert "name" in model
                assert "modified_at" in model
                assert "size" in model
                
                # Type checks
                assert isinstance(model["name"], str)
                assert isinstance(model["modified_at"], str)
                assert isinstance(model["size"], int)
                
                # Format checks
                assert model["modified_at"].endswith("Z")  # ISO format
                assert model["size"] > 0
                
                # Optional fields
                if "digest" in model:
                    assert isinstance(model["digest"], str)
    
    def test_list_models_content(self, ollama_client, mock_openai_models, test_client):
        """Test model content is correctly translated."""
        with patch.object(OpenAIService, 'list_models', return_value=mock_openai_models):
            response = ollama_client.list()
            
            models = response["models"]
            model_names = [m["name"] for m in models]
            
            # Should include chat models
            assert "gpt-3.5-turbo" in model_names
            assert "gpt-4" in model_names
            assert "gpt-4-turbo" in model_names
            
            # Should include embedding models
            assert "text-embedding-ada-002" in model_names
            assert "text-embedding-3-small" in model_names
    
    def test_empty_model_list(self, ollama_client, test_client):
        """Test handling of empty model list."""
        with patch.object(OpenAIService, 'list_models', return_value=[]):
            response = ollama_client.list()
            
            assert response == {"models": []}
    
    def test_list_models_error_handling(self, ollama_client, test_client):
        """Test error handling with Ollama SDK."""
        with patch.object(OpenAIService, 'list_models', side_effect=Exception("API Error")):
            # Ollama SDK should raise an exception
            with pytest.raises(Exception) as exc_info:
                ollama_client.list()
            
            # Should contain error information
            assert "API Error" in str(exc_info.value) or "500" in str(exc_info.value)
    
    @pytest.mark.slow
    def test_list_models_performance(self, ollama_client, mock_openai_models, test_client):
        """Test response time is within acceptable limits."""
        with patch.object(OpenAIService, 'list_models', return_value=mock_openai_models):
            start_time = time.time()
            response = ollama_client.list()
            duration = time.time() - start_time
            
            # Should complete within 100ms (excluding network latency)
            assert duration < 0.1
            assert len(response["models"]) > 0


@pytest.mark.sdk
class TestOllamaSDKCompatibilityAdvanced:
    """Advanced SDK compatibility tests."""
    
    def test_sdk_version_compatibility(self):
        """Test SDK version is compatible."""
        import ollama
        
        # Check SDK version
        assert hasattr(ollama, "__version__") or hasattr(ollama, "Client")
        
        # Verify expected methods exist
        client = ollama.Client()
        assert hasattr(client, "list")
        assert callable(client.list)
    
    def test_model_filtering_logic(self, test_client):
        """Test that irrelevant models are filtered out."""
        from openai.types import Model
        
        # Include some models that should be filtered
        all_models = [
            Model(id="gpt-3.5-turbo", created=1680000000, object="model", owned_by="openai"),
            Model(id="davinci-002", created=1680000001, object="model", owned_by="openai"),  # Should be filtered
            Model(id="text-curie-001", created=1680000002, object="model", owned_by="openai"),  # Should be filtered
            Model(id="gpt-4", created=1680000003, object="model", owned_by="openai"),
        ]
        
        with patch.object(OpenAIService, 'list_models', return_value=all_models):
            client = ollama.Client(host="http://localhost:11434")
            response = client.list()
            
            model_names = [m["name"] for m in response["models"]]
            
            # Should include GPT models
            assert "gpt-3.5-turbo" in model_names
            assert "gpt-4" in model_names
            
            # Should NOT include legacy models
            assert "davinci-002" not in model_names
            assert "text-curie-001" not in model_names
    
    def test_concurrent_requests(self, test_client):
        """Test handling of concurrent SDK requests."""
        import concurrent.futures
        from openai.types import Model
        
        mock_models = [
            Model(id="gpt-3.5-turbo", created=1680000000, object="model", owned_by="openai")
        ]
        
        def make_request():
            client = ollama.Client(host="http://localhost:11434")
            return client.list()
        
        with patch.object(OpenAIService, 'list_models', return_value=mock_models):
            # Make 10 concurrent requests
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_request) for _ in range(10)]
                results = [f.result() for f in concurrent.futures.as_completed(futures)]
            
            # All should succeed
            assert len(results) == 10
            for result in results:
                assert len(result["models"]) == 1
                assert result["models"][0]["name"] == "gpt-3.5-turbo"


@pytest.mark.sdk
@pytest.mark.requires_api_key
class TestOllamaSDKRealAPI:
    """Tests against real OpenAI API (requires valid API key)."""
    
    @pytest.fixture
    def real_api_key(self):
        """Get real API key from environment."""
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key or api_key == "test-key-12345":
            pytest.skip("Real OpenAI API key required")
        return api_key
    
    def test_real_api_list(self, real_api_key, monkeypatch):
        """Test against real OpenAI API."""
        # Set real API key
        monkeypatch.setenv("OPENAI_API_KEY", real_api_key)
        
        # Create real client
        client = ollama.Client(host="http://localhost:11434")
        
        # List models
        response = client.list()
        
        # Should have real models
        assert len(response["models"]) > 0
        
        # Verify format
        for model in response["models"]:
            assert "name" in model
            assert "modified_at" in model
            assert "size" in model
            
            # Real models should have reasonable sizes
            assert model["size"] > 1000000  # At least 1MB
```

#### Step 3: Create Performance Benchmarks
**tests/integration/test_performance_benchmarks.py**:
```python
"""Performance benchmarks for SDK compatibility."""
import statistics
import time
from typing import List
from unittest.mock import patch

import pytest

ollama = pytest.importorskip("ollama")


@pytest.mark.sdk
@pytest.mark.slow
class TestPerformanceBenchmarks:
    """Performance benchmarks for Ollama SDK operations."""
    
    def measure_response_time(self, func, iterations: int = 100) -> List[float]:
        """Measure response time over multiple iterations."""
        times = []
        for _ in range(iterations):
            start = time.time()
            func()
            times.append(time.time() - start)
        return times
    
    def test_list_models_benchmark(self, test_client):
        """Benchmark model listing performance."""
        from openai.types import Model
        
        # Mock models
        mock_models = [
            Model(id=f"model-{i}", created=1680000000+i, object="model", owned_by="openai")
            for i in range(50)  # 50 models
        ]
        
        with patch.object(OpenAIService, 'list_models', return_value=mock_models):
            client = ollama.Client(host="http://localhost:11434")
            
            # Warmup
            for _ in range(10):
                client.list()
            
            # Measure
            times = self.measure_response_time(lambda: client.list(), iterations=100)
            
            # Calculate statistics
            avg_time = statistics.mean(times)
            median_time = statistics.median(times)
            p95_time = statistics.quantiles(times, n=20)[18]  # 95th percentile
            p99_time = statistics.quantiles(times, n=100)[98]  # 99th percentile
            
            # Log results
            print(f"\nList Models Performance:")
            print(f"  Average: {avg_time*1000:.2f}ms")
            print(f"  Median: {median_time*1000:.2f}ms")
            print(f"  P95: {p95_time*1000:.2f}ms")
            print(f"  P99: {p99_time*1000:.2f}ms")
            
            # Assert performance requirements
            assert avg_time < 0.1  # Average under 100ms
            assert p95_time < 0.15  # 95th percentile under 150ms
            assert p99_time < 0.2   # 99th percentile under 200ms


@pytest.mark.sdk
class TestOllamaSDKEdgeCases:
    """Test edge cases with Ollama SDK."""
    
    def test_special_characters_in_model_names(self, test_client):
        """Test handling of special characters in model names."""
        from openai.types import Model
        
        # Models with special characters
        special_models = [
            Model(id="gpt-3.5-turbo", created=1680000000, object="model", owned_by="openai"),
            Model(id="gpt-4-vision-preview", created=1680000001, object="model", owned_by="openai"),
            Model(id="text-embedding-3-large", created=1680000002, object="model", owned_by="openai"),
        ]
        
        with patch.object(OpenAIService, 'list_models', return_value=special_models):
            client = ollama.Client(host="http://localhost:11434")
            response = client.list()
            
            # All models should be present
            model_names = [m["name"] for m in response["models"]]
            assert "gpt-3.5-turbo" in model_names
            assert "gpt-4-vision-preview" in model_names
            assert "text-embedding-3-large" in model_names
    
    def test_very_large_model_list(self, test_client):
        """Test handling of very large model lists."""
        from openai.types import Model
        
        # Create 1000 models
        large_model_list = [
            Model(id=f"model-{i:04d}", created=1680000000+i, object="model", owned_by="openai")
            for i in range(1000)
        ]
        
        with patch.object(OpenAIService, 'list_models', return_value=large_model_list):
            client = ollama.Client(host="http://localhost:11434")
            response = client.list()
            
            # Should handle large lists
            assert len(response["models"]) <= 1000  # May filter some
            
            # Should complete in reasonable time
            start = time.time()
            client.list()
            duration = time.time() - start
            assert duration < 1.0  # Under 1 second even for large list


def test_ollama_cli_compatibility():
    """Test compatibility with Ollama CLI (manual test)."""
    instructions = """
    Manual test for Ollama CLI compatibility:
    
    1. Start the proxy:
       python -m ollama_openai_proxy
    
    2. In another terminal, set Ollama host:
       export OLLAMA_HOST=http://localhost:11434
    
    3. List models using Ollama CLI:
       ollama list
    
    4. Verify output shows available models
    
    Expected output format:
    NAME                    ID              SIZE    MODIFIED
    gpt-3.5-turbo          gpt-3.5-turbo   1.5 GB  2024-01-20 10:30:00
    gpt-4                  gpt-4           20 GB   2024-01-20 10:30:00
    """
    print(instructions)
```

### Verification Steps

1. **Install Ollama SDK:**
   ```bash
   pip install ollama
   ```

2. **Run SDK compatibility tests:**
   ```bash
   # Run all SDK tests
   pytest tests/integration/test_ollama_sdk_list.py -v -m sdk
   
   # Run including slow tests
   pytest tests/integration/test_ollama_sdk_list.py -v -m "sdk" --slow
   ```

3. **Test with real Ollama Python SDK:**
   ```python
   import ollama
   
   # Start proxy in one terminal
   # python -m ollama_openai_proxy
   
   # In Python:
   client = ollama.Client(host="http://localhost:11434")
   models = client.list()
   print(f"Found {len(models['models'])} models")
   for model in models['models']:
       print(f"- {model['name']} ({model['size']/1e9:.1f}GB)")
   ```

4. **Run performance benchmarks:**
   ```bash
   pytest tests/integration/test_performance_benchmarks.py -v -s
   ```

5. **Test with real API (optional):**
   ```bash
   # Requires valid OPENAI_API_KEY
   OPENAI_API_KEY=sk-... pytest -m requires_api_key
   ```

### Definition of Done Checklist

- [ ] Ollama SDK installed in dev dependencies
- [ ] SDK compatibility tests created
- [ ] Tests verify exact response format
- [ ] Model name preservation verified
- [ ] Timestamp format verified (ISO with Z)
- [ ] Size field present and reasonable
- [ ] Empty list scenario tested
- [ ] Error handling tested
- [ ] Performance under 100ms overhead
- [ ] Multi-version SDK compatibility tested
- [ ] Edge cases handled properly
- [ ] Real API test available (optional)

### Manual Testing Checklist

- [ ] Ollama Python SDK client.list() works
- [ ] Response format matches Ollama exactly
- [ ] No authentication errors
- [ ] Performance acceptable
- [ ] Ollama CLI works (with OLLAMA_HOST set)

### Common Issues & Solutions

1. **Ollama SDK not found:**
   - Install with `pip install ollama`
   - Check it's in requirements-dev.txt

2. **Connection refused:**
   - Ensure proxy is running on port 11434
   - Check no firewall blocking

3. **Format mismatch:**
   - Verify timestamp ends with 'Z'
   - Ensure size is integer, not float
   - Check model names match exactly

### Success Criteria

- Existing Ollama code works without modification
- SDK methods return expected data structures
- Performance overhead < 100ms
- All edge cases handled gracefully

### Next Steps

After completing this story:
1. Run full test suite including SDK tests
2. Test with real Ollama applications
3. Document any compatibility notes
4. Create PR for Epic 1 completion
5. Celebrate successful foundation! 🎉