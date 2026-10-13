"""Interview problem runner.

Usage:
    python interview/run.py CODE [--base-url URL] [--force]

The interviewer gives you a code. A start code writes the problem brief and seed
data into ./problem/. A check code runs that problem's automated checks against
your running backend (default http://127.0.0.1:8000).

Only the Python standard library is used, so this works in Codespaces and on
macOS, Linux and Windows (use ``py`` instead of ``python`` on Windows if needed).
"""

import argparse
import hashlib
import hmac
import json
import sys
from pathlib import Path

INTERVIEW_DIR = Path(__file__).resolve().parent
DATA_DIR = INTERVIEW_DIR / "data"
PROBLEM_DIR = INTERVIEW_DIR.parent / "problem"
NAME_SALT = b"interview-name-v1"
SCRYPT_PARAMS = {"n": 2**14, "r": 8, "p": 1}
HEADER_SIZE = 64


def normalise(code):
    """Return the canonical form of a code: upper case, no spaces or dashes."""
    return code.strip().upper().replace("-", "").replace(" ", "")


def file_name(code):
    """Return the data file name that belongs to a normalised code."""
    digest = hashlib.scrypt(code.encode(), salt=NAME_SALT, dklen=12, **SCRYPT_PARAMS)
    return digest.hex() + ".bin"


def derive_keys(code, salt):
    """Derive the encryption and MAC keys for a code and per-file salt."""
    key = hashlib.scrypt(code.encode(), salt=salt, dklen=64, **SCRYPT_PARAMS)
    return key[:32], key[32:]


def xor_stream(enc_key, nonce, data):
    """XOR data with a SHAKE-256 keystream; the same call encrypts and decrypts."""
    stream = hashlib.shake_256(enc_key + nonce).digest(len(data))
    return (int.from_bytes(data, "big") ^ int.from_bytes(stream, "big")).to_bytes(len(data), "big")


def decrypt(code, blob):
    """Return the plaintext of a data file, or raise ValueError if it was altered."""
    salt, nonce, tag, ciphertext = blob[:16], blob[16:32], blob[32:HEADER_SIZE], blob[HEADER_SIZE:]
    enc_key, mac_key = derive_keys(code, salt)
    expected = hmac.new(mac_key, nonce + ciphertext, hashlib.sha256).digest()
    if not hmac.compare_digest(expected, tag):
        raise ValueError("data file is corrupted")
    return xor_stream(enc_key, nonce, ciphertext)


def write_problem(payload, force):
    """Write the brief and seed files for a start code."""
    marker = PROBLEM_DIR / ".title"
    if PROBLEM_DIR.exists() and not force:
        current = marker.read_text().strip() if marker.exists() else "an unknown problem"
        if current != payload["title"]:
            print(f"./problem/ already holds {current}. Rerun with --force to replace it.")
            return 1
    PROBLEM_DIR.mkdir(exist_ok=True)
    for name, content in payload["files"].items():
        (PROBLEM_DIR / name).write_text(content, encoding="utf-8")
    marker.write_text(payload["title"] + "\n")
    print(f"Problem: {payload['title']}")
    for name in payload["files"]:
        print(f"  wrote problem/{name}")
    print("\nStart by reading problem/BRIEF.md.")
    return 0


def run_checks(payload, base_url):
    """Run a check payload in memory against the backend."""
    namespace = {"__name__": "interview_checks", "PROBLEM_DIR": PROBLEM_DIR}
    exec(compile(payload["source"], "<interview checks>", "exec"), namespace)
    return namespace["main"](base_url)


def main():
    parser = argparse.ArgumentParser(description="Unlock an interview problem or run its checks.")
    parser.add_argument("code", help="code given by the interviewer")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="backend URL for checks")
    parser.add_argument("--force", action="store_true", help="replace an existing ./problem/ folder")
    args = parser.parse_args()

    code = normalise(args.code)
    path = DATA_DIR / file_name(code)
    if not path.exists():
        print("Unknown code. Check it with your interviewer.")
        return 1
    try:
        payload = json.loads(decrypt(code, path.read_bytes()))
    except ValueError as exc:
        print(f"Could not open this code's data: {exc}.")
        return 1

    if payload["kind"] == "start":
        return write_problem(payload, args.force)
    return run_checks(payload, args.base_url)


if __name__ == "__main__":
    sys.exit(main())
