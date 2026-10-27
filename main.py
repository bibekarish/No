import re
from urllib.parse import urlparse

import requests
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "change-this-to-a-random-secret"

GOOGLE_DRIVE_HOSTS = {
    "drive.google.com",
    "docs.google.com",
}


def extract_file_id(url):
    """Extract a Google Drive file ID from common share URLs."""
    parsed = urlparse(url.strip())

    if parsed.scheme != "https" or parsed.hostname not in GOOGLE_DRIVE_HOSTS:
        return None

    patterns = [
        r"/file/d/([a-zA-Z0-9_-]+)",
        r"/document/d/([a-zA-Z0-9_-]+)",
        r"/spreadsheets/d/([a-zA-Z0-9_-]+)",
        r"/presentation/d/([a-zA-Z0-9_-]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, parsed.path)
        if match:
            return match.group(1)

    if parsed.path == "/open":
        from urllib.parse import parse_qs
        file_id = parse_qs(parsed.query).get("id", [None])[0]
        if file_id and re.fullmatch(r"[a-zA-Z0-9_-]+", file_id):
            return file_id

    return None


@app.route("/", methods=["GET", "POST"])
def index():
    video_url = None
    download_url = None
    original_url = ""

    if request.method == "POST":
        original_url = request.form.get("drive_url", "").strip()
        file_id = extract_file_id(original_url)

        if not file_id:
            flash("Please enter a valid HTTPS Google Drive sharing link.", "error")
        else:
            # These endpoints work only when Google Drive permits access.
            video_url = (
                f"https://drive.google.com/file/d/{file_id}/preview"
            )
            download_url = (
                f"https://drive.google.com/uc?export=download&id={file_id}"
            )

    return render_template(
        "index.html",
        video_url=video_url,
        download_url=download_url,
        original_url=original_url,
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
