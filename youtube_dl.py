import os
import yt_dlp
from config import YT_DLP_OPTIONS_TEMPLATE, AUDIO_OPTIONS

def get_video_info(url: str) -> dict:
    """
    اطلاعات پایه و کیفیت‌های موجود یک ویدیو را برمی‌گرداند.
    خروجی شامل:
        - title, thumbnail, duration
        - formats: لیستی از دیکشنری‌ها شامل format_id, resolution, ext, filesize
    """
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        formats = []

        for f in info.get('formats', []):

            if f.get('height') and f.get('ext') in ['mp4', 'webm']:
                formats.append({
                    'format_id': f['format_id'],
                    'resolution': f'{f["height"]}p',
                    'ext': f['ext'],
                    'filesize': f.get('filesize') or f.get('filesize_approx'),
                    'note': f.get('format_note', '')
                })

        unique = {}
        for fmt in formats:
            res = fmt['resolution']
            if res not in unique or (fmt['filesize'] and (not unique[res]['filesize'] or fmt['filesize'] > unique[res]['filesize'])):
                unique[res] = fmt
        sorted_formats = sorted(unique.values(), key=lambda x: int(x['resolution'][:-1]), reverse=True)

        return {
            'title': info.get('title', 'Unknown'),
            'thumbnail': info.get('thumbnail'),
            'duration': info.get('duration', 0),
            'formats': sorted_formats
        }


def download_video(url: str, quality: str, output_dir: str = ".") -> str:
    """
    دانلود ویدیو با کیفیت انتخاب‌شده (مثلاً '720p' یا '1080p').
    مسیر فایل دانلود شده را برمی‌گرداند.
    """
    height = quality.replace('p', '')
    template = {
        'format': f'bestvideo[height<={height}]+bestaudio/best[height<={height}]',
        'merge_output_format': 'mp4',
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(template) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info)

        if not os.path.exists(file_path):

            base = os.path.splitext(file_path)[0]
            for ext in ['mp4', 'webm', 'mkv']:
                candidate = f"{base}.{ext}"
                if os.path.exists(candidate):
                    file_path = candidate
                    break
    return file_path

def download_audio(url: str, output_dir: str = ".") -> str:
    """
    استخراج صوت و تبدیل به MP3.
    مسیر فایل صوتی نهایی را برمی‌گرداند.
    """
    options = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info)
        mp3_path = os.path.splitext(file_path)[0] + '.mp3'
        if not os.path.exists(mp3_path):
            raise RuntimeError("FFmpeg ممکن است نصب نباشد. در کولب: !apt update && apt install ffmpeg -y")
        return mp3_path