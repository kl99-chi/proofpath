from pathlib import Path

# Where browser uploads land before store_attachment copies them into data/uploads.
INCOMING_DIR = Path(__file__).resolve().parent.parent / "data" / "uploads_incoming"