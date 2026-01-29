from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import StreamingResponse
import aiofiles
import aiofiles.os
import os
import getpass
import uuid

app = FastAPI()

username = getpass.getuser()
storage_path = "/home/dhaval/storage"

    

@app.post("/upload/{user_id}")
async def upload(user_id, encrypted_file_key: str = Form(...), file: UploadFile = File(...)):
    file_uuid = uuid.uuid4()

    os.makedirs(f"{storage_path}/{user_id}/{file_uuid}", exist_ok=True)

    file_name = file.filename

    async with aiofiles.open(f"{storage_path}/{user_id}/{file_uuid}/{file_name}", mode= "wb") as f:
        while content := await file.read(1024):
            await f.write(content)
    
    with open(f"{storage_path}/{user_id}/{file_uuid}/key.txt", "w") as key_file:
        key_file.write(encrypted_file_key)

    return {
        "file_uuid": file_uuid
    }



@app.get("/download/{user_id}/{file_id}")
async def download(user_id, file_id):

    def file_iterator():
        with open(f"{storage_path}/{user_id}/{file_id}", "rb") as file:
            while chunk := file.read(1024):
                yield chunk
    
    return StreamingResponse(
        file_iterator()
    )
        