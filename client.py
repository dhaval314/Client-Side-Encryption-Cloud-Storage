import requests
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


file_path = "/home/dhaval/Desktop/testfile.txt"
upload_endpoint = "http://localhost:8000/upload"
download_endpoint = "http://localhost:8000/download"
download_path = "/home/dhaval/Downloads"

def encrypt(file): # user_id is used as AAD (Additional Authenticated Data)
    key = os.urandom(32)
    nonce = os.urandom(12)
    encryptor = Cipher(algorithms.AES(key), modes.GCM(nonce)).encryptor()
    
    output_file = file_path + ".enc"
    with open(file, "rb") as f_in, open(output_file, "wb") as f_out:
        while chunk := f_in.read(64 * 1024):
            f_out.write(encryptor.update(chunk))
        encryptor.finalize()
        meta_data = nonce + encryptor.tag
        f_out.write(meta_data)
    print(key)

    return key

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

    key = encrypt(file_path)

    with open(f"{file_path}.enc", "rb") as f:
        files = {
            "file": (file_path.split("/")[-1], f)
        }
        r = requests.post(upload_endpoint + "/" + str(user_id), files=files)

    print(r.status_code)
    print(r.text)

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
    
    


