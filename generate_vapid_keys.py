#!/usr/bin/env python3
"""
Generate VAPID keys for Web Push Notifications
Run this once and add the keys to your .env file
"""

import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization


def generate_keys():
    """Generate VAPID key pair"""
    # Generate private key
    private_key = ec.generate_private_key(ec.SECP256R1())

    # Get public key
    public_key = private_key.public_key()

    # Serialize private key to PEM format
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    # Serialize public key to uncompressed point format for Web Push
    public_numbers = public_key.public_numbers()

    # Convert to uncompressed point format (0x04 + x + y)
    x_bytes = public_numbers.x.to_bytes(32, byteorder='big')
    y_bytes = public_numbers.y.to_bytes(32, byteorder='big')
    uncompressed_point = b'\x04' + x_bytes + y_bytes

    # Base64 URL-safe encode
    public_key_b64 = base64.urlsafe_b64encode(uncompressed_point).decode('utf-8').rstrip('=')

    # Private key for VAPID (just the raw 32-byte key)
    private_numbers = private_key.private_numbers()
    private_key_bytes = private_numbers.private_value.to_bytes(32, byteorder='big')
    private_key_b64 = base64.urlsafe_b64encode(private_key_bytes).decode('utf-8').rstrip('=')

    print("\n" + "=" * 70)
    print("🔐 VAPID KEYS GENERATED - Add these to your .env file:")
    print("=" * 70)
    print(f"\nVAPID_PRIVATE_KEY={private_key_b64}")
    print(f"VAPID_PUBLIC_KEY={public_key_b64}")
    print(f'VAPID_CLAIM_EMAIL=mailto:admin@nextsteps.com')
    print("\n" + "=" * 70)
    print("⚠️  IMPORTANT:")
    print("   1. Keep the PRIVATE key SECRET - never commit to Git!")
    print("   2. The PUBLIC key is safe to expose to clients")
    print("   3. Update the email to your actual contact email")
    print("=" * 70 + "\n")

    # Also save to a file for backup
    try:
        with open('.env.vapid', 'w') as f:
            f.write(f"VAPID_PRIVATE_KEY={private_key_b64}\n")
            f.write(f"VAPID_PUBLIC_KEY={public_key_b64}\n")
            f.write(f"VAPID_CLAIM_EMAIL=mailto:admin@nextsteps.com\n")
        print("✅ Keys also saved to .env.vapid (backup file)")
        print("   Copy these lines to your .env file\n")
    except Exception as e:
        print(f"⚠️  Could not save backup file: {e}\n")


if __name__ == "__main__":
    generate_keys()