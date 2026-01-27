from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
import aiofiles
import aiofiles.os
import os
import getpass


app = FastAPI()

username = getpass.getuser()
storage_path = "/home/dhaval/storage"
download_path = f"/home/{username}/Downloads"

@app.post("/upload/{user_id}")
async def upload(user_id, file: UploadFile = File(...)):

    try:
        await aiofiles.os.makedirs(f"{storage_path}/{user_id}")
    except:
        print(f"Directory for user: {user_id} already exists")


    async with aiofiles.open(f"{storage_path}/{user_id}/{file.filename}", mode= "wb") as f:
        while content := await file.read(1024):
            await f.write(content)
    return {
        "filename":file.filename,
        "file_size":file.size
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
        