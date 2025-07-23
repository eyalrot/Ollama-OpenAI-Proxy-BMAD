#!/usr/bin/env python3
"""
Validate API responses against the Ollama OpenAPI specification.

This tool helps ensure that your proxy implementation matches the expected
Ollama API format exactly.
"""
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import httpx
import yaml  # type: ignore[import-untyped]
from jsonschema import Draft7Validator, RefResolver
from jsonschema.exceptions import ValidationError


class OpenAPIValidator:
    """Validates API responses against OpenAPI specification."""

    def __init__(self, spec_path: str):
        """Initialize validator with OpenAPI spec."""
        self.spec_path = Path(spec_path)
        with open(self.spec_path) as f:
            self.spec = yaml.safe_load(f)

        # Create resolver for $ref references
        self.resolver = RefResolver(base_uri=f"file://{self.spec_path.parent}/", referrer=self.spec)

    def get_response_schema(self, path: str, method: str, status_code: int = 200) -> Optional[Dict[str, Any]]:
        """Get response schema for a specific endpoint."""
        path_spec = self.spec.get("paths", {}).get(path)
        if not path_spec:
            return None

        method_spec = path_spec.get(method.lower())
        if not method_spec:
            return None

        response_spec = method_spec.get("responses", {}).get(str(status_code))
        if not response_spec:
            return None

        content = response_spec.get("content", {}).get("application/json", {})
        return content.get("schema")  # type: ignore[no-any-return]

    def validate_response(self, path: str, method: str, response_data: Any, status_code: int = 200) -> bool:
        """Validate response data against schema."""
        schema = self.get_response_schema(path, method, status_code)
        if not schema:
            print(f"No schema found for {method} {path} (status {status_code})")
            return False

        try:
            # Resolve any $ref in the schema
            validator = Draft7Validator(schema, resolver=self.resolver)
            validator.validate(response_data)
            return True
        except ValidationError as e:
            print(f"Validation error: {e.message}")
            print(f"Failed at path: {' -> '.join(str(p) for p in e.absolute_path)}")
            return False


def test_tags_endpoint(validator: OpenAPIValidator, base_url: str) -> None:
    """Test /api/tags endpoint compliance."""
    print("\n=== Testing /api/tags ===")

    response = httpx.get(f"{base_url}/api/tags")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Response has {len(data.get('models', []))} models")

        # Validate against schema
        if validator.validate_response("/api/tags", "GET", data):
            print("✅ Response validates against OpenAPI schema")

            # Check specific fields that caused issues
            if data.get("models"):
                model = data["models"][0]
                print("\nFirst model structure:")
                print(f"  - name: {'✅' if 'name' in model else '❌'}")
                print(f"  - model: {'✅' if 'model' in model else '❌'}")
                print(f"  - modified_at: {'✅' if 'modified_at' in model else '❌'}")
                print(f"  - size: {'✅' if 'size' in model else '❌'}")
                print(f"  - digest: {'✅' if 'digest' in model else '❌'}")
        else:
            print("❌ Response does not match OpenAPI schema")
    else:
        print(f"❌ Unexpected status code: {response.status_code}")


def test_show_endpoint(validator: OpenAPIValidator, base_url: str, model_name: str) -> None:
    """Test /api/show endpoint compliance."""
    print(f"\n=== Testing /api/show for {model_name} ===")

    response = httpx.post(f"{base_url}/api/show", json={"name": model_name})
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        if validator.validate_response("/api/show", "POST", data):
            print("✅ Response validates against OpenAPI schema")
        else:
            print("❌ Response does not match OpenAPI schema")
    else:
        print(f"❌ Unexpected status code: {response.status_code}")


def compare_with_ollama_sdk() -> None:
    """Compare API responses with SDK expectations."""
    print("\n=== SDK Compatibility Check ===")

    try:
        import ollama

        client = ollama.Client(host="http://localhost:11434")

        # Test list() method
        sdk_response = client.list()
        print(f"SDK list() returns type: {type(sdk_response)}")
        print(f"Has 'models' attribute: {hasattr(sdk_response, 'models')}")

        if hasattr(sdk_response, "models") and sdk_response.models:
            model = sdk_response.models[0]
            print("\nSDK model object attributes:")
            for attr in ["name", "model", "modified_at", "size", "digest"]:
                value = getattr(model, attr, "<missing>")
                print(f"  - {attr}: {value}")
    except ImportError:
        print("Ollama SDK not installed. Run: pip install ollama")
    except Exception as e:
        print(f"Error testing SDK: {e}")


def main() -> None:
    """Run validation tests."""
    if len(sys.argv) < 2:
        print("Usage: python validate_against_openapi.py <openapi-spec.yaml> [base-url]")
        sys.exit(1)

    spec_path = sys.argv[1]
    base_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:11434"

    # Initialize validator
    validator = OpenAPIValidator(spec_path)

    print(f"Validating against: {spec_path}")
    print(f"Testing API at: {base_url}")

    # Test endpoints
    test_tags_endpoint(validator, base_url)

    # Get a model name from tags to test show endpoint
    try:
        response = httpx.get(f"{base_url}/api/tags")
        if response.status_code == 200:
            models = response.json().get("models", [])
            if models:
                test_show_endpoint(validator, base_url, models[0]["name"])
    except Exception as e:
        print(f"Error getting model list: {e}")

    # Compare with SDK
    compare_with_ollama_sdk()


if __name__ == "__main__":
    main()
