"""
Contract tests to ensure API responses match Ollama's exact format.

These tests validate against the OpenAPI specification to prevent
the kind of SDK compatibility issues encountered in Epic 1.
"""
from pathlib import Path
from typing import Any, Dict

import pytest
import yaml  # type: ignore[import-untyped]
from jsonschema import Draft7Validator, RefResolver
from jsonschema.exceptions import ValidationError
from ollama_openai_proxy.models.ollama import OllamaModel, OllamaTagsResponse


class TestOllamaAPIContract:
    """Test that our API responses match the Ollama OpenAPI specification."""

    @pytest.fixture(scope="class")
    def openapi_spec(self) -> Dict[str, Any]:
        """Load the Ollama OpenAPI specification."""
        spec_path = Path(__file__).parent.parent.parent / "api-specs" / "ollama-openapi.yaml"
        with open(spec_path) as f:
            return yaml.safe_load(f)  # type: ignore[no-any-return]

    @pytest.fixture
    def schema_validator(self, openapi_spec: Dict[str, Any]) -> tuple[Dict[str, Any], RefResolver]:
        """Create a JSON schema validator for the OpenAPI spec."""
        resolver = RefResolver(
            base_uri=f"file://{Path(__file__).parent.parent.parent}/api-specs/",
            referrer=openapi_spec,
        )
        return openapi_spec, resolver

    def validate_against_schema(
        self, data: Any, path: str, method: str, openapi_spec: Dict, resolver: RefResolver
    ) -> None:
        """Validate data against OpenAPI schema for endpoint."""
        # Get schema for endpoint
        path_spec = openapi_spec["paths"][path]
        method_spec = path_spec[method.lower()]
        response_spec = method_spec["responses"]["200"]
        schema = response_spec["content"]["application/json"]["schema"]

        # Validate
        validator = Draft7Validator(schema, resolver=resolver)
        validator.validate(data)

    def test_tags_response_contract(
        self, schema_validator: tuple[Dict[str, Any], RefResolver]
    ) -> None:
        """Test that /api/tags response matches Ollama's exact format."""
        openapi_spec, resolver = schema_validator

        # Create test response matching our current implementation
        response = OllamaTagsResponse(
            models=[
                OllamaModel(
                    name="gpt-3.5-turbo",
                    modified_at="2023-02-28T20:56:42Z",
                    size=1500000000,
                    digest="sha256:d2f48b2c5812",
                )
            ]
        )

        # Convert to dict (this is what FastAPI does)
        response_dict = response.model_dump()

        # This test will FAIL because Ollama expects both 'name' AND 'model' fields
        with pytest.raises(ValidationError) as exc_info:
            self.validate_against_schema(response_dict, "/api/tags", "GET", openapi_spec, resolver)

        # The error should be about missing 'model' field
        assert "model" in str(exc_info.value)

    def test_correct_tags_format(
        self, schema_validator: tuple[Dict[str, Any], RefResolver]
    ) -> None:
        """Test the correct Ollama format with both name and model fields."""
        openapi_spec, resolver = schema_validator

        # This is the CORRECT format Ollama expects
        correct_response = {
            "models": [
                {
                    "name": "llama3.1:latest",
                    "model": "llama3.1:latest",  # DUPLICATE field!
                    "modified_at": "2025-01-21T16:53:57.496699591-08:00",
                    "size": 4920753328,
                    "digest": (
                        "sha256:46e0c10c039e019119339687c3c1757" "cc81b9da49709a3b3924863ba87ca666e"
                    ),
                    "details": {
                        "parent_model": "",
                        "format": "gguf",
                        "family": "llama",
                        "families": ["llama"],
                        "parameter_size": "8.0B",
                        "quantization_level": "Q4_K_M",
                    },
                }
            ]
        }

        # This should pass validation
        self.validate_against_schema(correct_response, "/api/tags", "GET", openapi_spec, resolver)

    def test_model_field_requirements(self) -> None:
        """Document the exact field requirements for Ollama compatibility."""
        # Based on the Postman collection, each model MUST have:
        required_fields = {
            "name": str,  # e.g., "llama3.1:latest"
            "model": str,  # SAME as name!
            "modified_at": str,  # RFC3339 with timezone
            "size": int,  # In bytes
            "digest": str,  # SHA256 hash
        }

        # Document optional fields (not used in test but good for documentation)
        # optional_fields = {
        #     "details": {
        #         "parent_model": str,
        #         "format": str,
        #         "family": str,
        #         "families": list,
        #         "parameter_size": str,
        #         "quantization_level": str,
        #     }
        # }

        # This test documents the requirements
        assert all(field in required_fields for field in ["name", "model"])
        assert required_fields["name"] == required_fields["model"]  # Same type

    @pytest.mark.parametrize(
        "endpoint,method,request_body",
        [
            ("/api/generate", "POST", {"model": "llama3.1", "prompt": "Hello"}),
            (
                "/api/chat",
                "POST",
                {"model": "llama3.1", "messages": [{"role": "user", "content": "Hi"}]},
            ),
            ("/api/show", "POST", {"name": "llama3.1"}),
            ("/api/embed", "POST", {"model": "llama3.1", "input": "test"}),
        ],
    )
    def test_request_contracts(
        self,
        endpoint: str,
        method: str,
        request_body: Dict[str, Any],
        schema_validator: tuple[Dict[str, Any], RefResolver],
    ) -> None:
        """Test that requests match expected schema."""
        openapi_spec, resolver = schema_validator

        # Get request schema
        path_spec = openapi_spec["paths"][endpoint]
        method_spec = path_spec[method.lower()]
        request_spec = method_spec["requestBody"]["content"]["application/json"]["schema"]

        # Validate request
        validator = Draft7Validator(request_spec, resolver=resolver)
        validator.validate(request_body)


class TestOllamaModelCorrection:
    """Test the corrected Ollama model that includes both name and model fields."""

    def test_corrected_ollama_model(self) -> None:
        """Propose a corrected OllamaModel that matches the actual API."""
        from pydantic import BaseModel, Field

        class OllamaModelCorrected(BaseModel):
            """Corrected model that matches actual Ollama API."""

            name: str = Field(..., description="Model name/ID")
            model: str = Field(..., description="Model name/ID (duplicate of name)")
            modified_at: str = Field(..., description="RFC3339 timestamp with timezone")
            size: int = Field(..., description="Model size in bytes")
            digest: str = Field(..., description="Model digest/hash")
            details: Dict[str, Any] = Field(default_factory=dict, description="Model details")

            def __init__(self, **data: Any) -> None:
                # Automatically duplicate name to model if not provided
                if "model" not in data and "name" in data:
                    data["model"] = data["name"]
                super().__init__(**data)

        # Test the corrected model
        model = OllamaModelCorrected(
            name="gpt-3.5-turbo",
            modified_at="2023-02-28T20:56:42.000000000-08:00",
            size=1500000000,
            digest="sha256:abc123",
        )

        # Both fields should exist and be equal
        assert model.name == model.model == "gpt-3.5-turbo"

        # This is what the API should return
        api_response = model.model_dump()
        assert api_response["name"] == api_response["model"]


def test_sdk_transformation() -> None:
    """Document how the Ollama SDK transforms the API response."""
    # What the API returns:
    api_response = {
        "models": [
            {
                "name": "llama3.1:latest",
                "model": "llama3.1:latest",
                "modified_at": "2025-01-21T16:53:57.496699591-08:00",
                "size": 4920753328,
                "digest": (
                    "sha256:46e0c10c039e019119339687c3c1757" "cc81b9da49709a3b3924863ba87ca666e"
                ),
            }
        ]
    }

    # What the SDK exposes (pseudo-code):
    # sdk_response.models[0].model = None  # SDK bug or transformation?
    # sdk_response.models[0].name = <not accessible>
    # sdk_response.models[0].size = 4920753328
    # sdk_response.models[0].digest = "sha256:..."

    # This mismatch is why Epic 1 tests failed!
    assert api_response["models"][0]["name"] == api_response["models"][0]["model"]
