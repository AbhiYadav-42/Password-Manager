"""
1️⃣ Derive an encryption key from the master password
2️⃣ Encrypt new passwords before saving them to JSON
3️⃣ Decrypt passwords when reading from JSON
4️⃣ Salt handling

"""
import os
import base64
from cryptography.fernet import Fernet
from base64 import urlsafe_b64encode
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend



def encryption(master_password: str , salt:bytes) -> bytes:
  password_bytes = master_password.encode()

  kdf = PBKDF2HMAC(
    algorithm= hashes.SHA256(),
    length=32,
    salt = salt,
    iterations=480000
  )

  key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
  return key


def decryption(encrypted_password:str, key:bytes) ->str:
  cipher = Fernet(key)
  decrypted_bytes = cipher.decrypt(encrypted_password.encode ('utf-8'))
  decrypted_password = decrypted_bytes.decode('utf-8')
  return decrypted_password

