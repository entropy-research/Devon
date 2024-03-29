



from agent.prime_number import is_prime

def test_is_prime():
    assert is_prime(2) == True
    assert is_prime(3) == True
    assert is_prime(5) == True
    assert is_prime(7) == True
    assert is_prime(11) == True
    assert is_prime(13) == True
    assert is_prime(17) == True
    assert is_prime(19) == True

    assert is_prime(1) == False
    assert is_prime(0) == False
    assert is_prime(-1) == False


    assert is_prime(4) == False
    assert is_prime(6) == False
    assert is_prime(8) == False
    assert is_prime(9) == False
    assert is_prime(10) == False
    assert is_prime(12) == False
    assert is_prime(14) == False
    assert is_prime(15) == False
    assert is_prime(16) == False
    assert is_prime(18) == False
    assert is_prime(20) == False
    assert is_prime(21) == False
    assert is_prime(22) == False
    assert is_prime(23) == False
    assert is_prime(24) == False
    assert is_prime(25) == False

    assert is_prime(27) == False
    assert is_prime(28) == False
    assert is_prime(29) == False
    assert is_prime(30) == False

