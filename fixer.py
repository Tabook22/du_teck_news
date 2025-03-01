import os
from pathlib import Path
import sys

def check_file_encoding(filepath):
    """Check if file can be read with UTF-8 encoding."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            f.read()
        return True
    except UnicodeDecodeError:
        return False
    except Exception as e:
        print(f"Error processing {filepath}: {str(e)}")
        return False

def normalize_path(path):
    """Normalize path for Windows compatibility."""
    return str(Path(path)).replace('\\', '/')

def find_problematic_files(directory="."):
    """Find all Python files with non-UTF-8 encoding."""
    problematic_files = []
    
    # Convert to absolute path
    directory = os.path.abspath(directory)
    
    for root, dirs, files in os.walk(directory):
        # Skip common directories that should be ignored
        dirs[:] = [d for d in dirs if d not in {
            '.venv', 'venv', '__pycache__', 
            '.git', '.idea', '.vs', 'build', 'dist'
        }]
            
        for file in files:
            if file.endswith(('.py', '.pyw')):
                filepath = os.path.join(root, file)
                if not check_file_encoding(filepath):
                    # Get relative path from current directory
                    rel_path = os.path.relpath(filepath, directory)
                    problematic_files.append(normalize_path(rel_path))
    
    return problematic_files

def main():
    print("Scanning for files with encoding issues...\n")
    
    files = find_problematic_files()
    
    if not files:
        print("No files with encoding issues found.")
        return
        
    print("Files with encoding issues:")
    for file in files:
        print(f"  - {file}")
    
    # Create ignore list with normalized paths
    ignore_list = ".venv," + ",".join(files)
    
    print("\nTo use with pipreqs, copy and run this EXACT command:")
    print(f'pipreqs . --ignore "{ignore_list}" --encoding=latin1')
    
    # Also write the command to a file for easy copy-paste
    with open('pipreqs_command.txt', 'w') as f:
        f.write(f'pipreqs . --ignore "{ignore_list}" --encoding=latin1')
    print("\nThe command has also been saved to 'pipreqs_command.txt'")

if __name__ == "__main__":
    main()