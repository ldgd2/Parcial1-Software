import os
import re

emoji_pattern = re.compile(
    r"[\U00010000-\U0010ffff]",
    flags=re.UNICODE
)

def find_emojis():
    src_dir = r"c:\Users\ldgd2\Documents\universidad\software 1\sem 2-2026\examen1\Examen\frontend\src"
    
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith((".ts", ".tsx", ".css", ".html")):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        for i, line in enumerate(lines):
                            emojis_found = emoji_pattern.findall(line)
                            if emojis_found:
                                print(f"File: {filepath} Line: {i+1} Emojis: {emojis_found}")
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")

if __name__ == "__main__":
    find_emojis()
