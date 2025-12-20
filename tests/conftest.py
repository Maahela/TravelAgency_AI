import sys
import os
from pathlib import Path

# Add the project root directory to the Python path
# This allows tests in tests/ to import modules from the root (e.g. database, utils)
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))
