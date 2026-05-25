"""Quick check for semantic chunk quality."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.chunk_knowledge import load_and_chunk_all

chunks = load_and_chunk_all()
print("total", len(chunks))

branding = [c for c in chunks if c["metadata"].get("category") == "branding"]
print("branding", len(branding))

principles = [c for c in branding if c["metadata"].get("chunk_type") == "principle"]
print("principle chunks", len(principles))
for c in principles[:15]:
    m = c["metadata"]
    title = m.get("title", "")[:70]
    wc = m.get("word_count", 0)
    sys.stdout.buffer.write(f"  {wc:3d}w  {title}\n".encode("utf-8", errors="replace"))
