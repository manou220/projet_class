import os
from werkzeug.utils import secure_filename

ALLOWED_EXT = {'csv','xls','xlsx','json'}

def allowed(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXT

def save_file(file, upload_folder, filename=None):
    filename = filename or secure_filename(file.filename)
    os.makedirs(upload_folder, exist_ok=True)
    path = os.path.join(upload_folder, filename)
    file.save(path)
    return path
