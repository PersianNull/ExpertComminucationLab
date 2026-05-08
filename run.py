import os
import asyncio
import nest_asyncio
nest_asyncio.apply()

from config import (
    API_ID, API_HASH, BOT_TOKEN, AUTHORIZED_USERS,
    RECEIVED_FOLDER, YOUTUBE_FOLDER, SENT_FOLDER, SENT_POLL_INTERVAL
)
from google_drive import (
    authenticate_google_drive, get_or_create_folder,
    upload_file_from_memory, download_file, list_files_in_folder, check_new_files_in_sent
)
from youtube_dl import get_video_info, download_video, download_audio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import tempfile
import zipfile
import shutil  

print("🔐 احراز هویت گوگل درایو...")
drive_service = authenticate_google_drive()
print("✅ احراز هویت گوگل انجام شد.")

app = Client(
    ":memory:",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True
)

user_last_url = {}
pending_compression = {}  

def authorized_only(func):
    async def wrapper(client, message):
        if message.from_user.id not in AUTHORIZED_USERS:
            await message.reply("⛔ شما مجاز به استفاده از این بات نیستید.")
            return
        return await func(client, message)
    return wrapper

def quality_keyboard(formats):
    buttons = []
    for fmt in formats[:8]:
        label = f"🎥 {fmt['resolution']} ({fmt['ext']})"
        buttons.append([InlineKeyboardButton(label, callback_data=f"yt_dl|{fmt['resolution']}")])
    buttons.append([InlineKeyboardButton("🎵 فقط صوت (MP3)", callback_data="yt_audio")])
    buttons.append([InlineKeyboardButton("❌ لغو", callback_data="yt_cancel")])
    return InlineKeyboardMarkup(buttons)

def compress_file(file_path: str, output_dir: str) -> str:
    """فایل را زیپ کرده و مسیر فایل زیپ‌شده را برمی‌گرداند."""
    base = os.path.basename(file_path)
    zip_name = os.path.splitext(base)[0] + ".zip"
    zip_path = os.path.join(output_dir, zip_name)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(file_path, arcname=base)
    return zip_path

@app.on_message(filters.command("start"))
@authorized_only
async def start_command(client, message):
    await message.reply(
        "👋 سلام! من بات مدیریت فایل و یوتیوب هستم.\n\n"
        "✅ فایل ارسال کنی → امکان فشرده‌سازی و ذخیره در Google Drive\n"
        "🔗 لینک یوتیوب بفرستی → انتخاب کیفیت + امکان فشرده‌سازی\n"
        "📂 دستور /sent → دریافت فایل‌های موجود در پوشه Sent\n\n"
        "⚠️ فقط کاربر مجاز می‌تواند از بات استفاده کند."
    )

@app.on_message(filters.document | filters.video | filters.audio | filters.photo)
@authorized_only
async def receive_file(client, message):
    status_msg = await message.reply("⬇️ در حال دریافت فایل...")
    user_id = message.from_user.id
    try:
        temp_path = await client.download_media(message)
        file_name = message.document.file_name if message.document else os.path.basename(temp_path)
        received_id = get_or_create_folder(drive_service, RECEIVED_FOLDER)

        pending_compression[user_id] = {
            'file_path': temp_path,
            'file_name': file_name,
            'parent_id': received_id,
            'tmpdir': None,          
            'is_youtube': False
        }

        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🗜 فشرده کن (ZIP)", callback_data="compress_yes")],
            [InlineKeyboardButton("📂 بدون فشرده‌سازی", callback_data="compress_no")]
        ])
        await status_msg.edit_text(
            f"📥 فایل **{file_name}** دریافت شد.\nآیا می‌خواهید قبل از آپلود فشرده شود؟",
            reply_markup=buttons
        )
    except Exception as e:
        await status_msg.edit_text(f"❌ خطا در دریافت فایل: {e}")

@app.on_message(filters.text & filters.regex(r'https?://(?:www\.)?(youtube\.com|youtu\.be)/\S+'))
@authorized_only
async def youtube_link(client, message):
    url = message.text.strip()
    info_msg = await message.reply("🔍 دریافت اطلاعات ویدیو...")
    try:
        info = get_video_info(url)
        await info_msg.delete()
        user_last_url[message.from_user.id] = url
        await message.reply_photo(
            photo=info['thumbnail'],
            caption=f"🎬 **{info['title']}**\n⏱ {info['duration']} ثانیه\n\nلطفاً کیفیت یا گزینه صوت را انتخاب کنید:",
            reply_markup=quality_keyboard(info['formats'])
        )
    except Exception as e:
        await info_msg.edit_text(f"❌ خطا در پردازش لینک: {e}")

@app.on_message(filters.command("sent"))
@authorized_only
async def sent_files(client, message):
    try:
        sent_id = get_or_create_folder(drive_service, SENT_FOLDER)
        files = list_files_in_folder(drive_service, sent_id)
        if not files:
            await message.reply("📂 پوشه Sent خالی است.")
            return
        buttons = []
        for f in files[:20]:
            size_mb = int(f['size']) / (1024*1024) if f['size'].isdigit() else 0
            label = f"{f['title']} ({size_mb:.1f} MB)"
            buttons.append([InlineKeyboardButton(label, callback_data=f"send_file|{f['id']}")])
        await message.reply("📁 فایل‌های موجود در Sent:", reply_markup=InlineKeyboardMarkup(buttons))
    except Exception as e:
        await message.reply(f"❌ خطا: {e}")

@app.on_callback_query()
async def unified_callback(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id

    if user_id not in AUTHORIZED_USERS:
        await callback_query.answer("⛔ شما مجاز به استفاده از این بات نیستید.", show_alert=True)
        return

    data = callback_query.data

    if data.startswith("send_file|"):
        file_id = data.split("|")[1]
        try:
            status = await callback_query.message.reply("⬇️ در حال آماده‌سازی فایل...")
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                download_file(drive_service, file_id, tmp.name)
                file_path = tmp.name
            await callback_query.message.reply_document(document=file_path)
            os.unlink(file_path)
            await status.delete()
        except Exception as e:
            await callback_query.message.reply(f"❌ خطا در ارسال فایل: {e}")
        await callback_query.answer()
        return

    if data in ("compress_yes", "compress_no"):
        pending = pending_compression.pop(user_id, None)
        if not pending:
            await callback_query.answer("⛔ اطلاعات فایل منقضی شده است.", show_alert=True)
            return

        file_path = pending['file_path']
        file_name = pending['file_name']
        parent_id = pending['parent_id']
        tmpdir = pending.get('tmpdir')
        is_youtube = pending.get('is_youtube', False)

        await callback_query.message.edit_reply_markup(None)

        try:
            if data == "compress_yes":
                await callback_query.message.edit_text("🗜 در حال فشرده‌سازی...")
                work_dir = tmpdir if (tmpdir and os.path.isdir(tmpdir)) else os.path.dirname(file_path)
                zip_path = compress_file(file_path, work_dir)
                with open(zip_path, "rb") as f:
                    file_bytes = f.read()
                os.unlink(zip_path)
                upload_file_from_memory(drive_service, file_bytes, os.path.basename(zip_path), parent_id)
                await callback_query.message.edit_text(f"✅ فایل فشرده‌شده در Google Drive ذخیره شد.")
            else:
                await callback_query.message.edit_text("☁️ در حال آپلود به گوگل درایو...")
                with open(file_path, "rb") as f:
                    file_bytes = f.read()
                upload_file_from_memory(drive_service, file_bytes, file_name, parent_id)
                await callback_query.message.edit_text(f"✅ فایل '{file_name}' در Google Drive ذخیره شد.")
        except Exception as e:
            await callback_query.message.edit_text(f"❌ خطا در آپلود: {e}")
        finally:

            if tmpdir and os.path.isdir(tmpdir):
                shutil.rmtree(tmpdir, ignore_errors=True)
            else:

                if os.path.exists(file_path):
                    os.unlink(file_path)
            await callback_query.answer()
        return


    if data == "yt_cancel":
        await callback_query.message.delete()
        await callback_query.answer("عملیات لغو شد.")
        return


    if data.startswith("yt_dl|") or data == "yt_audio":
        url = user_last_url.get(user_id)
        if not url:
            await callback_query.answer("⛔ لینک منقضی شده، دوباره بفرست.", show_alert=True)
            return

        await callback_query.answer()
        status_msg = await callback_query.message.reply("⬇️ در حال دانلود از یوتیوب...")
        try:

            tmpdir = tempfile.mkdtemp()
            if data == "yt_audio":
                file_path = download_audio(url, output_dir=tmpdir)
            else:
                quality = data.split("|")[1]
                file_path = download_video(url, quality, output_dir=tmpdir)

            file_name = os.path.basename(file_path)
            youtube_id = get_or_create_folder(drive_service, YOUTUBE_FOLDER)

            pending_compression[user_id] = {
                'file_path': file_path,
                'file_name': file_name,
                'parent_id': youtube_id,
                'tmpdir': tmpdir,
                'is_youtube': True
            }

            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("🗜 فشرده کن (ZIP)", callback_data="compress_yes")],
                [InlineKeyboardButton("📂 بدون فشرده‌سازی", callback_data="compress_no")]
            ])
            await status_msg.edit_text(
                f"📥 **{file_name}** دانلود شد.\nآیا قبل از آپلود فشرده شود؟",
                reply_markup=buttons
            )
        except Exception as e:
            await status_msg.edit_text(f"❌ خطا: {e}")
        return


    await callback_query.answer("انتخاب نامعتبر.", show_alert=True)


async def monitor_sent():
    while True:
        try:
            new_files = check_new_files_in_sent(drive_service)
            if new_files:
                for uid in AUTHORIZED_USERS:
                    for f in new_files:
                        size_mb = int(f['size']) / (1024*1024) if f['size'].isdigit() else 0
                        await app.send_message(uid, f"🔔 فایل جدید در Sent:\n{f['title']} ({size_mb:.1f} MB)\nبا /sent دریافت کنید.")
        except Exception as e:
            print(f"خطا در مانیتورینگ Sent: {e}")
        await asyncio.sleep(SENT_POLL_INTERVAL)


async def runner():
    print("🚀 شروع بات...")
    await app.start()
    print("✅ بات فعال شد! (قابلیت فشرده‌سازی هوشمند)")
    asyncio.create_task(monitor_sent())
    await pyrogram.idle()
    await app.stop()

if __name__ == "__main__":
    import pyrogram
    asyncio.run(runner())