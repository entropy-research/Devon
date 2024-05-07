from collatz import collatz

print("Testing collatz function manually...")

# Test a positive integer
print("\nTesting positive integer input: 5")
try:
    result = collatz(5)
    print("Result:", result)
except Exception as e:
    print("Exception:", str(e))

# Test a negative integer 
print("\nTesting negative integer input: -5")
try:
    result = collatz(-5)
    print("Result:", result)
except Exception as e:
    print("Exception:", str(e))

# Test zero
print("\nTesting zero input")
try:  
    result = collatz(0)
    print("Result:", result)
except Exception as e:
    print("Exception:", str(e))

# Test a large integer
print("\nTesting large integer input: 100")
try:
    result = collatz(100)
    print("Result:", result)
    print("Sequence length:", len(result))
    print("Ends in 1?", result[-1] == 1)
except Exception as e:
    print("Exception:", str(e))

print("\nManual testing complete.")
