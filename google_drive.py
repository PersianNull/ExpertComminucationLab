import os
import io
import time
import pickle
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload, MediaInMemoryUpload
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.colab import userdata
from config import RECEIVED_FOLDER, YOUTUBE_FOLDER, SENT_FOLDER

SCOPES = ['https://www.googleapis.com/auth/drive']
TOKEN_SECRET_NAME = 'GOOGLE_DRIVE_TOKEN'

def _save_token_to_secret(token_bytes):
    try:
        userdata.set(TOKEN_SECRET_NAME, token_bytes.hex())
        print("✅ توکن در Secrets ذخیره شد.")
    except Exception as e:
        print(f"⚠️ نتوانست توکن را ذخیره کند: {e}")

def _load_token_from_secret():
    try:
        token_hex = userdata.get(TOKEN_SECRET_NAME)
        if token_hex:
            return bytes.fromhex(token_hex)
    except:
        pass
    return None

def _get_credentials():
    creds = None
    token_bytes = _load_token_from_secret()
    if token_bytes:
        creds = pickle.loads(token_bytes)
        if creds and creds.valid:
            print("✅ احراز هویت با توکن ذخیره‌شده موفق بود.")
            return creds
        elif creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            _save_token_to_secret(pickle.dumps(creds))
            print("✅ توکن بازیابی شد.")
            return creds

    if not os.path.exists('credentials.json'):
        raise FileNotFoundError(
            "❌ فایل credentials.json پیدا نشد.\n"
            "لطفاً آن را از Google Cloud Console دانلود کرده و در پنل سمت چپ Colab آپلود کنید.\n"
            "سپس این سلول را دوباره اجرا کنید."
        )

    flow = InstalledAppFlow.from_client_secrets_file(
    'credentials.json',
    SCOPES,
    redirect_uri='urn:ietf:wg:oauth:2.0:oob'
)
    auth_url, _ = flow.authorization_url(prompt='consent')
    print("\n🔗 برای ادامه، لینک زیر را در مرورگر باز کنید و حساب گوگل خود را انتخاب کنید:")
    print(auth_url)
    print("\nسپس کد تأیید داده شده را در کادر زیر وارد کنید:")
    from getpass import getpass
    code = getpass("Authorization code: ")
    flow.fetch_token(code=code)
    creds = flow.credentials
    _save_token_to_secret(pickle.dumps(creds))
    print("✅ احراز هویت دستی با موفقیت انجام و ذخیره شد.")
    return creds

def authenticate_google_drive():
    creds = _get_credentials()
    return build('drive', 'v3', credentials=creds)

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
