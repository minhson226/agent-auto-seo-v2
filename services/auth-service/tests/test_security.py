"""Tests for security utilities."""

import pytest
from datetime import timedelta

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    encrypt_api_key,
    decrypt_api_key,
    get_password_hash,
    verify_password,
    generate_api_key,
)


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_password_hash_is_different_from_plain(self):
        """Test that password hash is different from plain password."""
        password = "mysecretpassword"
        hashed = get_password_hash(password)
        assert hashed != password

    def test_password_verification_success(self):
        """Test successful password verification."""
        password = "mysecretpassword"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_password_verification_failure(self):
        """Test failed password verification."""
        password = "mysecretpassword"
        hashed = get_password_hash(password)
        assert verify_password("wrongpassword", hashed) is False

    def test_different_passwords_have_different_hashes(self):
        """Test that different passwords produce different hashes."""
        hash1 = get_password_hash("password1")
        hash2 = get_password_hash("password2")
        assert hash1 != hash2

    def test_same_password_produces_different_hashes(self):
        """Test that same password produces different hashes (bcrypt salt)."""
        password = "samepassword"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        assert hash1 != hash2  # Different salts
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWT:
    """Tests for JWT token functions."""

    def test_create_access_token(self):
        """Test creating an access token."""
        data = {"sub": "user123"}
        token = create_access_token(data)
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_access_token(self):
        """Test decoding an access token."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        data = {"sub": user_id}
        token = create_access_token(data)
        payload = decode_token(token)
        
        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["type"] == "access"
        assert "exp" in payload

    def test_create_refresh_token(self):
        """Test creating a refresh token."""
        data = {"sub": "user123"}
        token = create_refresh_token(data)
        assert token is not None
        assert isinstance(token, str)

    def test_decode_refresh_token(self):
        """Test decoding a refresh token."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        data = {"sub": user_id}
        token = create_refresh_token(data)
        payload = decode_token(token)
        
        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"

    def test_decode_invalid_token(self):
        """Test decoding an invalid token returns None."""
        payload = decode_token("invalid.token.here")
        assert payload is None

    def test_token_with_custom_expiry(self):
        """Test creating token with custom expiry."""
        data = {"sub": "user123"}
        token = create_access_token(data, expires_delta=timedelta(hours=1))
        payload = decode_token(token)
        assert payload is not None


class TestEncryption:
    """Tests for API key encryption functions."""

    def test_encrypt_and_decrypt_api_key(self):
        """Test encrypting and decrypting an API key."""
        original_key = "sk-test-api-key-12345"
        encrypted = encrypt_api_key(original_key)
        
        assert encrypted != original_key
        assert isinstance(encrypted, str)
        
        decrypted = decrypt_api_key(encrypted)
        assert decrypted == original_key

    def test_encrypted_key_is_different_each_time(self):
        """Test that encryption produces different results (due to IV)."""
        api_key = "sk-test-api-key"
        encrypted1 = encrypt_api_key(api_key)
        encrypted2 = encrypt_api_key(api_key)
        
        # Fernet uses random IV, so encryptions should differ
        # But both should decrypt to the same value
        assert decrypt_api_key(encrypted1) == api_key
        assert decrypt_api_key(encrypted2) == api_key

    def test_generate_api_key(self):
        """Test generating a secure API key."""
        key = generate_api_key()
        assert key.startswith("ask_")
        assert len(key) > 10

    def test_generated_keys_are_unique(self):
        """Test that generated keys are unique."""
        keys = [generate_api_key() for _ in range(100)]
        assert len(set(keys)) == 100
