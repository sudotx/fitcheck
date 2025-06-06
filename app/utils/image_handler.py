import uuid

import cloudinary
import cloudinary.uploader
from cloudinary import CloudinaryImage
from flask import current_app

from PIL import Image
from werkzeug.utils import secure_filename

from app.config import config

# Configure Cloudinary
cloudinary.config(
    cloud_name=config.CLOUDINARY_CLOUD_NAME,
    api_key=config.CLOUDINARY_API_KEY,
    api_secret=config.CLOUDINARY_API_SECRET,
    secure=True,
)


class ImageHandler:

    @staticmethod
    def allowed_file(filename):
        return (
            "." in filename
            and filename.rsplit(".", 1)[1].lower() in config.ALLOWED_EXTENSIONS
        )

    @staticmethod
    def upload_to_cloudinary(file, folder):
        """
        Upload an image to Cloudinary and return the URL
        """
        # if not file or not ImageHandler.allowed_file(file.filename):
        #     return None

        try:
            # Generate a unique filename
            filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"

            # Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(
                file,
                folder=folder,
                public_id=filename,
                unique_filename=True,
                overwrite=True,
                resource_type="image",
            )

            # Get the secure URL
            image_url = upload_result.get("secure_url")

            # Create a thumbnail version
            thumbnail_url = CloudinaryImage(f"{folder}/{filename}").build_url(
                width=200, height=200, crop="fill"
            )

            return {
                "original_url": image_url,
                "thumbnail_url": thumbnail_url,
                "public_id": upload_result.get("public_id"),
            }

        except Exception as e:
            current_app.logger.error(f"Error uploading to Cloudinary: {str(e)}")
            return None

    @staticmethod
    def delete_from_cloudinary(public_id):
        """
        Delete an image from Cloudinary
        """
        try:
            result = cloudinary.uploader.destroy(public_id)
            return result.get("result") == "ok"
        except Exception as e:
            current_app.logger.error(f"Error deleting from Cloudinary: {str(e)}")
            return False


image_handler = ImageHandler()
