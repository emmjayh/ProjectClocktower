#!/usr/bin/env python3
"""Test what dependencies are available"""

import sys

print("Python version:", sys.version)
print("\nChecking dependencies:")

deps = [
    "numpy",
    "torch",
    "whisper",
    "openai_whisper",
    "requests",
    "pyaudio",
    "pygame",
    "librosa",
    "sklearn",
]

for dep in deps:
    try:
        if dep == "openai_whisper":
            import openai_whisper

            print(f"✓ {dep} - installed")
        else:
            __import__(dep)
            print(f"✓ {dep} - installed")
    except ImportError as e:
        print(f"✗ {dep} - NOT installed ({e})")

# Check if models directory exists
from pathlib import Path

models_dir = Path(__file__).parent / "models"
print(f"\nModels directory exists: {models_dir.exists()}")
if models_dir.exists():
    print("Contents:")
    for item in models_dir.iterdir():
        print(f"  - {item.name}")
