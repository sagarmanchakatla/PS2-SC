from flask import Flask, render_template, request, send_file, jsonify
from PIL import Image
import os
import io
import traceback
import logging
import random

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

class TextToSignLanguageConverter:
    def __init__(self, data_folder):
        self.data_folder = data_folder
        self.image_map = self._create_image_map()

    def _create_image_map(self):
        image_map = {}
        for letter in os.listdir(self.data_folder):
            letter_path = os.path.join(self.data_folder, letter)
            if os.path.isdir(letter_path):
                image_map[letter.lower()] = [
                    os.path.join(letter_path, img)
                    for img in os.listdir(letter_path)
                    if img.lower().endswith(('.png', '.jpg', '.jpeg'))
                ]
        return image_map

    def convert_text(self, text):
        words = text.lower().split()
        image_sequence = []

        for word in words:
            for char in word:
                if char in self.image_map:
                    try:
                        image_path = random.choice(self.image_map[char])
                        image = Image.open(image_path)
                        image_sequence.append(image)
                        app.logger.info(f"Loaded image for '{char}': {image.size} from {image_path}")
                    except Exception as e:
                        app.logger.error(f"Error loading image for '{char}': {str(e)}")
            
            # Add a space between words
            if word != words[-1]:
                image_sequence.append(None)  # None represents a space

        return image_sequence

    def create_result_image(self, image_sequence):
        # Calculate the total width and maximum height
        total_width = sum(img.width if img else 50 for img in image_sequence)  # 50px for space
        max_height = max(img.height if img else 0 for img in image_sequence)

        app.logger.info(f"Calculated dimensions: width={total_width}, height={max_height}")

        # Add a small buffer to the dimensions
        buffer = 10
        total_width += buffer
        max_height += buffer

        # Create a new image with the calculated dimensions
        result_image = Image.new('RGB', (total_width, max_height), color='white')

        # Paste all images into the result image
        x_offset = 0
        for img in image_sequence:
            if img:
                try:
                    result_image.paste(img, (x_offset, 0))
                    app.logger.info(f"Pasted image at x_offset={x_offset}")
                    x_offset += img.width
                except Exception as e:
                    app.logger.error(f"Error pasting image: {str(e)}")
            else:
                x_offset += 50  # Space width

        return result_image

# Update this path to the location of your 'data1' folder
converter = TextToSignLanguageConverter("data1")

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        input_text = request.form['text']
        try:
            image_sequence = converter.convert_text(input_text)
            result_image = converter.create_result_image(image_sequence)
            
            img_io = io.BytesIO()
            result_image.save(img_io, 'PNG')
            img_io.seek(0)
            return send_file(img_io, mimetype='image/png')
        except Exception as e:
            app.logger.error(f"Error processing request: {str(e)}")
            app.logger.error(traceback.format_exc())
            return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)