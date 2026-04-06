"""
api.py — PyWebView JS↔Python bridge
All methods return dicts so JS can handle success/error uniformly.
"""

import os
import json
import base64
from cryptography.fernet import Fernet

import stage_2
import stage_3
import Stage_1                          # import module, not names — fixes memory bug

import pyperclip
import threading
import time
MASTER_FILE = stage_2.MASTER_FILE

_session_key: bytes | None = None


def _ok(data=None):
    return {"success": True, "data": data}

def _err(msg: str):
    return {"success": False, "error": msg}


class Api:

    def check_has_user(self):
        try:
            with open(MASTER_FILE, "r") as f:
                has = bool(json.load(f).get("users"))
            return _ok(has)
        except Exception:
            return _ok(False)

    def register(self, username: str, password: str, confirm: str):
        if not username.strip():
            return _err("Username cannot be empty")
        if not password:
            return _err("Password cannot be empty")
        if password != confirm:
            return _err("Passwords do not match")
        if len(password) < 6:
            return _err("Minimum 6 characters required")
        try:
            data = stage_2._load_or_init_master_file()
            salt = stage_2.HASH_SALT
            k = stage_2.hash_Value(username.strip() + salt)
            v = stage_2.hash_Value(salt + password)
            if k in data["users"]:
                return _err("Username already exists")
            data["users"][k] = v
            os.makedirs(os.path.dirname(MASTER_FILE), exist_ok=True)
            with open(MASTER_FILE, "w") as f:
                json.dump(data, f, indent=2)
            return self.login(username, password)
        except Exception as e:
            return _err(str(e))

    def login(self, username: str, password: str):
        global _session_key
        if not username.strip() or not password:
            return _err("Username and password required")
        try:
            with open(MASTER_FILE, "r") as f:
                data = json.load(f)
            salt = data.get("hash_salt", "")
            hu = stage_2.hash_Value(username.strip() + salt)
            hp = stage_2.hash_Value(salt + password)
            if hu in data.get("users", {}) and data["users"][hu] == hp:
                kdf_salt = base64.b64decode(data["kdf_salt"])
                _session_key = stage_3.encryption(password, kdf_salt)
                Stage_1.load_passwords()
                return _ok("granted")
            else:
                return _err("Invalid credentials")
        except FileNotFoundError:
            return _err("No vault found — register first")
        except Exception as e:
            return _err(str(e))

    def logout(self):
        global _session_key
        _session_key = None
        return _ok()

    def get_passwords(self):
        if _session_key is None:
            return _err("Not authenticated")
        try:
            entries = []
            for site, value in Stage_1.pass_dic.items():
                try:
                    if isinstance(value, dict):
                        enc      = value.get("password", "")
                        username = value.get("username", "")
                        url      = value.get("url", "")
                    else:
                        enc      = value
                        username = ""
                        url      = ""
                    plain = stage_3.decryption(enc, _session_key)
                except Exception:
                    plain    = "⚠ decrypt error"
                    username = ""
                    url      = ""
                entries.append({"site": site, "password": plain, "username": username, "url": url})
            return _ok(entries)
        except Exception as e:
            return _err(str(e))

    def add_password(self, site: str, password: str, username: str = "", url:str = ""):
        if _session_key is None:
            return _err("Not authenticated")
        if not site.strip():
            return _err("Website cannot be empty")
        is_valid, feedback = Stage_1.validation_pass(password)
        if not is_valid:
            return _err(feedback)
        try:
            f   = Fernet(_session_key)
            enc = f.encrypt(password.encode("utf-8")).decode("utf-8")
            entry = {"password": enc}
            if username.strip():
                entry["username"] = username.strip()
            if url.strip():
                entry["url"] =  url.strip()
            Stage_1.pass_dic[site.strip()] = entry
            with open(Stage_1.pass_file, "w") as fp:
                json.dump(Stage_1.pass_dic, fp, indent=4)
            return _ok({"site": site.strip(), "password": password, "username": username.strip()})
        except Exception as e:
            return _err(str(e))

    def delete_password(self, site: str):
        if _session_key is None:
            return _err("Not authenticated")
        if site not in Stage_1.pass_dic:
            return _err("Entry not found")
        try:
            Stage_1.pass_dic.pop(site)
            with open(Stage_1.pass_file, "w") as fp:
                json.dump(Stage_1.pass_dic, fp, indent=4)
            return _ok()
        except Exception as e:
            return _err(str(e))

    def verify_master(self, password: str):
        """Verify master password before allowing edit. Doesn't change session."""
        try:
            with open(MASTER_FILE, "r") as f:
                data = json.load(f)
            salt = data.get("hash_salt", "")
            hp = stage_2.hash_Value(salt + password)
            # Check if this password matches any user's stored hash
            if hp in data.get("users", {}).values():
                return _ok()
            return _err("Incorrect master password")
        except Exception as e:
            return _err(str(e))

    def update_password(self, site: str, password: str, username: str = ""):
        if _session_key is None:
            return _err("Not authenticated")
        if site not in Stage_1.pass_dic:
            return _err("Entry not found")
        is_valid, feedback = Stage_1.validation_pass(password)
        if not is_valid:
            return _err(feedback)
        try:
            f   = Fernet(_session_key)
            enc = f.encrypt(password.encode("utf-8")).decode("utf-8")
            entry = {"password": enc}
            if username.strip():
                entry["username"] = username.strip()
            # Preserve existing URL if present
            old_entry = Stage_1.pass_dic.get(site, {})
            if isinstance(old_entry, dict) and old_entry.get("url"):
                entry["url"] = old_entry["url"]
            Stage_1.pass_dic[site] = entry
            with open(Stage_1.pass_file, "w") as fp:
                json.dump(Stage_1.pass_dic, fp, indent=4)
            return _ok({"site": site, "password": password, "username": username.strip()})
        except Exception as e:
            return _err(str(e))

    def validate_password(self, password: str):
        is_valid, feedback = Stage_1.validation_pass(password)
        return _ok({"valid": is_valid, "feedback": feedback})


    def auto_login(self, site: str):
        if _session_key is None:
            return _err("Not authenticated")

        entry = Stage_1.pass_dic.get(site)
        if not entry:   
            return _err("Entry not found")

        # Support both old string format and new dict format
        if isinstance(entry, dict):
            enc_pw   = entry.get("password", "")
            username = entry.get("username", "")
            url      = entry.get("url", "")
        else:
            return _err("No URL stored — re-add this entry with a URL")

        print(f"[AUTO_LOGIN] Site: {site}, URL: '{url}', Username: {username}")
        
        if not url:
            return _err("No URL stored for this site — edit the entry and add a URL")

        try:
            password = stage_3.decryption(enc_pw, _session_key)
        except Exception as e:
            return _err(f"Decryption failed: {e}")

        # Run in background thread so UI doesn't freeze
        import threading
        import auto_login as auto_login_module
        threading.Thread(
            target=auto_login_module.auto_login_brave,
            args=(url, username, password),
            daemon=True
        ).start()

        return _ok(f"Launching browser for {site}...")

    def copy_password(self,site:str):
        if _session_key is None:
            return _err("Not Authenticated")

        entry = Stage_1.pass_dic.get(site)
        if not entry:
            return _err("Entry not found")

        if isinstance(entry, dict):
            enc = entry.get("password","")
        else:
            enc= entry

        try: 
            password = stage_3.decryption(enc, _session_key)
        except Exception as e:
            return _err(f"Decryption Failed:{e} ")

        # copy to clipboard
        pyperclip.copy(password)

        def _destruct():
            time.sleep(10)
            if pyperclip.paste() == password:
                pyperclip.copy("")

        threading.Thread(target=_destruct, daemon=True).start()

        return _ok("Copied!")