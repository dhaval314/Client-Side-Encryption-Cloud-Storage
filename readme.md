# Client-Side Encrypted Cloud Storage System

A zero-knowledge cloud storage system where **all encryption happens on the client**.  
The server never sees plaintext data or encryption keys, ensuring strong confidentiality even in the event of server compromise.

---

## Overview

This project implements a secure file storage and transfer system based on **client-side encryption** principles.  
Files are encrypted locally before upload, and only encrypted blobs are ever stored or transmitted.

Key design goals:
- Zero-knowledge server
- Strong cryptographic isolation
- Simple, auditable architecture
- Practical performance for medium-sized files

---

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

---


## Tech Stack

**Client**
- Python
- `cryptography` (Fernet symmetric encryption)

**Server**
- Python
- FastAPI
- RESTful APIs

**Other**
- UUID-based file isolation
- Streaming downloads

---

## Upload Flow

1. Client generates a random data key
2. File is encrypted locally using the data key
3. Data key is encrypted using a master key
4. Encrypted file and encrypted key are uploaded
5. Server stores both without decryption

---

## Download Flow

1. Client requests encrypted file and encrypted key
2. Server streams encrypted data
3. Client decrypts the data key locally
4. Client decrypts the file locally

---

## Limitations

- No key recovery if the client loses its master key
- Not optimized for very large files
- No deduplication due to encryption randomness




