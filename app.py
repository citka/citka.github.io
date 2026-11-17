import os
import secrets
import subprocess
import tempfile
from pathlib import Path
from flask import Flask, render_template, request, send_file, abort, flash, redirect, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500 MB upload limit

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}
OUTPUT_DIR = Path(tempfile.gettempdir()) / "vconvert_outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

@app.get("/")
def index():
    return render_template("index.html")

@app.post("/convert")
def convert():
    uploaded = request.files.get("video")
    output_format = request.form.get("format", "mp4").lower()
    quality = request.form.get("quality", "1080")

    if not uploaded or not uploaded.filename:
        flash("กรุณาเลือกไฟล์วิดีโอก่อน")
        return redirect(url_for("index"))

    ext = Path(uploaded.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        flash("ไฟล์นี้ยังไม่รองรับ กรุณาใช้ MP4, MOV, MKV, WEBM, AVI หรือ M4V")
        return redirect(url_for("index"))
    if output_format not in {"mp4", "mp3"}:
        abort(400)

    job_id = secrets.token_urlsafe(12)
    with tempfile.TemporaryDirectory(prefix="vconvert_") as workdir:
        source = Path(workdir) / f"input{ext}"
        output = Path(workdir) / f"converted.{output_format}"
        uploaded.save(source)

        command = ["ffmpeg", "-y", "-i", str(source), "-map", "0:a:0?"]
        if output_format == "mp3":
            command += ["-vn", "-codec:a", "libmp3lame", "-b:a", "192k", str(output)]
        else:
            scale = {"720": "1280:720", "1080": "1920:1080", "original": None}.get(quality, "1920:1080")
            command = ["ffmpeg", "-y", "-i", str(source), "-map", "0:v:0", "-map", "0:a:0?"]
            if scale:
                command += ["-vf", f"scale={scale}:force_original_aspect_ratio=decrease,pad={scale}:(ow-iw)/2:(oh-ih)/2"]
            command += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(output)]

        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=900, check=False)
        except subprocess.TimeoutExpired:
            flash("การแปลงใช้เวลานานเกินกำหนด (15 นาที) ลองใช้ไฟล์ที่เล็กลง")
            return redirect(url_for("index"))

        if result.returncode != 0 or not output.exists() or output.stat().st_size == 0:
            app.logger.warning("FFmpeg conversion failed: %s", result.stderr[-2000:])
            flash("แปลงไฟล์ไม่สำเร็จ ไฟล์อาจเสียหรือไม่มีแทร็กเสียง/วิดีโอที่รองรับ")
            return redirect(url_for("index"))

        # Keep a unique result briefly so Flask can stream it after the temp workspace closes.
        final_path = OUTPUT_DIR / f"{job_id}.{output_format}"
        output.replace(final_path)

    response = send_file(final_path, as_attachment=True, download_name=f"vconvert.{output_format}")
    @response.call_on_close
    def cleanup():
        try:
            final_path.unlink(missing_ok=True)
        except OSError:
            pass
    return response

@app.errorhandler(413)
def too_large(_error):
    return "ไฟล์มีขนาดใหญ่เกิน 500 MB", 413

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
