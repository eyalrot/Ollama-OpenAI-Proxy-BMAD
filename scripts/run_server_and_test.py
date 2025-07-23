#!/usr/bin/env python3
"""Run proxy server asynchronously and execute integration tests."""
import asyncio
import os
import sys
import urllib.error
import urllib.request
from contextlib import asynccontextmanager
from typing import AsyncIterator


async def start_proxy_server() -> asyncio.subprocess.Process:
    """Start the proxy server asynchronously."""
    print("🚀 Starting proxy server...")

    # Start the server process
    process = await asyncio.create_subprocess_exec(
        sys.executable, "-m", "ollama_openai_proxy.main", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    # Wait for server to be ready
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            req = urllib.request.Request("http://localhost:11434/health")
            with urllib.request.urlopen(req, timeout=1) as response:
                if response.status == 200:
                    print("✅ Proxy server is ready!")
                    return process
        except (urllib.error.URLError, urllib.error.HTTPError):
            await asyncio.sleep(0.5)

        if attempt % 5 == 0:
            print(f"   Waiting for server to start... ({attempt}/{max_attempts})")

    # Check if process is still running
    if process.returncode is not None:
        stdout, stderr = await process.communicate()
        print("❌ Server process exited unexpectedly!")
        print(f"Stdout: {stdout.decode()}")
        print(f"Stderr: {stderr.decode()}")
        raise RuntimeError("Failed to start proxy server")

    raise RuntimeError("Server did not respond within timeout")


@asynccontextmanager
async def proxy_server() -> AsyncIterator[asyncio.subprocess.Process]:
    """Context manager to run proxy server."""
    process = None
    try:
        process = await start_proxy_server()
        yield process
    finally:
        if process:
            print("\n🛑 Stopping proxy server...")
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                print("⚠️  Server didn't stop gracefully, killing it...")
                process.kill()
                await process.wait()


async def run_tests() -> int:
    """Run the integration tests."""
    print("\n🧪 Running Ollama SDK generate integration tests...")

    # Run pytest
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "pytest",
        "tests/integration/test_ollama_sdk_generate.py",
        "-v",
        "--tb=short",
        "-s",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    # Stream output in real-time
    if process.stdout:
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            print(line.decode().rstrip())

    await process.wait()
    return process.returncode or 0


async def main() -> int:
    """Main async function."""
    print("🔍 Ollama-OpenAI Proxy Server & Integration Test Runner")
    print("=" * 60)

    # Check OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY not set - tests may fail")
        print("   Set it with: export OPENAI_API_KEY='your-key-here'")
    else:
        print(f"✅ OpenAI API key found: {api_key[:8]}...")

    # Check if Ollama SDK is installed
    try:
        import ollama  # noqa: F401

        print("✅ Ollama SDK is installed")
    except ImportError:
        print("❌ Ollama SDK not installed!")
        print("   Install with: pip install ollama")
        return 1

    # Run server and tests
    try:
        async with proxy_server():
            # Give it a moment to fully initialize
            await asyncio.sleep(1)

            # Run the tests
            test_result = await run_tests()

            if test_result == 0:
                print("\n✅ All tests passed!")
            else:
                print(f"\n❌ Tests failed with exit code: {test_result}")

            return test_result

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
