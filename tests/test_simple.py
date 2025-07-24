"""Simple test to verify pytest is working."""

import pytest


def test_addition():
    """Test basic addition."""
    assert 1 + 1 == 2


def test_string_concat():
    """Test string concatenation."""
    assert "hello" + " " + "world" == "hello world"


@pytest.mark.asyncio
async def test_async_function():
    """Test async functionality."""
    async def get_value():
        return 42
    
    result = await get_value()
    assert result == 42


class TestSimpleClass:
    """Test class with multiple tests."""
    
    def test_list_operations(self):
        """Test list operations."""
        lst = [1, 2, 3]
        lst.append(4)
        assert len(lst) == 4
        assert lst[-1] == 4
    
    def test_dict_operations(self):
        """Test dictionary operations."""
        d = {"key": "value"}
        d["new_key"] = "new_value"
        assert len(d) == 2
        assert d.get("key") == "value"