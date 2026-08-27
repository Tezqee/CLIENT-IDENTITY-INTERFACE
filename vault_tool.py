#!/usr/bin/env python3
"""
Technocore Vault Interoperability Tool.
Converts keys between:
- Python CLI format (identity.pem - encrypted PKCS8 PEM)
- Web UI format (agent-vault.json - encrypted AES-GCM vault)
"""

import sys
import os
import json
import base64
import getpass
from pathlib import Path

# Add dependency checks
try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
    )
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
except ImportError:
    print("Error: The 'cryptography' library is required. Please install it using:")
    print("pip install cryptography")
    sys.exit(1)

# Import helper functions from technocore_agent if available
sys.path.append(str(Path(__file__).parent))
try:
    from technocore_agent import load_identity, create_identity, did_from_private_key
except ImportError:
    # Inline fallback implementations if technocore_agent is missing
    def did_from_private_key(private_key):
        from technocore_agent import did_from_private_key as original_did
        return original_did(private_key)

def encrypt_vault(raw_private_bytes, passphrase, did):
    salt = os.urandom(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = kdf.derive(passphrase.encode('utf-8'))
    aesgcm = AESGCM(key)
    iv = os.urandom(12)
    # Encrypts and appends the 16-byte auth tag at the end (matching Web Crypto GCM)
    ciphertext_with_tag = aesgcm.encrypt(iv, raw_private_bytes, None)
    return {
        "did": did,
        "salt": salt.hex(),
        "iv": iv.hex(),
        # Use base64URL (no padding) to match Web UI format
        "ciphertext": base64.urlsafe_b64encode(ciphertext_with_tag).decode('utf-8').rstrip('=')
    }

def decrypt_vault(vault_data, passphrase):
    salt = bytes.fromhex(vault_data["salt"])
    iv = bytes.fromhex(vault_data["iv"])
    # Support both standard base64 and base64URL (with or without padding)
    ciphertext_str = vault_data["ciphertext"]
    # Add padding if missing
    padding = 4 - len(ciphertext_str) % 4
    if padding != 4:
        ciphertext_str += '=' * padding
    # Handle both base64URL (-_) and standard base64 (+/)
    ciphertext_with_tag = base64.urlsafe_b64decode(ciphertext_str)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = kdf.derive(passphrase.encode('utf-8'))
    aesgcm = AESGCM(key)
    # Decrypts by splitting the 16-byte auth tag automatically from the end
    raw_private_bytes = aesgcm.decrypt(iv, ciphertext_with_tag, None)
    return raw_private_bytes

def cli_to_web():
    pem_path = Path("identity.pem")
    if not pem_path.exists():
        print(f"Error: {pem_path.name} not found in the current directory.")
        sys.exit(1)

    print(f"Reading encrypted CLI identity from {pem_path.name}...")
    passphrase = getpass.getpass("Enter passphrase for identity.pem: ")
    
    try:
        private_key = load_identity(pem_path, passphrase.encode('utf-8'))
    except Exception as e:
        print(f"Error loading identity: {e}")
        sys.exit(1)
        
    did = did_from_private_key(private_key)
    print(f"Loaded DID: {did}")
    
    raw_private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    web_passphrase = getpass.getpass("Enter passphrase to encrypt Web Vault (12+ chars): ")
    if len(web_passphrase) < 12:
        print("Error: Web vault passphrase must be at least 12 characters.")
        sys.exit(1)
        
    confirm = getpass.getpass("Confirm Web Vault passphrase: ")
    if web_passphrase != confirm:
        print("Error: Passphrases do not match.")
        sys.exit(1)
        
    vault = encrypt_vault(raw_private_bytes, web_passphrase, did)
    
    out_path = Path("agent-vault.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(vault, f, indent=2)
        
    print(f"Success! Web UI vault written to {out_path.name}")
    print("You can now import this file under the 'Identity' tab in the Web UI dashboard.")

def web_to_cli():
    vault_path = Path("agent-vault.json")
    if not vault_path.exists():
        print(f"Error: {vault_path.name} not found in the current directory.")
        sys.exit(1)
        
    print(f"Reading encrypted Web UI vault from {vault_path.name}...")
    with open(vault_path, "r", encoding="utf-8") as f:
        try:
            vault_data = json.load(f)
        except Exception as e:
            print(f"Error reading JSON: {e}")
            sys.exit(1)
            
    required_fields = ("did", "salt", "iv", "ciphertext")
    if any(field not in vault_data for field in required_fields):
        print(f"Error: {vault_path.name} is missing required fields.")
        sys.exit(1)
        
    passphrase = getpass.getpass("Enter passphrase for agent-vault.json: ")
    
    try:
        raw_private_bytes = decrypt_vault(vault_data, passphrase)
    except Exception as e:
        print(f"Decryption failed: {e}")
        sys.exit(1)
        
    private_key = Ed25519PrivateKey.from_private_bytes(raw_private_bytes)
    did = did_from_private_key(private_key)
    if did != vault_data["did"]:
        print("Warning: Derived DID does not match DID in vault data.")
        
    print(f"Decrypted DID: {did}")
    
    cli_passphrase = getpass.getpass("Enter passphrase to encrypt identity.pem (12+ chars): ")
    if len(cli_passphrase) < 12:
        print("Error: CLI passphrase must be at least 12 characters.")
        sys.exit(1)
        
    confirm = getpass.getpass("Confirm CLI passphrase: ")
    if cli_passphrase != confirm:
        print("Error: Passphrases do not match.")
        sys.exit(1)
        
    out_path = Path("identity.pem")
    if out_path.exists():
        overwrite = input(f"{out_path.name} already exists. Overwrite? (y/n): ")
        if overwrite.lower() != 'y':
            print("Aborting.")
            sys.exit(0)
            
        # Delete old file first to ensure secure file permissions can be created by create_identity
        out_path.unlink()
        
    try:
        # Create identity using technocore_agent utility to ensure permissions and formats are correct
        create_identity(out_path, cli_passphrase)
        # However, create_identity generates a new key. We want to write our imported key.
        # Let's manually encrypt and write our key matching the exact PKCS8 format of technocore_agent
        # delete file created by create_identity
        out_path.unlink()
        
        encoded_passphrase = cli_passphrase.encode("utf-8")
        private_bytes = private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.BestAvailableEncryption(encoded_passphrase),
        )
        
        # Write securely with 0600 permissions
        descriptor = os.open(out_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as key_file:
            key_file.write(private_bytes)
            key_file.flush()
            os.fsync(key_file.fileno())
        os.chmod(out_path, 0o600)
        
        print(f"Success! Encrypted CLI identity written to {out_path.name}")
        print("You can now run 'python technocore_agent.py did' to confirm the DID matches.")
        
    except Exception as e:
        print(f"Error writing identity file: {e}")
        sys.exit(1)

def main():
    print("=" * 50)
    print("        Technocore Vault Interoperability Tool")
    print("=" * 50)
    print("1. Convert CLI Key to Web Vault (identity.pem -> agent-vault.json)")
    print("2. Convert Web Vault to CLI Key (agent-vault.json -> identity.pem)")
    print("=" * 50)
    
    choice = input("Select an option (1 or 2): ").strip()
    if choice == '1':
        cli_to_web()
    elif choice == '2':
        web_to_cli()
    else:
        print("Invalid choice. Exiting.")
        sys.exit(1)

if __name__ == "__main__":
    main()
