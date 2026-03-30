import os
import string
import json
import hashlib
import getpass
import base64
from pathlib import Path
from cryptography.fernet import Fernet
from base64 import urlsafe_b64encode
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import stage_2
import stage_3

#  Core Structure (No encryption) of your password manager project.

#  to do following task i need to use the funcitons
#  user says add then it should ask the website name 
#  ask for password 
#  can perferom view 
#  save it in a file (JSON)

#
pass_dic = {
  # "wesbite_name" : "password"
}

# Build a path relative to this script so the code works no matter the CWD.
# Using pathlib keeps paths readable and portable.
BASE_DIR = Path(__file__).parent
pass_file = BASE_DIR / "Password_Manager1" / "password.json"
def load_passwords():
  global pass_dic
  try:
    # open() accepts Path objects on modern Python versions
    with open(pass_file, "r") as pass_word:
      pass_dic = json.load(pass_word)
  except FileNotFoundError as e:
    print(e)
    pass_dic = {}
  except json.JSONDecodeError as e:
    # empty or malformed JSON -> start with empty dict
    print("Password file is empty or malformed; starting with empty store.")
    pass_dic = {}

special_symbols = set(string.punctuation) 

def validation_pass(password):
  has_length= len(password) >=8
  has_digit = False
  has_symbol = False
  has_uppercase = False
  has_lowercase = False
  
  for char in password:
    if char.isdigit():
      has_digit = True
    elif char in special_symbols:
      has_symbol = True
    elif char.isupper():
      has_uppercase = True
    elif char.islower():
      has_lowercase = True


# Optional: Exit the loop early if all conditions are met
    if has_digit and has_symbol and has_uppercase and has_lowercase and has_length:
      break

  if has_lowercase and has_digit and has_symbol and has_uppercase and has_length:
    return True, "Password is Valid"
  else:
    Feedback = []
    if not has_digit:
      Feedback.append("Password must contains atleast one digit")
    if not has_length:
      Feedback.append("Password must contains atleast 8 values")
    if not has_symbol:
      Feedback.append("Password must contains atleast one symbol")
    if not has_uppercase:
      Feedback.append("Password must contains atleast one uppercase")
    if not has_lowercase:
      Feedback.append("Password must contains atleast one lowecase")
    return False ,"\n".join(Feedback)

def add(key):
  website = input("Website name: ")
  password = input("Password: ")

  # Call validation once and reuse the result so we don't run the checks twice.
  is_valid, feedback = validation_pass(password)
  if not is_valid:
    print(feedback)
    return

# Encryp the password first
  f = Fernet(key)
  encrypted_password = f.encrypt(password.encode('utf-8'))

# FILE I/O of storing encrypted password in the dict
  pass_dic[website] = encrypted_password.decode('utf-8')

  with open(pass_file, "w") as pass_word:
    json.dump(pass_dic,pass_word,indent=4)
  print("Password SAVED!!")     # SAVED!!

# VIEW
def view(key):
  global pass_dic
  for website, encrypted_pass in pass_dic.items():
    try:
      decrypted_pass = stage_3.decryption(encrypted_pass,key)
      print(f"{website}: {decrypted_pass}")
    except Exception as e:
      print(f"Error decrypting {website} : {e}")



# ----------------------------
# Main runtime block
# Wrap interactive code in this guard so importing this module (for tests
# or a GUI) doesn't start the interactive prompt immediately.
# ----------------------------
if __name__ == "__main__":
  # Authenticate master user (prompts for username/password)
  from Login_page import run_login
  from Vault_page import run_vault
  master_password, key = run_login()
  if not master_password:
    # user cancelled or failed login
    exit()

  # Load stored passwords from disk (safe if file is missing or malformed)
  load_passwords()
  run_vault(key)
