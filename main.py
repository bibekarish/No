import os
import re
from urllib.parse import urlparse, parse_qs

from flask import Flask, render_template, request, flash

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", os.urandom(32).hex())

GOOGLE_DRIVE_HOSTS = {
    "drive.google.com",
    "docs.google.com",
}


def extract_file_id(url):
    """Extract a file ID from a valid Google Drive sharing URL."""
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


@app.route("/", methods=["GET", "POST"])
def index():
    video_url = None
    download_url = None
    original_url = ""

    if request.method == "POST":
        original_url = request.form.get("drive_url", "").strip()

        if len(original_url) > 2048:
            flash("The link is too long.", "error")
        else:
            file_id = extract_file_id(original_url)

            if not file_id:
                flash(
                    "Please enter a valid Google Drive sharing link.",
                    "error",
                )
            else:
                video_url = (
                    f"https://drive.google.com/file/d/{file_id}/preview"
                )

                download_url = (
                    f"https://drive.google.com/uc"
                    f"?export=download&id={file_id}"
                )

    return render_template(
        "index.html",
        video_url=video_url,
        download_url=download_url,
        original_url=original_url,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
