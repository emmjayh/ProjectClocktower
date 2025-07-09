"""
Basic tests that don't require heavy dependencies
"""

import pytest


def test_basic_functionality():
    """Basic test to ensure pytest works"""
    assert True


def test_python_version():
    """Test Python version compatibility"""
    import sys
    
    version = sys.version_info
    assert version.major == 3
    assert version.minor >= 11


def test_imports():
    """Test that basic Python imports work"""
    import json
    import logging
    import random
    from dataclasses import dataclass
    from datetime import datetime
    from typing import Any, Dict, Optional
    
    # Test basic functionality
    assert json.loads('{"test": true}')["test"] is True
    assert isinstance(datetime.now(), datetime)
    
    @dataclass
    class TestClass:
        name: str
        value: int = 0
    
    test_obj = TestClass("test", 42)
    assert test_obj.name == "test"
    assert test_obj.value == 42