import os
from pathlib import Path

# Get the absolute path to the project root directory
ROOT_DIR = Path(__file__).parent.absolute()

# Define all paths relative to the root directory
PATHS = {
    'docs': ROOT_DIR / 'docs',
    'images': ROOT_DIR / 'images',
    'outputs': ROOT_DIR / 'outputs',
    'templates': ROOT_DIR / 'available_templates',
    'uploads': ROOT_DIR / 'uploads',
    'document_parsed': ROOT_DIR / 'document_parsed.json',
    'presentation_data': ROOT_DIR / 'presentation_data.json',
    'slide_content': ROOT_DIR / 'slide_content.json'
}

# Create necessary directories if they don't exist
for path in PATHS.values():
    if isinstance(path, Path) and not path.suffix:  # Only create directories, not files
        path.mkdir(exist_ok=True) 