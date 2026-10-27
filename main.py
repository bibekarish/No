import os
import re
from urllib.parse import urlparse, parse_qs

from flask import Flask, render_template, request, flash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(32).hex())

DRIVE_HOSTS = {"drive.google.com", "docs.google.com"}


def extract_file_id(url):
    try:
        parsed = urlparse(url.strip())

        if (
            parsed.scheme != "https"
            or parsed.hostname not in DRIVE_HOSTS
            or parsed.port is not None
            or parsed.username is not None
            or parsed.password is not None
        ):
            return None

        match = re.search(
            r"/(?:file|document|spreadsheets|presentation)/d/([A-Za-z0-9_-]+)",
            parsed.path,
        )

        if match:
            return match.group(1)

        if parsed.path == "/open":
            file_id = parse_qs(parsed.query).get("id", [None])[0]
            if file_id and re.fullmatch(r"[A-Za-z0-9_-]+", file_id):
                return file_id

    except (ValueError, AttributeError):
        pass

    return None


def player(file_id=None, original_url=""):
    video_url = None
    download_url = None

    if file_id and re.fullmatch(r"[A-Za-z0-9_-]+", file_id):
        video_url = f"https://drive.google.com/file/d/{file_id}/preview"
        download_url = f"https://drive.google.com/uc?export=download&id={file_id}"

    return render_template(
        "index.html",
        video_url=video_url,
        download_url=download_url,
        original_url=original_url,
        file_id=file_id,
    )


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("drive_url", "").strip()

        if len(url) > 2048:
            flash("Link is too long.", "error")
            return player()

        file_id = extract_file_id(url)

        if not file_id:
            flash("Enter a valid Google Drive sharing link.", "error")
            return player(original_url=url)

        return player(file_id, url)

    # Example: /?id=GOOGLE_DRIVE_FILE_ID
    file_id = request.args.get("id", "").strip()

    if file_id and re.fullmatch(r"[A-Za-z0-9_-]+", file_id):
        return player(file_id)

    # Example: /?drive_url=https%3A%2F%2Fdrive.google.com%2Ffile%2Fd%2FID%2Fview
    drive_url = request.args.get("drive_url", "").strip()

    if drive_url:
        file_id = extract_file_id(drive_url)
        if file_id:
            return player(file_id, drive_url)

    return player()


@app.route("/<file_id>")
def direct_player(file_id):
    if not re.fullmatch(r"[A-Za-z0-9_-]+", file_id):
        return "Invalid file ID", 400

    return player(file_id)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
