from fastapi import FastAPI

app = FastAPI()

@app.get("/upload")
async def upload():
    return {"message":"upload page"}


@app.get("/download")
async def download():
    return {"message":"download page"}