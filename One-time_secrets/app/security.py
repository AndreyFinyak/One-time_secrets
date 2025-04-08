from cryptography.fernet import Fernet
import os

FERNET_KEY = os.getenv("FERNET_KEY", Fernet.generate_key())  
fernet = Fernet(FERNET_KEY)

def encrypt_secret(secret: str) -> str:
    return fernet.encrypt(secret.encode()).decode()

def decrypt_secret(encrypted_secret: str) -> str:
    return fernet.decrypt(encrypted_secret.encode()).decode()
