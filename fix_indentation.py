# Fix indentation issues in video_sequence_controller.py
import re

# Read the file
input_file = 'node/video_sequence_controller.py'
with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

# Make sure the CATEGORY for VideoSequenceControllerNode is correct
for i, line in enumerate(lines):
    if 'CATEGORY = "Hagenland"' in line:
        lines[i] = '    CATEGORY = "🔄Hagenland"\n'
        print(f"Fixed CATEGORY on line {i+1}")

# Check for any misaligned else statements
for i, line in enumerate(lines):
    if re.search(r'^(\s*)else:', line):
        indent = len(re.match(r'^(\s*)', line).group(1))
        # Check if this is at a weird indent level
        if indent != 8 and indent != 12 and indent != 16 and indent != 20:
            print(f"Found misaligned else at line {i+1} with indent {indent}")
            # Try to fix it by aligning with the nearest reasonable indentation
            if indent < 12:
                lines[i] = ' ' * 8 + 'else:\n'
                print(f"  Fixed to indent 8")
            elif indent < 16:
                lines[i] = ' ' * 12 + 'else:\n'
                print(f"  Fixed to indent 12")
            elif indent < 20:
                lines[i] = ' ' * 16 + 'else:\n'
                print(f"  Fixed to indent 16")
            else:
                lines[i] = ' ' * 20 + 'else:\n'
                print(f"  Fixed to indent 20")

# Write the fixed file
with open(input_file, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f"File {input_file} has been fixed") 