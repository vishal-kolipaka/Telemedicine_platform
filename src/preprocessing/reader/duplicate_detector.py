"""
Duplicate Detection — hash-based, runs BEFORE extraction.

Computes a file hash and checks it against known_hashes (a dict mapping
{file_hash: document_id}). If a match is found, returns immediately with
an EXACT_DUPLICATE signal — no extractor is ever invoked.

Section 5.4 of the spec.
"""

import hashlib


def compute_file_hash(file_path: str, algorithm: str = "sha256") -> str:
    """Compute the cryptographic hash of a file.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm name (default: sha256).

    Returns:
        Hex digest string.
    """
    hasher = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files without loading all into memory
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def check_duplicate(
    file_hash: str, known_hashes: dict[str, str]
) -> dict | None:
    """Check if a file hash matches any known document.

    Args:
        file_hash: Hash of the current file.
        known_hashes: Dict mapping {file_hash: document_id} of previously
                      processed documents.

    Returns:
        {"status": "EXACT_DUPLICATE", "matched_document_id": str} if match
        found, or None if no match.
    """
    if file_hash in known_hashes:
        return {
            "status": "EXACT_DUPLICATE",
            "matched_document_id": known_hashes[file_hash],
        }
    return None
