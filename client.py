import requests
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.fernet import Fernet
import hashlib
import base64
import json
from datetime import datetime, timezone
import click
import sys


def base_dir():
    if getattr(sys, 'frozen', False):
        return os.getcwd()
    return os.path.dirname(os.path.abspath(__file__))


def get_config(key):
    config_path = os.path.join(base_dir(), "config.json")

    if not os.path.exists(config_path):
        raise FileNotFoundError("config.json not found in the current directory")

    with open(config_path, "r") as file:
        config = json.load(file)

    if key not in config:
        raise KeyError(f"{key} not found in config.json")

    return config[key]

server_ip = get_config("server_ip")

upload_endpoint = f"{server_ip}/upload"
download_file_endpoint = f"{server_ip}/download_file"
download_key_endpoint = f"{server_ip}/download_key"
login_endpoint = f"{server_ip}/auth/login"
register_endpoint = f"{server_ip}/auth/register"


# Main Group
@click.group()
def cli():
    pass

@cli.command()
@click.argument("username")
@click.argument("password")
def login(username, password):
    r = requests.post(
        login_endpoint,
        json={
            "username": username,
            "password": password
        }
    )

    if r.status_code != 200:
        raise Exception("[-] Login failed")

    click.echo("[+] Login Successful")
    AUTH_TOKEN = r.json()["access_token"]
    
    # Store the auth token
    config_path = os.path.join(base_dir(), "config.json")

    if not os.path.exists(config_path):
        raise FileNotFoundError("config.json not found in the current directory")
    
    with open(config_path, "r") as file:
        config = json.load(file)
    if "auth_token" not in config:
        print("[-] AUTH TOKEN not found")
        return
    config["auth_token"] = AUTH_TOKEN
    with open(config_path, "w") as file:
        json.dump(config, file, indent=4)


@cli.command()
@click.argument("username")
@click.argument("password")
def register(username, password):
    r = requests.post(
        register_endpoint,
        json={
            "username": username,
            "password": password
        }
    )

    if r.status_code != 200:
        raise Exception("[-] Registration failed")

    print("[+] User registered successfully")


def auth_headers():

    AUTH_TOKEN = get_config("auth_token")
    if not AUTH_TOKEN:
        raise Exception("Not logged in")
    return {
        "Authorization": f"Bearer {AUTH_TOKEN}"
    }


def encrypt(file, duplicate = False, new_file_name = None):
    file_key = os.urandom(32)
    nonce = os.urandom(12)

    encryptor = Cipher(
        algorithms.AES(file_key),
        modes.GCM(nonce)
    ).encryptor()
    output_file = file + ".enc"
    '''
    # If duplicate exists, then a numbered file name will be created
    if not duplicate:
        output_file = file + ".enc"
    else:
        output_file = new_file_name + ".enc"
    '''
    with open(file, "rb") as f_in, open(output_file, "wb") as f_out:
        
        while chunk := f_in.read(64 * 1024):
            f_out.write(encryptor.update(chunk))
        encryptor.finalize()
        f_out.write(nonce + encryptor.tag)

    return file_key, output_file

# Function to create a numbered file name if the file already exists on the server
def newfilename(curr):
    name, ext = os.path.splitext(curr)
    name_list = name.split("-")
    
    try:
        new_num = int(name_list[-1]) + 1
        new_name = name[:len(name) - len(name_list[-1])]
        return f"{new_name}{new_num}{ext}"
    except:
        return f"{name}-1{ext}"

# Get the hash value of the file
def get_file_hash(file):
    with open(file, "rb") as f:
        digest = hashlib.file_digest(f, "sha256")
        file_hash = digest.hexdigest()
    return file_hash

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

@cli.command()
@click.argument("file_path")
def upload(file_path):
    # Load the json file containing all the file name to uuid and file hash mappings
    uploaded_files_path = os.path.join(base_dir(), "uploaded_files.json")

    if not os.path.exists(uploaded_files_path):
        raise FileNotFoundError("uploaded_files.json not found in the current directory")
    
    with open(uploaded_files_path, "r") as file:
        uploaded_files = json.load(file)

    # Get the file hash
    file_hash = get_file_hash(file_path)

    filename = os.path.basename(file_path)
    # 
    if filename in uploaded_files and uploaded_files[filename]["hash"] == file_hash:
        print(f"[-] File: {filename} already exists")
        return

    try: 
        # ask the user for passphrase
        passphrase = input("Enter your passphrase: ")
        master_key = base64.urlsafe_b64encode(hashlib.sha256(passphrase.encode("utf-8")).digest())

        file_key, encrypted_file_path = encrypt(file_path)

        cipher_suite = Fernet(master_key)
        encrypted_file_key = cipher_suite.encrypt(file_key).decode("utf-8")
        
        with open(encrypted_file_path, "rb") as f:
            files = {
                "file": (filename, f)
            }
            data = {
                "encrypted_file_key": encrypted_file_key
            }
            
            r = requests.post(
                upload_endpoint,
                files=files,
                data=data,
                headers=auth_headers()
            )
            
        if r.status_code != 200:
            print(f"[-] Error: {r.status_code}")
            return

        # Remove the .enc file created after it is sent to the server
        os.remove(f"{file_path}.enc")

        print(f"[+] File: {filename} successfully uploaded")

        # Add the newly uploaded file's mapping and store it
        file_uuid_mapping = {filename:
                                { 
                                    "uuid": r.text[1:-1],
                                    "hash": file_hash,
                                    "uploaded_at": datetime.now(timezone.utc).isoformat()
                                }
                            }
        uploaded_files.update(file_uuid_mapping)

        with open(uploaded_files_path,"w") as file:
            json.dump(uploaded_files, file, indent=4)
    except Exception as e:
        print(f"[-] Error: {e}")


@cli.command()
@click.argument("file_name")
def download(file_name):
    download_path = get_config("download_path")
    try:
        uploaded_files_path = os.path.join(base_dir(), "uploaded_files.json")

        if not os.path.exists(uploaded_files_path):
            raise FileNotFoundError("uploaded_files.json not found in the current directory")
    
        with open(uploaded_files_path, "r") as file:
            uploaded_files = json.load(file)

        file_id = uploaded_files[file_name]["uuid"]

        try:

            # Ask the user for the passphrase
            passphrase = input("Enter you passphrase: ")
            master_key = base64.urlsafe_b64encode(hashlib.sha256(passphrase.encode("utf-8")).digest())

            # Retrieve the encrypted file key
            r = requests.get(f"{download_key_endpoint}/{file_id}", 
                             headers=auth_headers())
            encrypted_file_key = r.text[1:-1]

            # Decrypt the encrypted file key
            cipher_suite = Fernet(master_key)
            decrypted_file_key = cipher_suite.decrypt(encrypted_file_key)

            # Retrieve the encrypted file
            response = requests.get(f"{download_file_endpoint}/{file_id}",
                                     stream=True,
                                     headers=auth_headers())
            with open(f"{download_path}/{file_name}", "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    f.write(chunk)
            # print(response.status_code)

            # Decrypt the encrypted file
            decrypt(f"{download_path}/{file_name}", decrypted_file_key)
            print(f"[+] Successfully downloaded file: {file_name}")
        except:
            print("[-] Error decrypting file")
            return

    except Exception as e:
        print(f"[-] Error: {e}")

def main():
    cli()

if __name__ == '__main__':
    main()



    





    


