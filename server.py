from fastapi import FastAPI
from fastapi import UploadFile, File
import aiofiles

app = FastAPI()

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    file_path = "/home/dhaval/storage/"
    
    async with aiofiles.open(f"{file_path}/{file.filename}", mode= "wb") as f:
        while content := await file.read(1024):
            await f.write(content)
    return {
        "filename":file.filename,
        "file_size":file.size
    }



@app.get("/download")
async def download():
    return {"message":"download page"}