#!/usr/bin/env python3
"""
VAPID Key Generator for Web Push Notifications
Run this script once to generate your VAPID keys
"""

try:
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives import serialization
    import base64
except ImportError:
    print("Error: cryptography not installed")
    print("Install it with: pip install cryptography")
    exit(1)


def urlsafe_b64encode(data):
    """Base64 URL-safe encoding without padding"""
    return base64.urlsafe_b64encode(data).strip(b'=').decode('utf-8')


def generate_keys():
    """Generate VAPID key pair"""
    print("=" * 60)
    print("  VAPID KEY GENERATOR FOR WEB PUSH NOTIFICATIONS")
    print("=" * 60)
    print()

    # Generate private key
    private_key = ec.generate_private_key(ec.SECP256R1())

    # Get public key
    public_key = private_key.public_key()

    # Serialize private key
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    # Serialize public key (uncompressed point format)
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )

    # Encode to base64 URL-safe format
    private_key_b64 = urlsafe_b64encode(private_bytes)
    public_key_b64 = urlsafe_b64encode(public_bytes)

    print("✅ Keys generated successfully!")
    print()
    print("Add these to your .env file:")
    print("-" * 60)
    print(f"VAPID_PUBLIC_KEY={public_key_b64}")
    print(f"VAPID_PRIVATE_KEY={private_key_b64}")
    print(f"VAPID_CLAIM_EMAIL=mailto:your-email@example.com")
    print("-" * 60)
    print()
    print("⚠️  IMPORTANT:")
    print("1. Keep your PRIVATE key secret!")
    print("2. Add .env to .gitignore")
    print("3. Update VAPID_CLAIM_EMAIL with your actual email")
    print()


if __name__ == '__main__':
    generate_keys()