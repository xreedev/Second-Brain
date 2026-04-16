import os

def fetch_file_content(file_path):
    """Fetch the content of a file, returning an error message if it fails."""
    if not os.path.exists(file_path):
        return f"File does not exist: {file_path}"
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"