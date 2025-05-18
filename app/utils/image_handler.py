import os
from flask import current_app
from werkzeug.utils import secure_filename
from PIL import Image
import uuid

# use cloudinary as CDN


class ImageHandler:
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

    @staticmethod
    def allowed_file(filename):
        return (
            "." in filename
            and filename.rsplit(".", 1)[1].lower() in ImageHandler.ALLOWED_EXTENSIONS
        )

    @staticmethod
    def save_image(file, upload_folder):
        if not file or not ImageHandler.allowed_file(file.filename):
            return None

        filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
        filepath = os.path.join(upload_folder, filename)

        try:
            # Save original image
            file.save(filepath)

            # Create thumbnail
            thumbnail_path = os.path.join(upload_folder, f"thumb_{filename}")
            with Image.open(filepath) as img:
                img.thumbnail((200, 200))
                img.save(thumbnail_path)

            return filename
        except Exception as e:
            current_app.logger.error(f"Error saving image: {str(e)}")
            return None


def upload_to_s3():
    print("todo")
