import os
import io
import time
import pickle
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from pydrive2.files import GoogleDriveFile
from google.colab import userdata
from config import RECEIVED_FOLDER, YOUTUBE_FOLDER, SENT_FOLDER

TOKEN_SECRET_NAME = 'PYDRIVE_TOKEN'

def _save_token_to_secret(gauth: GoogleAuth):
    """ذخیره توکن pydrive2 در Colab Secrets"""
    try:
        token_bytes = pickle.dumps(gauth.credentials)
        userdata.set(TOKEN_SECRET_NAME, token_bytes.hex())
        print("✅ توکن در Secrets ذخیره شد.")
    except Exception as e:
        print(f"⚠️ نتوانست توکن را ذخیره کند: {e}")

def _load_token_from_secret(gauth: GoogleAuth):
    """بارگذاری توکن از Colab Secrets و اعمال آن به gauth"""
    try:
        token_hex = userdata.get(TOKEN_SECRET_NAME)
        if token_hex:
            creds = pickle.loads(bytes.fromhex(token_hex))
            gauth.credentials = creds
            return True
    except:
        pass
    return False

def authenticate_google_drive():
    gauth = GoogleAuth()
    
    if _load_token_from_secret(gauth):
        
        if gauth.access_token_expired:
            gauth.Refresh()
            _save_token_to_secret(gauth)
        gauth.Authorize()
        print("✅ احراز هویت با توکن ذخیره‌شده موفق بود.")
        return GoogleDrive(gauth)

    gauth.CommandLineAuth()  
    
    _save_token_to_secret(gauth)
    gauth.Authorize()
    return GoogleDrive(gauth)

def get_or_create_folder(drive: GoogleDrive, folder_path: str, parent_id: str = "root") -> str:
    parts = folder_path.split("/")
    current_parent = parent_id
    for part in parts:
        if not part:
            continue
        query = f"title='{part}' and mimeType='application/vnd.google-apps.folder' and '{current_parent}' in parents and trashed=false"
        file_list = drive.ListFile({'q': query}).GetList()
        if file_list:
            current_parent = file_list[0]['id']
        else:
            folder_metadata = {
                'title': part,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [{'id': current_parent}]
            }
            folder = drive.CreateFile(folder_metadata)
            folder.Upload()
            current_parent = folder['id']
            print(f"📁 پوشه '{part}' ساخته شد (ID: {current_parent})")
    return current_parent

def upload_file(drive: GoogleDrive, local_file_path: str, parent_folder_id: str) -> GoogleDriveFile:
    if not os.path.exists(local_file_path):
        raise FileNotFoundError(f"فایل محلی یافت نشد: {local_file_path}")
    file_name = os.path.basename(local_file_path)
    file = drive.CreateFile({'title': file_name, 'parents': [{'id': parent_folder_id}]})
    file.SetContentFile(local_file_path)
    file.Upload()
    print(f"✅ آپلود شد: {file_name} (ID: {file['id']})")
    return file

def upload_file_from_memory(drive: GoogleDrive, file_bytes: bytes, file_name: str, parent_folder_id: str) -> GoogleDriveFile:
    file = drive.CreateFile({'title': file_name, 'parents': [{'id': parent_folder_id}]})
    file.content = io.BytesIO(file_bytes)
    file.Upload()
    print(f"✅ آپلود شد: {file_name} (ID: {file['id']})")
    return file

def download_file(drive: GoogleDrive, file_id: str, output_path: str) -> str:
    file = drive.CreateFile({'id': file_id})
    file.FetchMetadata()
    file.GetContentFile(output_path)
    print(f"⬇️ دانلود شد: {file['title']} -> {output_path}")
    return output_path

def list_files_in_folder(drive: GoogleDrive, folder_id: str) -> list:
    query = f"'{folder_id}' in parents and trashed=false and mimeType!='application/vnd.google-apps.folder'"
    file_list = drive.ListFile({'q': query}).GetList()
    files = []
    for f in file_list:
        files.append({
            'id': f['id'],
            'title': f['title'],
            'size': f.get('fileSize', '0'),
            'created': f.get('createdDate', ''),
            'mime': f.get('mimeType', '')
        })
    return files

def get_file_metadata(drive: GoogleDrive, file_id: str) -> dict:
    file = drive.CreateFile({'id': file_id})
    file.FetchMetadata()
    return file

def get_last_sent_check_time():
    try:
        with open("last_sent_check.txt", "r") as f:
            return float(f.read().strip())
    except:
        return 0.0

def set_last_sent_check_time(timestamp):
    with open("last_sent_check.txt", "w") as f:
        f.write(str(timestamp))

def check_new_files_in_sent(drive: GoogleDrive) -> list:
    folder_id = get_or_create_folder(drive, SENT_FOLDER)
    all_files = list_files_in_folder(drive, folder_id)
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
