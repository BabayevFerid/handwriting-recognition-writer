import os
import random
import io
from flask import Flask, render_template, request, redirect, send_file, url_for
from PIL import Image, ImageDraw
try:
    import easyocr
    OCR_ENABLED = True
    reader = easyocr.Reader(['en', 'az'])
except ImportError:
    OCR_ENABLED = False

app = Flask(__name__)

# Yaradılacaq qovluqlar
os.makedirs("glyphs", exist_ok=True)
os.makedirs("output", exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html", ocr_enabled=OCR_ENABLED)

@app.route("/collect", methods=["GET", "POST"])
def collect():
    if request.method == "POST":
        char = request.form.get("char")
        data = request.form.get("dataURL")
        if char and data:
            from base64 import b64decode
            header, encoded = data.split(",", 1)
            imgdata = b64decode(encoded)
            save_dir = os.path.join("glyphs", char)
            os.makedirs(save_dir, exist_ok=True)
            count = len(os.listdir(save_dir))
            with open(os.path.join(save_dir, f"sample_{count}.png"), "wb") as f:
                f.write(imgdata)
        return redirect(url_for("collect"))
    return render_template("collect.html")

@app.route("/render", methods=["GET", "POST"])
def render_text():
    if request.method == "POST":
        text = request.form.get("text")
        line_height = int(request.form.get("line_height", 120))
        spacing = int(request.form.get("spacing", 20))
        jitter = int(request.form.get("jitter", 5))

        lines = text.split("\n")
        width = max(len(line) for line in lines) * (100 + spacing)
        height = len(lines) * line_height

        img = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(img)

        y = 10
        for line in lines:
            x = 10
            for ch in line:
                glyph_dir = os.path.join("glyphs", ch)
                if os.path.exists(glyph_dir) and os.listdir(glyph_dir):
                    sample = random.choice(os.listdir(glyph_dir))
                    glyph_img = Image.open(os.path.join(glyph_dir, sample))
                    img.paste(glyph_img, (x + random.randint(-jitter, jitter), y), glyph_img)
                    x += glyph_img.width + spacing
                else:
                    draw.text((x, y), ch, fill="black")
                    x += 40 + spacing
            y += line_height

        output_path = os.path.join("output", "rendered.png")
        img.save(output_path)
        return send_file(output_path, mimetype="image/png")
    return render_template("render.html")

@app.route("/ocr", methods=["GET", "POST"])
def ocr():
    if not OCR_ENABLED:
        return "EasyOCR quraşdırılmayıb."
    result_text = None
    if request.method == "POST":
        file = request.files["file"]
        if file:
            img = Image.open(file.stream).convert("RGB")
            img_path = "temp.png"
            img.save(img_path)
            results = reader.readtext(img_path)
            result_text = " ".join([res[1] for res in results])
    return render_template("ocr.html", text=result_text)

if __name__ == "__main__":
    app.run(debug=False)
