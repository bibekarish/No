import os
import re
from urllib.parse import urlparse, parse_qs

from flask import Flask, render_template, request, flash

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    os.urandom(32).hex()
)

GOOGLE_DRIVE_HOSTS = {
    "drive.google.com",
    "docs.google.com",
}


def extract_file_id(url):
    """Extract a Google Drive file ID from supported URLs."""
    try:
        parsed = urlparse(url.strip())

        if (
            parsed.scheme != "https"
            or parsed.hostname not in GOOGLE_DRIVE_HOSTS
            or parsed.port is not None
            or parsed.username is not None
            or parsed.password is not None
        ):
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
            file_id = parse_qs(parsed.query).get("id", [None])[0]

            if file_id and re.fullmatch(r"[a-zA-Z0-9_-]+", file_id):
                return file_id

    except (ValueError, AttributeError):
        return None

    return None


def render_player(file_id=None, original_url=""):
    video_url = None
    download_url = None

    if file_id and re.fullmatch(r"[a-zA-Z0-9_-]+", file_id):
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


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        # Supports: /?drive_url=GOOGLE_DRIVE_URL
        drive_url = request.args.get("drive_url", "").strip()

        if drive_url:
            file_id = extract_file_id(drive_url)

            if file_id:
                return render_player(file_id, drive_url)

        # Supports: /?id=GOOGLE_DRIVE_FILE_ID
        file_id = request.args.get("id", "").strip()

        if file_id and re.fullmatch(r"[a-zA-Z0-9_-]+", file_id):
            return render_player(file_id)

        return render_player()

    original_url = request.form.get("drive_url", "").strip()

    if len(original_url) > 2048:
        flash("The link is too long.", "error")
        return render_player()

    file_id = extract_file_id(original_url)

    if not file_id:
        flash("Please enter a valid Google Drive sharing link.", "error")
        return render_player(original_url=original_url)

    return render_player(file_id, original_url)


@app.route("/<path:drive_path>", methods=["GET"])
def direct_player(drive_path):
    """
    Direct format:
    /https://drive.google.com/file/d/FILE_ID/view
    """

    # The URL path may begin with https:/ because URL parsers
    # normalize slashes in some cases.
    candidate = drive_path

    if candidate.startswith("https:/") and not candidate.startswith("https://"):
        candidate = candidate.replace("https:/", "https://", 1)

    if not candidate.startswith("https://"):
        return "Invalid URL. Use a Google Drive sharing link.", 400

    file_id = extract_file_id(candidate)

    if not file_id:
        return "Invalid Google Drive sharing link.", 400

    return render_player(file_id, candidate)


@app.route("/<file_id>", methods=["GET"])
def direct_id_player(file_id):
    """Short direct format: /GOOGLE_DRIVE_FILE_ID"""

    if not re.fullmatch(r"[a-zA-Z0-9_-]+", file_id):
        return "Invalid Google Drive file ID.", 400

    return render_player(file_id)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
