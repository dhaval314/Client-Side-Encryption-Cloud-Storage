# Client-Side Encrypted Cloud Storage System

A zero-knowledge cloud storage system where **all encryption happens on the client**.  
The server never sees plaintext data or encryption keys, ensuring strong confidentiality even in the event of server compromise.


## Overview

This project implements a secure file storage and transfer system based on **client-side encryption** principles.  
Files are encrypted locally before upload, and only encrypted blobs are ever stored or transmitted.

Key design goals:
- Zero-knowledge server
- Strong cryptographic isolation
- Simple, auditable architecture
- Practical performance for medium-sized files



## Security Model

### Client-Side Encryption
All cryptographic operations occur on the client:
- File encryption
- Key generation
- Decryption during download

The backend acts only as a storage and relay layer.

### Key Decoupling
- Each file is encrypted with a **unique symmetric data key**
- Data keys are encrypted using a **user-derived master key**
- Encrypted data keys and encrypted files are stored separately

This design:
- Limits the impact of key compromise
- Enables efficient key rotation
- Prevents server-side key misuse




## Tech Stack

**Client**
- Python
- `cryptography` (Fernet symmetric encryption)

**Server**
- Python
- FastAPI
- RESTful APIs
- sqlite3

**Other**
- UUID-based file isolation
- Streaming downloads


## Upload Flow

1. Client generates a random data key
2. File is encrypted locally using the data key
3. Data key is encrypted using a master key
4. Encrypted file and encrypted key are uploaded
5. Server stores both without decryption



## Download Flow

1. Client requests encrypted file and encrypted key
2. Server streams encrypted data
3. Client decrypts the data key locally
4. Client decrypts the file locally

## Server Structure
```
.
├── app
|   ├── .env # To store secret key which signs the auth tokens
│   ├── app.db # To store users
│   ├── server.py
│   └── venv/
└── storage 
    └── <uuid1>/ # A directory containing all files of user1
    └── <uuid2>/
        └── <file_uuid> # A directory with encrypted file and encrypted file key
```

## Command Line Interface

All interactions with the client are performed through `client.py`.

 

### Help

```
python client.py --help
```

Displays all available commands and options.

### Register

```
python client.py register <username> <password>
```

### Login

```
python client.py login <username> <password>
```

Authenticates the user with the server and retrieves an access token. The token is stored locally in the `config.json` file and automatically included in future requests.

 

### Upload File

```
python client.py upload <file_path>
```

Uploads a file securely to the server. If the same file name and hash already exist locally, the upload is skipped.

 

### Download File

```
python client.py download <file_name>
```

Downloads the file by looking up the file name mapped UUID in the `uploaded_file.json` file. Download path is set using `config.json`



