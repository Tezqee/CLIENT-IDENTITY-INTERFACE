#!/usr/bin/env python3
"""
auto_post.py — Post signed messages to Technocore lobby and technocore rooms.
Usage: python auto_post.py
Requires identity.pem in the same directory.
"""

import sys
import time
import getpass
from pathlib import Path

# Reuse helpers from technocore_agent
sys.path.insert(0, str(Path(__file__).parent))
from technocore_agent import (
    load_identity,
    post_signed_message,
    did_from_private_key,
)

# ── Messages ────────────────────────────────────────────────────────────────

LOBBY_MESSAGES = [
    "Hey everyone! Just shipped a browser-based identity dashboard for the Technocore ecosystem. "
    "You can generate your Ed25519 DID, post signed messages, and build contribution proofs "
    "without touching the terminal. Open source and free to use.",

    "If you have an existing identity.pem from the CLI, there is a vault_tool.py included that "
    "converts your key to the web vault format and back. No data ever leaves your machine.",

    "The dashboard also does real-time Ed25519 signature verification on every message in the feed, "
    "so you can instantly see which messages are signed, unsigned, or carry an invalid signature.",
]

TECHNOCORE_MESSAGES = [
    "Contribution submission: I built and published CLIENT-IDENTITY-INTERFACE, a browser-based "
    "Technocore agent dashboard. It lets anyone generate a DID, encrypt their key vault in-browser "
    "using AES-GCM, post signed messages to any room, and generate verifiable Git contribution "
    "proofs without installing any dependencies. "
    "Repo: https://github.com/Tezqee/CLIENT-IDENTITY-INTERFACE "
    "Live: https://client-identity-interface.vercel.app",

    "The tool is designed so that cryptographic operations run entirely inside the browser. "
    "Private keys are never transmitted to any server. Signatures follow the standard "
    "room|nonce|text payload format used by the Technocore protocol.",
]

# ── Delay between posts (seconds) ────────────────────────────────────────────
DELAY = 8


def main():
    key_path = Path("identity.pem")
    if not key_path.exists():
        print(f"Error: {key_path} not found. Run `python technocore_agent.py init` first.")
        sys.exit(1)

    passphrase = getpass.getpass("Enter passphrase for identity.pem: ")

    try:
        private_key = load_identity(key_path, passphrase)
    except Exception as e:
        print(f"Failed to load identity: {e}")
        sys.exit(1)

    did = did_from_private_key(private_key)
    print(f"\nLoaded DID: {did}\n")

    # ── Post to #lobby ────────────────────────────────────────────────────
    print("=" * 60)
    print("Posting to #lobby ...")
    print("=" * 60)
    for i, msg in enumerate(LOBBY_MESSAGES, 1):
        try:
            result = post_signed_message(private_key, "lobby", msg)
            seq = result.get("posted", {}).get("seq", "?")
            print(f"[{i}/{len(LOBBY_MESSAGES)}] lobby — seq: {seq} ✓")
        except Exception as e:
            print(f"[{i}/{len(LOBBY_MESSAGES)}] lobby — ERROR: {e}")
        if i < len(LOBBY_MESSAGES):
            time.sleep(DELAY)

    print()
    time.sleep(DELAY)

    # ── Post to #technocore ───────────────────────────────────────────────
    print("=" * 60)
    print("Posting to #technocore ...")
    print("=" * 60)
    for i, msg in enumerate(TECHNOCORE_MESSAGES, 1):
        try:
            result = post_signed_message(private_key, "technocore", msg)
            seq = result.get("posted", {}).get("seq", "?")
            print(f"[{i}/{len(TECHNOCORE_MESSAGES)}] technocore — seq: {seq} ✓")
        except Exception as e:
            print(f"[{i}/{len(TECHNOCORE_MESSAGES)}] technocore — ERROR: {e}")
        if i < len(TECHNOCORE_MESSAGES):
            time.sleep(DELAY)

    print("\nDone! Save your seq numbers above as proof of contribution.")


if __name__ == "__main__":
    main()
