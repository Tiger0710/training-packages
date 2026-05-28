"""
研修パッケージMDファイルをGoogle Docsに変換・アップロードするスクリプト
1. Google Drive上に共有フォルダ作成
2. MD → HTML変換
3. HTML → Google Docs としてアップロード
"""

import os
import markdown
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaInMemoryUpload

CREDENTIALS_DIR = r"C:\Users\TaigaKato\kimono-classifier\credentials"
TOKEN_PATH = os.path.join(CREDENTIALS_DIR, "token.json")
MD_DIR = r"C:\Users\TaigaKato\training-packages"

FILES = [
    ("01_新卒研修.md", "01_新卒社員研修パッケージ"),
    ("02_若手中堅研修.md", "02_若手・中堅社員研修パッケージ"),
    ("03_課長研修.md", "03_課長研修パッケージ"),
    ("04_部長経営層研修.md", "04_部長・経営層研修パッケージ"),
]

FOLDER_NAME = "HSJ研修パッケージ"


def get_credentials():
    creds = Credentials.from_authorized_user_file(TOKEN_PATH)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_PATH, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
        print("Token refreshed.")
    return creds


def md_to_html(md_path: str) -> str:
    with open(md_path, encoding="utf-8") as f:
        md_text = f.read()
    html_body = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "nl2br"],
    )
    # Wrap in minimal HTML with UTF-8
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body>{html_body}</body></html>"""


def create_folder(drive_service, name: str) -> str:
    meta = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    folder = drive_service.files().create(body=meta, fields="id,webViewLink").execute()
    folder_id = folder["id"]
    print(f"Folder created: {name} (id={folder_id})")
    print(f"  Link: {folder.get('webViewLink', 'N/A')}")

    # Make it accessible to anyone with the link (viewer)
    drive_service.permissions().create(
        fileId=folder_id,
        body={"type": "anyone", "role": "writer"},
    ).execute()
    print("  Shared: anyone with link can edit")

    return folder_id


def upload_doc(drive_service, folder_id: str, title: str, html_content: str) -> dict:
    media = MediaInMemoryUpload(
        html_content.encode("utf-8"),
        mimetype="text/html",
        resumable=False,
    )
    meta = {
        "name": title,
        "parents": [folder_id],
        "mimeType": "application/vnd.google-apps.document",
    }
    doc = (
        drive_service.files()
        .create(body=meta, media_body=media, fields="id,webViewLink")
        .execute()
    )
    print(f"  Uploaded: {title}")
    print(f"    Link: {doc.get('webViewLink', 'N/A')}")
    return doc


def main():
    creds = get_credentials()
    drive = build("drive", "v3", credentials=creds)

    # 1. Create folder
    folder_id = create_folder(drive, FOLDER_NAME)
    print()

    # 2. Convert and upload each file
    for md_file, doc_title in FILES:
        md_path = os.path.join(MD_DIR, md_file)
        if not os.path.exists(md_path):
            print(f"  SKIP (not found): {md_file}")
            continue
        html = md_to_html(md_path)
        upload_doc(drive, folder_id, doc_title, html)

    print()
    print("Done! All files uploaded.")
    print(f"Folder: https://drive.google.com/drive/folders/{folder_id}")


if __name__ == "__main__":
    main()
