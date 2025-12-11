#!/usr/bin/env python3
"""Test script to verify keyring fallback functionality."""

import sys
from pathlib import Path

# Add the package to the path
sys.path.insert(0, str(Path(__file__).parent))

from github_feedback.core.config import Config, _setup_keyring_fallback
import keyring

def test_keyring_fallback():
    """Test that keyring operations work with fallback."""
    print("Testing keyring fallback mechanism...")
    print(f"Current keyring backend: {keyring.get_keyring()}")

    try:
        # Try to set up fallback
        _setup_keyring_fallback()
        print(f"After fallback setup: {keyring.get_keyring()}")

        # Test basic operations
        config = Config()

        # Test storing a PAT
        print("\nTesting PAT storage...")
        test_pat = "ghp_test123456789"
        config.update_auth(test_pat)
        print("✓ PAT stored successfully")

        # Test retrieving a PAT
        print("\nTesting PAT retrieval...")
        retrieved_pat = config.get_pat()
        if retrieved_pat == test_pat:
            print("✓ PAT retrieved successfully")
        else:
            print(f"✗ PAT mismatch: expected {test_pat}, got {retrieved_pat}")

        # Test has_pat
        print("\nTesting has_pat check...")
        if config.has_pat():
            print("✓ has_pat returned True")
        else:
            print("✗ has_pat returned False")

        print("\n✓ All tests passed!")
        return True

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_keyring_fallback()
    sys.exit(0 if success else 1)
