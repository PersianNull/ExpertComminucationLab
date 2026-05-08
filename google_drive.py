import os
import io
import time
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload, MediaInMemoryUpload
from google.auth import default as google_auth_default
from google.colab import auth
from config import RECEIVED_FOLDER, YOUTUBE_FOLDER, SENT_FOLDER

def _build_drive_service():
    auth.authenticate_user()
    creds, _ = google_auth_default()
    return build('drive', 'v3', credentials=creds)

def authenticate_google_drive():
    return _build_drive_service()

def get_or_create_folder(service, folder_path: str, parent_id: str = "root") -> str:
    parts = folder_path.split("/")
    current_parent = parent_id
    for part in parts:
        if not part:
            continue
        query = f"name='{part}' and mimeType='application/vnd.google-apps.folder' and '{current_parent}' in parents and trashed=false"
        response = service.files().list(q=query, fields="files(id, name)").execute()
        folders = response.get('files', [])
        if folders:
            current_parent = folders[0]['id']
        else:
            folder_metadata = {
                'name': part,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [current_parent]
            }
            folder = service.files().create(body=folder_metadata, fields='id').execute()
            current_parent = folder['id']
            print(f"📁 پوشه '{part}' ساخته شد (ID: {current_parent})")
    return current_parent

def upload_file(service, local_file_path: str, parent_folder_id: str) -> dict:
    if not os.path.exists(local_file_path):
        raise FileNotFoundError(f"فایل محلی یافت نشد: {local_file_path}")
    file_name = os.path.basename(local_file_path)
    media = MediaFileUpload(local_file_path, resumable=True)
    file_metadata = {'name': file_name, 'parents': [parent_folder_id]}
    uploaded = service.files().create(body=file_metadata, media_body=media, fields='id,name').execute()
    print(f"✅ آپلود شد: {file_name} (ID: {uploaded['id']})")
    return uploaded

def upload_file_from_memory(service, file_bytes: bytes, file_name: str, parent_folder_id: str) -> dict:
    media = MediaInMemoryUpload(file_bytes, resumable=True)
    file_metadata = {'name': file_name, 'parents': [parent_folder_id]}
    uploaded = service.files().create(body=file_metadata, media_body=media, fields='id,name').execute()
    print(f"✅ آپلود شد: {file_name} (ID: {uploaded['id']})")
    return uploaded

def download_file(service, file_id: str, output_path: str) -> str:
    request = service.files().get_media(fileId=file_id)
    with io.FileIO(output_path, 'wb') as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
    print(f"⬇️ دانلود شد: {output_path}")
    return output_path

def list_files_in_folder(service, folder_id: str) -> list:
    query = f"'{folder_id}' in parents and trashed=false and mimeType!='application/vnd.google-apps.folder'"
    results = service.files().list(q=query, fields="files(id, name, size, createdTime, mimeType)").execute()
    files = []
    for f in results.get('files', []):
        files.append({
            'id': f['id'],
            'title': f['name'],
            'size': f.get('size', '0'),
            'created': f.get('createdTime', ''),
            'mime': f.get('mimeType', '')
        })
    return files

def get_file_metadata(service, file_id: str) -> dict:
    return service.files().get(fileId=file_id, fields='id,name,size,createdTime,mimeType').execute()

def get_last_sent_check_time():
    try:
        with open("last_sent_check.txt", "r") as f:
            return float(f.read().strip())
    except:
        return 0.0

def set_last_sent_check_time(timestamp):
    with open("last_sent_check.txt", "w") as f:
        f.write(str(timestamp))

def check_new_files_in_sent(service) -> list:
    folder_id = get_or_create_folder(service, SENT_FOLDER)
    all_files = list_files_in_folder(service, folder_id)
    last_check = get_last_sent_check_time()
    current_time = time.time()
    new_files = []
    for f in all_files:
        date_str = f.get('created', '')
        if date_str:
            try:
                file_ts = time.mktime(time.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ"))
            except:
                file_ts = 0
        else:
            file_ts = 0
        if file_ts > last_check:
            new_files.append(f)
    set_last_sent_check_time(current_time)
    return new_files