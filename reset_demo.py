"""Reset ProofPath to clean demo data. Run from anywhere: python reset_demo.py"""
from pathlib import Path

root = Path(__file__).resolve().parent
data = root / "data" / "proofpath_data.json"
uploads = root / "data" / "uploads"

if data.exists():
    data.unlink()
if uploads.exists():
    for f in uploads.iterdir():
        if f.is_file():
            f.unlink()
print("Demo data cleared. It is recreated on the next launch.")