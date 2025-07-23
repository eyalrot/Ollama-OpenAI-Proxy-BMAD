#!/usr/bin/env python3
"""
Simple test script to demonstrate Ollama SDK compatibility.

Usage:
    1. Start the proxy: python -m ollama_openai_proxy
    2. Run this script: python examples/test_ollama_sdk.py
"""
import os
import sys

try:
    import ollama
except ImportError:
    print("Error: ollama package not installed")
    print("Install with: pip install ollama")
    sys.exit(1)

def test_list_models():
    """Test listing models with Ollama SDK."""
    print("Testing Ollama SDK compatibility...\n")
    
    # Create client pointing to proxy
    client = ollama.Client(host="http://localhost:11434")
    
    try:
        # List models
        print("Listing models...")
        response = client.list()
        
        print(f"Found {len(response.models)} models:\n")
        
        # Display models
        for i, model in enumerate(response.models, 1):
            size_gb = model.size / 1e9
            print(f"{i}. Model:")
            print(f"   Size: {size_gb:.1f} GB")
            print(f"   Modified: {model.modified_at}")
            print(f"   Digest: {model.digest[:20]}...")
            print()
            
            if i >= 5:  # Show first 5 models
                print(f"... and {len(response.models) - 5} more models")
                break
        
        print("\n✅ SDK compatibility test PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ SDK compatibility test FAILED!")
        print(f"Error: {e}")
        return False

def main():
    """Run the test."""
    # Check if API key is set
    if not os.environ.get("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY not set")
        print("Set it with: export OPENAI_API_KEY=your-key-here")
        sys.exit(1)
    
    # Run test
    success = test_list_models()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()