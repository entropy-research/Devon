import sys
import difflib
import argparse

def apply_udiff(udiff_path, fuzziness=0):
    with open(udiff_path, 'r') as udiff_file:
        udiff_text = udiff_file.read()


    patches = difflib.PatchSet.from_string(udiff_text)

    for patch in patches:
        target_file = patch.target
        with open(target_file, 'r') as f:
            content = f.read()
        
        updated_content = patch.apply(content, fuzziness=fuzziness)

        with open(target_file, 'w') as f:
            f.write(updated_content)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("udiff_path", help="Path to the udiff file")
    parser.add_argument("-f", "--fuzziness", type=int, default=0, help="Fuzziness level for patch application")
    args = parser.parse_args()
    apply_udiff(args.udiff_path, args.fuzziness)
