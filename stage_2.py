"""Stage_2"""

""" Todo- """
# WIll create a MASTER password using HASHING
# Will add salting method 
# Also Fix my messy code
import os
import json
import hashlib
import getpass
import base64

def hash_Value(value: str) -> str:
  return hashlib.sha256(value.encode()).hexdigest()

# Path to store master password and salts (file lives next to this module)
BASE_DIR = os.path.dirname(__file__)
MASTER_FILE = os.path.join(BASE_DIR, "Password_Manager1", "master_password.json")

# Ensure master file exists and contains persistent salts and a users dict.
def _load_or_init_master_file():
  try:
    with open(MASTER_FILE, "r") as f:
      data = json.load(f)
      # ensure required keys
      if not isinstance(data, dict) or "hash_salt" not in data or "kdf_salt" not in data or "users" not in data:
        raise ValueError("master file missing required keys")
      return data
  except (FileNotFoundError, json.JSONDecodeError, ValueError):
    # create fresh file
    hash_salt = os.urandom(16).hex()
    kdf_salt = base64.b64encode(os.urandom(16)).decode()
    data = {
      "hash_salt": hash_salt,
      "kdf_salt": kdf_salt,
      "users": {}
    }
    os.makedirs(os.path.dirname(MASTER_FILE), exist_ok=True)
    with open(MASTER_FILE, "w") as f:
      json.dump(data, f, indent=2)
    return data

# Load or initialize at module import so salts are stable across runs
_MASTER_DATA = _load_or_init_master_file()
HASH_SALT = _MASTER_DATA["hash_salt"]
KDF_SALT = base64.b64decode(_MASTER_DATA["kdf_salt"])  # bytes used by KDF


def Master_Pass():
  print("LOGIN!!")

  # Load latest data (in case Master_Pass created user previously)
  try:
    with open(MASTER_FILE, "r") as m_pass:
      data = json.load(m_pass)
  except Exception as e:
    print("Error reading master file:", e)
    return False

  users = data.get("users", {})

  # If no user exists, offer to create one
  if not users:
    print("No master user found. Let's create one.")
    username = input("Choose a username: ")
    while True:
      pw1 = getpass.getpass(prompt="Choose Master Password: ")
      pw2 = getpass.getpass(prompt="Confirm Master Password: ")
      if pw1 != pw2:
        print("Passwords do not match — try again.")
        continue
      if len(pw1) < 6:
        print("Password too short — use at least 6 characters.")
        continue
      break

    key = hash_Value(username + HASH_SALT)
    val = hash_Value(HASH_SALT + pw1)
    data["users"][key] = val
    with open(MASTER_FILE, "w") as f:
      json.dump(data, f, indent=2)
    print("Master user created — please login now.")

  # Prompt for login
  while True:
    Master = input("Enter Username: ")
    in_put = getpass.getpass(prompt="Enter Master Password: ")

    hashed2 = hash_Value(Master + HASH_SALT)
    hashed = hash_Value(HASH_SALT + in_put)

    if hashed2 in data.get("users", {}) and data["users"][hashed2] == hashed:
      print("✅ Password Verified!!")
      return in_put
    else:
      print("❌ Incorrect credentials!!")
      wanna_try_again = input("wanna try again? (y/n): ")
      if wanna_try_again != "y":
        return False
