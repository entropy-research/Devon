total = 0
while True:
    num = input("Enter a number (or press Enter to finish): ")
    if num == "":
        break
    
    try:
        total += int(num)
    except ValueError:
        print("Invalid input. Please enter a valid number.")
        continue

print(f"The sum of the numbers entered is: {total}")
