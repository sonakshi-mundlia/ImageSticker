import os
import uuid

UPLOAD_DIR = "uploads"

def save_image(file):
    """
    Saves uploaded file and returns local path
    """

    # create folder if not exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # generate unique filename
    filename = f"{uuid.uuid4().hex}.png"
    file_path = os.path.join(UPLOAD_DIR, filename)

    # write file to disk
    with open(file_path, "wb") as f:
        f.write(file.file.read())

    return file_path