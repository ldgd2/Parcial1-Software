import os
import re
from pathlib import Path

def find_file(filename, src_dir):
    # Returns the absolute alias path e.g. @/features/...
    # filename can be "types.ts" or "types"
    if not filename.endswith((".ts", ".tsx", ".js", ".jsx")):
        possible_extensions = [".ts", ".tsx", ".js", ".jsx"]
    else:
        possible_extensions = [""]
        
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            for ext in possible_extensions:
                if file == filename + ext:
                    # found it
                    rel_path = os.path.relpath(os.path.join(root, file), src_dir)
                    # convert backslash to slash
                    rel_path = rel_path.replace("\\", "/")
                    # remove extension for the import
                    if rel_path.endswith((".ts", ".tsx")):
                        rel_path = rel_path.rsplit(".", 1)[0]
                    return "@/" + rel_path
    return None

def main():
    src_dir = r"c:\Users\ldgd2\Documents\universidad\software 1\sem 2-2026\examen1\Examen\frontend\src"
    
    # Regex to find imports: import ... from '...' or import '...'
    import_pattern = re.compile(r"""(import\s+.*?from\s+['"])(.*?)(['"])|(import\s+['"])(.*?)(['"])""")
    
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith((".ts", ".tsx", ".js", ".jsx")):
                filepath = os.path.join(root, file)
                
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                original = content
                
                def replacer(match):
                    is_from = match.group(1) is not None
                    prefix = match.group(1) or match.group(4)
                    import_path = match.group(2) or match.group(5)
                    suffix = match.group(3) or match.group(6)
                    
                    if import_path.startswith("."):
                        # Resolve the relative path to see if it exists
                        current_dir = os.path.dirname(filepath)
                        target_path = os.path.normpath(os.path.join(current_dir, import_path))
                        
                        # Check if exists (with some extension)
                        exists = False
                        for ext in ["", ".ts", ".tsx", ".js", ".jsx", ".css"]:
                            if os.path.exists(target_path + ext) and os.path.isfile(target_path + ext):
                                exists = True
                                break
                                
                        if not exists:
                            # It's broken. Find the basename and search the whole src tree.
                            basename = os.path.basename(import_path)
                            new_path = find_file(basename, src_dir)
                            if new_path:
                                return prefix + new_path + suffix
                    return match.group(0)
                    
                content = import_pattern.sub(replacer, content)
                
                if content != original:
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(content)
                    print(f"Auto-fixed imports in: {filepath}")

if __name__ == "__main__":
    main()
