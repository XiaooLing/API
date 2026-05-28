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
    res = data.get("res", 128)

    if not url:
        return jsonify({"error": "missing url"}), 400

    try:
        # Resolution
        try:
            res = int(res)
        except:
            return jsonify({"error": "invalid res"}), 400

        # -------------------------
        # LOAD IMAGE
        # -------------------------
        if url.startswith("data:image"):
            header, encoded = url.split(",", 1)
            img_bytes = base64.b64decode(encoded)
            img = Image.open(BytesIO(img_bytes))
        else:
            response = requests.get(
                url,
                headers={
                    "User-Agent":
                    "Mozilla/5.0"
                },
                timeout=60
            )

            response.raise_for_status()

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

        # Keep aspect ratio
        img.thumbnail((res, res))

        width, height = img.size

        pixels = list(img.getdata())

        pixel_matrix = [
            pixels[i * width:(i + 1) * width]
            for i in range(height)
        ]

        return jsonify({
            "width": width,
            "height": height,
            "pixels": pixel_matrix
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run()
