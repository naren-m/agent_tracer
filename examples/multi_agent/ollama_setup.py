#!/usr/bin/env python3
"""
Ollama Setup Verification Script

Checks that:
1. Ollama server is running
2. llama2 model is available
3. Basic text generation works

Usage:
    python ollama_setup.py
"""

import sys
import ollama


def check_ollama_running():
    """Check if Ollama server is running."""
    print("Checking if Ollama server is running...")

    try:
        client = ollama.Client()
        # Try to list models - will fail if server not running
        client.list()
        print("✓ Ollama server is running")
        return client
    except Exception as e:
        print("❌ Ollama server is not running")
        print("\nTo install and start Ollama:")
        print("1. Visit https://ollama.ai/download")
        print("2. Download and install Ollama for your OS")
        print("3. Start Ollama (it should run in the background)")
        print("\nOr use the command line:")
        print("  macOS/Linux: Install from https://ollama.ai/download")
        print("  Then run: ollama serve")
        print(f"\nError details: {e}")
        return None


def check_llama2_available(client):
    """Check if llama model is available (llama2, llama3.x, etc)."""
    print("\nChecking if llama model is available...")

    try:
        models = client.list()
        # models is a ListModelsResponse with a models attribute
        model_names = [m.model for m in models.models]

        # Check for any llama model
        llama_models = [name for name in model_names if 'llama' in name.lower()]

        if llama_models:
            print(f"✓ Llama model(s) found: {llama_models[0]}")
            if len(llama_models) > 1:
                print(f"  (and {len(llama_models)-1} more)")
            return True
        else:
            print("❌ No llama model found")
            print("\nAvailable models:", model_names if model_names else "None")
            print("\nTo pull a llama model:")
            print("  ollama pull llama2")
            print("  ollama pull llama3.1")
            print("  ollama pull llama3.2")
            print("\nThis will download ~3-5GB")
            return False

    except Exception as e:
        print(f"❌ Error checking models: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_simple_generation(client):
    """Test basic text generation with available llama model."""
    print("\nTesting basic text generation...")

    try:
        # Find first available llama model
        models = client.list()
        model_names = [m.model for m in models.models]
        llama_models = [name for name in model_names if 'llama' in name.lower()]

        if not llama_models:
            print("❌ No llama model available for testing")
            return False

        model_to_use = llama_models[0]
        print(f"Using model: {model_to_use}")

        response = client.chat(
            model=model_to_use,
            messages=[
                {
                    'role': 'user',
                    'content': 'Say "hello" and nothing else.',
                }
            ]
        )

        content = response['message']['content']
        print(f"✓ Generation works! Response: {content.strip()[:50]}...")
        return True

    except Exception as e:
        print(f"❌ Generation failed: {e}")
        return False


def main():
    """Run all checks."""
    print("=" * 60)
    print("Ollama Setup Verification")
    print("=" * 60)

    # Check 1: Ollama running
    client = check_ollama_running()
    if not client:
        sys.exit(1)

    # Check 2: llama2 available
    if not check_llama2_available(client):
        sys.exit(1)

    # Check 3: Generation works
    if not test_simple_generation(client):
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✓ All checks passed! Ollama is ready for use.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
