import pytest
from collatz import collatz

def test_positive_integer():
    assert collatz(5) == [5, 16, 8, 4, 2, 1]

def test_negative_integer():
    with pytest.raises(ValueError):
        collatz(-5)

def test_zero_input():
    with pytest.raises(ValueError):
        collatz(0)

def test_large_integer():
    result = collatz(100)
    assert result[-1] == 1
    assert len(result) == 26

def test_sequence_ends_with_one():
    for i in range(1, 1000):
        assert collatz(i)[-1] == 1
