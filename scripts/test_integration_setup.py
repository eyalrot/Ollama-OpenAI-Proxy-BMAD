#!/usr/bin/env python3
"""Verify integration test setup with real proxy server and OpenAI API key."""
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from typing import Optional


def check_openai_api_key() -> bool:
    """Check if OpenAI API key is set."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY environment variable not set")
        print("   Please set it with: export OPENAI_API_KEY='your-key-here'")
        return False

    if api_key.startswith("sk-"):
        print(f"✅ OpenAI API key found: {api_key[:8]}...")
        return True
    else:
        print(f"⚠️  OpenAI API key found but doesn't start with 'sk-': {api_key[:8]}...")
        return True  # Still allow testing


def check_proxy_server(port: int = 11434) -> bool:
    """Check if proxy server is running."""
    try:
        req = urllib.request.Request(f"http://localhost:{port}/health")
        with urllib.request.urlopen(req, timeout=2) as response:
            if response.status == 200:
                print(f"✅ Proxy server is running on port {port}")
                return True
            else:
                print(f"⚠️  Proxy server responded with status {response.status}")
                return False
    except urllib.error.URLError:
        print(f"❌ Proxy server is not running on port {port}")
        print("   Start it with: python -m ollama_openai_proxy.main")
        return False
    except Exception as e:
        print(f"❌ Error checking proxy server: {e}")
        return False


def check_ollama_sdk() -> bool:
    """Check if Ollama SDK is installed."""
    try:
        import ollama

        print(f"✅ Ollama SDK is installed (version {getattr(ollama, '__version__', 'unknown')})")
        return True
    except ImportError:
        print("❌ Ollama SDK not installed")
        print("   Install it with: pip install ollama")
        return False


def test_basic_connection() -> bool:
    """Test basic connection through Ollama SDK."""
    try:
        import ollama

        client = ollama.Client(host="http://localhost:11434")

        # Try to list models
        response = client.list()
        if hasattr(response, "models"):
            model_count = len(response.models)
            print(f"✅ Successfully connected via Ollama SDK - found {model_count} models")
            if model_count > 0:
                print(f"   Available models: {', '.join(m.model for m in response.models[:3])}...")
            return True
        else:
            print("⚠️  Connected but unexpected response format")
            return False
    except Exception as e:
        print(f"❌ Failed to connect via Ollama SDK: {e}")
        return False


def run_integration_tests(specific_test: Optional[str] = None) -> bool:
    """Run the integration tests."""
    print("\n🧪 Running integration tests...")

    cmd = [sys.executable, "-m", "pytest", "tests/integration/test_ollama_sdk_generate.py", "-v", "--tb=short"]

    if specific_test:
        cmd.append(f"-k={specific_test}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ All integration tests passed!")
            # Show summary
            for line in result.stdout.split("\n"):
                if "passed" in line and ("failed" in line or "error" in line or "skipped" in line):
                    print(f"   {line.strip()}")
            return True
        else:
            print("❌ Some integration tests failed")
            print("\nTest output:")
            print(result.stdout)
            if result.stderr:
                print("\nErrors:")
                print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False


def main() -> int:
    """Main verification flow."""
    print("🔍 Ollama-OpenAI Proxy Integration Test Verification")
    print("=" * 50)

    all_good = True

    # Check prerequisites
    if not check_openai_api_key():
        all_good = False

    if not check_ollama_sdk():
        all_good = False
        print("\n❌ Cannot proceed without Ollama SDK")
        return 1

    if not check_proxy_server():
        all_good = False
        print("\n💡 Attempting to start proxy server...")
        # Try to start the server
        server_process = subprocess.Popen(
            [sys.executable, "-m", "ollama_openai_proxy.main"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        # Wait a bit for server to start
        print("   Waiting for server to start...")
        time.sleep(3)

        if check_proxy_server():
            print("✅ Proxy server started successfully")
        else:
            print("❌ Failed to start proxy server")
            server_process.terminate()
            return 1
    else:
        server_process = None

    # Test basic connection
    if not test_basic_connection():
        all_good = False

    if not all_good:
        print("\n⚠️  Some prerequisites failed, but attempting tests anyway...")

    # Run a quick test first
    print("\n🧪 Running quick connectivity test...")
    if run_integration_tests("test_server_connectivity_generate"):
        print("\n🧪 Running full integration test suite...")
        run_integration_tests()

    # Cleanup
    if server_process:
        print("\n🛑 Stopping proxy server...")
        server_process.terminate()
        server_process.wait(timeout=5)

    print("\n✨ Verification complete!")
    return 0 if all_good else 1


if __name__ == "__main__":
    sys.exit(main())
