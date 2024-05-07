import os
import re

password_pattern = r'(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}'

def check_secrets(directory):
    for root, dirs, files in os.walk(directory):
        print(f"Files in directory: {files}")
        print(f"Scanning directory: {root}")
        for file in [f for f in files if f in os.listdir(root)]:
            print(f"Checking file: {file}")
            file_path = os.path.join(root, file)
            
            with open(file_path, 'r') as f:
                lines = f.readlines()
                
                for i, line in enumerate(lines):
                    api_key_pattern = r'[A-Za-z0-9]{32,45}'
                    api_key_match = re.search(api_key_pattern, line)
                    if api_key_match:
                        print(f"Potential API key found in {file_path} on line {i+1}")
                        print(f"Key: {api_key_match.group()}")
                        print("---")
                        
                        # If Python file, print enclosing function or class name
                        if file_path.endswith(".py"):
                            func_line = i
                            while func_line >= 0:
                                if lines[func_line].startswith("def ") or lines[func_line].startswith("class "):
                                    func_name = lines[func_line].split()[1].split("(")[0]
                                    print(f"Secret found in function/class: {func_name}")
                                    print("---")
                                    break
                                func_line -= 1
                        
                    password_match = re.search(password_pattern, line)
                    if password_match:
                        print(f"Potential password found in {file_path} on line {i+1}")
                        print(f"Password: {password_match.string}")
                        print("---")

if __name__ == '__main__':
    codebase_dir = 'test_secrets'  # Search test directory
    check_secrets(codebase_dir)
