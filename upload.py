import os
import pickle
from datetime import datetime, timedelta
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# === Cấu hình ===
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRET_FILE = "client_secret_400767361173-a5ufvf180lcmkcfi3rjnk6tjmaql9opr.apps.googleusercontent.com.json"
VIDEO_DIR = "source_pool"  # Thư mục chứa video
CATEGORY_ID = "15"  # Animals

# === Xác thực Google ===
def get_authenticated_service():
    credentials = None
    if os.path.exists("token.pkl"):
        with open("token.pkl", "rb") as f:
            credentials = pickle.load(f)
    if not credentials or not credentials.valid:
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
        credentials = flow.run_local_server(port=0)
        with open("token.pkl", "wb") as f:
            pickle.dump(credentials, f)
    return build("youtube", "v3", credentials=credentials)

# === Upload video ===
def upload_video(youtube, file_path, title, description, tags, schedule_time):
    request_body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": CATEGORY_ID
        },
        "status": {
            "privacyStatus": "private",
            "publishAt": schedule_time.isoformat("T") + "Z",
            "selfDeclaredMadeForKids": False
        }
    }

    media = MediaFileUpload(file_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=request_body, media_body=media)

    print(f"[Info] Uploading: {title}")
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"[Info] Upload progress: {int(status.progress() * 100)}%")
    print(f"[Success] Uploaded: https://youtu.be/{response['id']}")
    return response['id']

# === Tạo metadata từ tên file ===
def generate_metadata(file_name):
    base = os.path.splitext(file_name)[0]
    title = base.replace("_", " ").title()
    description = f"Tự động upload: {title}"
    tags = ["auto", "upload", "tool"]
    return title, description, tags

# === Quét thư mục & upload ===
def scan_and_upload():
    youtube = get_authenticated_service()
    files = [f for f in os.listdir(VIDEO_DIR) if f.lower().endswith(('.mp4', '.mov', '.avi'))]
    print(f"[Info] Found {len(files)} videos.")

    for file in files:
        path = os.path.join(VIDEO_DIR, file)
        title, description, tags = generate_metadata(file)
        schedule_time = datetime.utcnow() + timedelta(days=1)
        try:
            upload_video(youtube, path, title, description, tags, schedule_time)
        except Exception as e:
            print(f"[Error] Failed to upload {file}: {e}")

if __name__ == "__main__":
    scan_and_upload()
