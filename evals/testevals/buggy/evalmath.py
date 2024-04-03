# cli_app.py
import argparse

def add_numbers(a, b):
    # Bug 1: Incorrect addition logic
    return a - b

def multiply_numbers(a, b):
    # Bug 2: Incorrect multiplication logic
    return a + b

def main():
    parser = argparse.ArgumentParser(description="CLI Application")
    parser.add_argument("operation", choices=["add", "multiply"], help="Operation to perform")
    parser.add_argument("num1", type=int, help="First number")
    parser.add_argument("num2", type=int, help="Second number")
    args = parser.parse_args()

    if args.operation == "add":
        result = add_numbers(args.num1, args.num2)
        print("Result:", result)
    elif args.operation == "multiply":
        result = multiply_numbers(args.num1, args.num2)
        print("Result:", result)
    else:
        # Bug 3: Incorrect error handling
        print("Valid operation!")

if __name__ == "__main__":
    main()