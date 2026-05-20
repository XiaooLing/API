from flask import Flask, request, jsonify
import requests
from PIL import Image, ImageOps
from io import BytesIO
import base64

app = Flask(__name__)

@app.route('/', methods=['POST'])
def get_pixels():
    data = request.get_json(silent=True) or {}
    url = data.get("url")
    width = data.get("width")
    height = data.get("height")

    # Default to 128x128 if not provided
    size = 128
    if width and height:
        try:
            width = int(width)
            height = int(height)
            size = (width, height)
        except ValueError:
            return jsonify({"error": "Invalid width or height"}), 400
    elif data.get("res"):
        # fallback to 'res' if width and height are not provided
        try:
            size = int(data.get("res"))
        except ValueError:
            return jsonify({"error": "Invalid res value"}), 400

    if not url:
        return jsonify({"error": "missing url"}), 400

    try:
        # -------------------------
        # BASE64 IMAGE SUPPORT
        # -------------------------
        if url.startswith("data:image"):
            header, encoded = url.split(",", 1)
            img_bytes = base64.b64decode(encoded)
            img = Image.open(BytesIO(img_bytes))
        # -------------------------
        # NORMAL URL IMAGE SUPPORT
        # -------------------------
        else:
            response = requests.get(
                url,
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                                  "Chrome/58.0.3029.110 Safari/537.36"
                },
                stream=True,
                timeout=60
            )

            response.raise_for_status()

            # 🔥 CHECK IF IT'S REALLY AN IMAGE
            content_type = response.headers.get("Content-Type", "")

            if "image" not in content_type:
                return jsonify({
                    "error": "URL is not an image",
                    "content_type": content_type
                }), 400

            img = Image.open(BytesIO(response.content))

        # -------------------------
        # PROCESS IMAGE
        # -------------------------
        img = img.convert("RGB")
        # Scale image without stretching
        if isinstance(size, tuple):
            target_size = size
        else:
            target_size = (size, size)
        img = ImageOps.contain(img, target_size)

        # Create black canvas with specified size
        canvas = Image.new("RGB", target_size, (0, 0, 0))
        # Center image
        x = (target_size[0] - img.width) // 2
        y = (target_size[1] - img.height) // 2
        canvas.paste(img, (x, y))

        # Convert to pixel matrix
        pixels = list(canvas.getdata())
        pixel_matrix = [
            pixels[i * target_size[0]:(i + 1) * target_size[0]]
            for i in range(target_size[1])
        ]

        return jsonify({
            "size": target_size,
            "pixels": pixel_matrix
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run()
