import requests

file_path = "/home/rituparnpant/Downloads/discord-0.0.122.deb"
upload_endpoint = "http://10.80.231.252:8000/upload"
download_endpoint = "http://10.80.231.252:8000/download"
download_path = "/home/rituparnpant/Downloads/"


def upload(user_id):
    with open(f"{file_path}", "rb") as f:
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
        
    except Exception as e:
        print(f"Error: {e}")
    
    

download(1, "test", download_path)
