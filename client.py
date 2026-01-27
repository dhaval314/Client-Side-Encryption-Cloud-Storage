import requests

upload_endpoint = "http://localhost:8000/upload"

with open("/home/dhaval/Desktop/test", "rb") as f:
    files = {
        "file": ("test", f)
    }

    r = requests.post(upload_endpoint, files=files)

print(r.status_code)
print(r.text)