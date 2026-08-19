import sys
from pathlib import Path

# Make the shared golden-scenario definitions importable from the test modules.
sys.path.insert(0, str(Path(__file__).resolve().parent))
