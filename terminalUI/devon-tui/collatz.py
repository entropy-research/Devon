def collatz(n):
    if n <= 0:
        raise ValueError("Input must be a positive integer")
    sequence = [n]
    while n != 1:
        if n % 2 == 0:
            n = n // 2
        else:
            n = 3 * n + 1
        sequence.append(n)
    return sequence

n = int(input("Enter a number: "))
sequence = collatz(n)
print("Collatz sequence for", n, "is:")
print(sequence)



