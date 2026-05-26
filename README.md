# 🤖 Telegram ↔ Google Drive Bot with YouTube Downloader
[📖 Persian Version (نسخه فارسی)](README_FA.md)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/PersianNull/ExpertComminucationLab/blob/main/telegram_bot_colab.ipynb)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

A powerful, production-ready Telegram bot that acts as your personal bridge between Telegram and Google Drive. Send files, download YouTube videos with quality selection, compress before uploading, and sync files bidirectionally — all with a single click on Google Colab.

---

## ✨ Features

### 📂 Telegram → Google Drive (File Upload)
- Send any **document, video, audio, or photo** to the bot
- Files are automatically uploaded to the **`Received`** folder in your Google Drive
- **Optional ZIP compression** before upload — save space and bandwidth

### 🎬 YouTube → Google Drive (Video Download)
- Send any **YouTube link** to the bot
- Choose from **all available qualities** (144p up to 4K)
- Option to extract **audio only (MP3)**
- **Optional ZIP compression** after download
- Videos are saved in the **`YouTube`** folder in your Google Drive

### 📤 Google Drive → Telegram (File Retrieval)
- Place any file in the **`Sent`** folder of your Google Drive
- Use the **`/sent`** command in Telegram to browse and download files
- Bot **automatically notifies you** when new files appear in the Sent folder

### 🔒 Security
- **User whitelist**: only authorized Telegram user IDs can interact with the bot
- **OAuth 2.0**: Google Drive authentication uses secure token-based access
- **No sensitive data** stored in GitHub — credentials are entered at runtime

### ☁️ Easy Deployment
- **One-click launch** on Google Colab — no server, no VPS, no terminal
- **No coding required** — just run the provided cells in order
- **Automatic dependency installation** — everything is handled for you

---

## 📋 Prerequisites

Before running the bot, you need to obtain four things:

| # | Item | Description | Source |
|---|------|-------------|--------|
| 1 | `API_ID` | Telegram API application ID | [my.telegram.org](https://my.telegram.org) |
| 2 | `API_HASH` | Telegram API application hash | [my.telegram.org](https://my.telegram.org) |
| 3 | `BOT_TOKEN` | Your Telegram bot token | [@BotFather](https://t.me/BotFather) |
| 4 | `USER_ID` | Your Telegram numeric user ID | [@userinfobot](https://t.me/userinfobot) |
| 5 | `credentials.json` | Google OAuth 2.0 Client ID (for Drive access) | [Google Cloud Console](https://console.cloud.google.com) |

---

## 🔧 Installation & Setup Guide

### Step 1: Get Telegram API_ID and API_HASH

1. Go to [my.telegram.org](https://my.telegram.org) and log in with your phone number.
2. Click on **"API development tools"**.
3. Fill out the **"Create New Application"** form:
   - **App title**: `MyGoogleDriveBot` (or any name you like)
   - **Short name**: `GDBot` (no spaces)
   - **Platform**: `Desktop`
   - **URL**: (leave empty — not required)
4. Click **"Create application"**.
5. You will see your **`api_id`** (a number) and **`api_hash`** (a long string). Save these securely.

> ⚠️ **Important**: `api_id` and `api_hash` belong to your Telegram account, not the bot. Keep them private.

---

### Step 2: Create a Telegram Bot and Get BOT_TOKEN

1. Open Telegram and search for [@BotFather](https://t.me/BotFather).
2. Start a chat and send the command: `/newbot`
3. Follow the instructions:
   - Choose a **name** for your bot (e.g., `My Google Drive Bot`)
   - Choose a **username** for your bot (must end with `bot`, e.g., `MyGDriveBot`)
4. After creation, BotFather will give you a **token** (looks like: `1234567890:ABCdefGHIJklmNOPQRSTuvwxYz`).
5. Save this token securely.

> ⚠️ **Important**: Never share your bot token with anyone. Anyone with this token can control your bot.

---

### Step 3: Get Your Telegram USER_ID

1. Open Telegram and search for [@userinfobot](https://t.me/userinfobot).
2. Start the bot and send any message (or just `/start`).
3. The bot will reply with your **`Id`** (a number like `123456789`).
4. Save this number — it will be used to authorize you as the only user of your bot.

> 💡 **Multiple users?** Separate IDs with commas: `123456789,987654321`

---

### Step 4: Google Cloud Project & OAuth Setup (credentials.json)

This is a **one-time manual setup** to give your bot secure access to your Google Drive.

1.  Go to the [Google Cloud Console](https://console.cloud.google.com).
2.  Create a new project (or select an existing one) from the top bar.
3.  **Enable the Drive API**: Use the search bar to find **"Google Drive API"**, select it, and click **"Enable"**.
4.  **Configure the Consent Screen**:
    *   Go to **APIs & Services** → **OAuth consent screen**.
    *   Choose **External** as the User Type and click **Create**.
    *   Fill in only the required fields: **App name** (e.g., `My Colab Bot`), **User support email** (your email), and **Developer contact information** (your email again).
    *   Click **Save and Continue** through the Scopes and Test Users sections (you don't need to add anything there yet).
    *   **Crucial Step**: Navigate to **Audience** in the left sidebar, and under **Test users**, click **Add Users** and enter your own email. This allows you to use the app before it's verified by Google.
5.  **Create the Credentials**:
    *   Go to **APIs & Services** → **Credentials**.
    *   Click **Create Credentials** → **OAuth client ID**.
    *   Choose **Desktop app** as the Application type and give it a name.
    *   Click **Create**.
    *   Click **Download JSON** on the right side of your new Client ID.
6.  **Rename the file**: Rename the downloaded file to exactly **`credentials.json`**.

> 🔒 **Do not share this file.** It contains secrets that allow access to your Google Drive. It will be uploaded directly to your private Colab session.

---

### Step 5: Run the Notebook on Google Colab

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/PersianNull/ExpertComminucationLab/blob/main/telegram_bot_colab.ipynb)

1.  **Click the "Open In Colab" badge above**. The notebook will open in your browser.
2.  **Upload `credentials.json`**: In the Colab sidebar, click the folder icon. Drag and drop your `credentials.json` file there.
3.  **Run Cell 1**: Installs all required Python libraries and FFmpeg.
4.  **Run Cell 2 (Credentials)**: This cell will download the latest project files. When prompted, enter your `API_ID`, `API_HASH`, `BOT_TOKEN`, and `USER_ID`. These are securely stored in your session only.
5.  **Run Cell 3 (Launch Bot)**: The bot will start. For the **first time**, it will print a long Google link in the output.
    *   Click the link and log in with your Google account. You may see a warning that the app isn't verified—this is normal. Click **Continue**.
    *   Grant the requested permissions. You will receive an **Authorization Code**.
    *   Copy that code and paste it back into the Colab cell when it asks `Authorization code:`. Press Enter.
    *   The authentication token is now securely saved in Colab's Secrets for all future runs. You will not have to do this again.

> 🎉 Your bot is now running! The runtime will remain active as long as the Colab session is open. Send `/start` to your bot on Telegram to begin.

---

## 📖 Usage

### Commands in Telegram

| Command | Description |
|---------|-------------|
| `/start` | Display welcome message and usage instructions |
| `/sent` | List files available in the `Sent` folder for download |

### Sending Files to Google Drive
1. Send any file (document, video, audio, photo) to your bot.
2. The bot asks: **"Do you want to compress before upload?"**
3. Choose **"Compress (ZIP)"** or **"Without Compression"**.
4. File is uploaded to `TelegramBot/Received` in your Google Drive.

### Downloading YouTube Videos
1. Send a YouTube link (e.g., `https://www.youtube.com/watch?v=...`).
2. Bot displays video info and available qualities.
3. Select a quality or **"Audio only (MP3)"**.
4. After download, choose whether to compress before upload.
5. File is saved in `TelegramBot/YouTube` in your Google Drive.

### Retrieving Files from Google Drive
1. Place any file in the `TelegramBot/Sent` folder in your Google Drive.
2. The bot notifies you: **"🔔 New file in Sent"**.
3. Send `/sent` to see all available files.
4. Click on a file to download it to Telegram.

---

## 🔐 Security Notes

- **`.env` file is never committed** to GitHub — credentials are entered at runtime.
- **Only whitelisted users** can interact with the bot (controlled by `AUTHORIZED_USERS`).
- The Google OAuth token is saved securely in your Colab **Secrets** and refreshed automatically.
- Session data is stored **in-memory** — no persistent files on disk.

---

## ⚠️ Limitations (Free Colab)

- Google Colab free tier disconnects after **~90 minutes of inactivity**.
- For 24/7 operation, deploy the bot on a **VPS** (DigitalOcean, Hetzner, etc.).
- Maximum file size for Telegram bots: **50 MB** (regular), **2 GB** (channels).
- Google Drive storage depends on your account's quota.

---

## 📄 License

This project is licensed under the **MIT License** — feel free to use, modify, and share.

---

## 🙏 Acknowledgements

- [Pyrogram](https://docs.pyrogram.org/) — elegant Telegram MTProto framework
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — powerful YouTube downloader
- [Google Colab](https://colab.research.google.com/) — free cloud execution environment

---
