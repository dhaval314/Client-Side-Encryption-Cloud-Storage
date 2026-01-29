import requests
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.fernet import Fernet
import hashlib
import base64


file_path = "/home/dhaval/Desktop/test"
upload_endpoint = "http://localhost:8000/upload"
download_endpoint = "http://localhost:8000/download"
download_path = "/home/dhaval/Downloads"
passphrase = "abcd"
master_key = base64.urlsafe_b64encode(hashlib.sha256(passphrase.encode("utf-8")).digest())


def encrypt(file):
    file_key = os.urandom(32)
    nonce = os.urandom(12)

    encryptor = Cipher(
        algorithms.AES(file_key),
        modes.GCM(nonce)
    ).encryptor()

    output_file = file + ".enc"

    with open(file, "rb") as f_in, open(output_file, "wb") as f_out:
        while chunk := f_in.read(64 * 1024):
            f_out.write(encryptor.update(chunk))
        encryptor.finalize()
        f_out.write(nonce + encryptor.tag)

    return file_key, output_file


def decrypt(encrypted_file, key):
    file_size = os.path.getsize(encrypted_file)
    ciphertext_size = file_size - 28 

    with open(encrypted_file, "rb") as f_in:
        
        ciphertext = f_in.read(ciphertext_size)
        
        nonce = f_in.read(12)
        tag = f_in.read(16)
    
    decryptor = Cipher(
        algorithms.AES(key), 
        modes.GCM(nonce, tag)
    ).decryptor()
    try:
        
        decrypted_data = decryptor.update(ciphertext) + decryptor.finalize()
        
        output_path = encrypted_file.replace(".enc", ".dec")
        with open(output_path, "wb") as f_out:
            f_out.write(decrypted_data)
            
        return output_path
    except Exception as e:
        
        raise ValueError("Decryption failed: Data tampered with or wrong parameters.") from e
    
def upload(user_id):
    file_key, encrypted_file_path = encrypt(file_path)

    cipher_suite = Fernet(master_key)
    encrypted_file_key = cipher_suite.encrypt(file_key).decode("utf-8")

    with open(encrypted_file_path, "rb") as f:
        files = {
            "file": (os.path.basename(encrypted_file_path), f)
        }
        data = {
            "encrypted_file_key": encrypted_file_key
        }

        r = requests.post(
            f"{upload_endpoint}/{user_id}",
            files=files,
            data=data
        )
    print(r.status_code)
    print(r.text)
    


upload(1)

def download(user_id, file_id, download_path):
    try:
        response = requests.get(f"{download_endpoint}/{user_id}/{file_id}", stream=True)
        with open(f"{download_path}/{file_id}", "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                f.write(chunk)
        print(response.status_code)
        print(response.text)
    except Exception as e:
        print(f"Error: {e}")
    
    


