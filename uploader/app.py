from flask import Flask, request, jsonify
import os
import magic  # pip install python-magic
import time
from uploader.settings import DEFAULT_UPLOAD_FOLDER, DEFAULT_BASE_URL, DEFAULT_API_KEY, DEFAULT_ALLOWED_MIME_TYPES, DEFAULT_CLEANUP_THRESHOLD_SECONDS, DEFAULT_ALLOW_REWRITE

# Configuration from environment variables or fallback to settings.py
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', DEFAULT_UPLOAD_FOLDER)
app.config['BASE_URL'] = os.getenv('BASE_URL', DEFAULT_BASE_URL)
app.config['API_KEY'] = os.getenv('API_KEY', DEFAULT_API_KEY)
app.config['ALLOWED_MIME_TYPES'] = os.getenv('ALLOWED_MIME_TYPES', ','.join(DEFAULT_ALLOWED_MIME_TYPES)).split(',')
app.config['CLEANUP_THRESHOLD_SECONDS'] = int(os.getenv('CLEANUP_THRESHOLD_SECONDS', DEFAULT_CLEANUP_THRESHOLD_SECONDS))
app.config['ALLOW_REWRITE'] = os.getenv('ALLOW_REWRITE', DEFAULT_ALLOW_REWRITE)


# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_mime_type(file_path):
    mime = magic.Magic(mime=True)
    mime_type = mime.from_file(file_path)
    return mime_type in app.config['ALLOWED_MIME_TYPES']

def cleanup_old_files():
    now = time.time()
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.isfile(file_path):
            file_age = now - os.path.getmtime(file_path)
            if file_age > app.config['CLEANUP_THRESHOLD_SECONDS']:
                os.remove(file_path)

@app.route('/upload', methods=['POST'])
def upload_file():
    # Perform cleanup before handling the upload
    cleanup_old_files()

    # Check for API-KEY header
    x_api_key = request.headers.get('X-API-KEY')

    if x_api_key != app.config['API_KEY']:
        return jsonify({'error': 'Unauthorized: Invalid API-KEY'}), 401

    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected for uploading'}), 400

    # Temporarily save the file to check its MIME type
    temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_{file.filename}")
    try:
        file.save(temp_path)
    except Exception as e:
        return jsonify({'error': f'Failed to save file for validation: {str(e)}'}), 500

    # Validate the file's MIME type
    if not allowed_mime_type(temp_path):
        os.remove(temp_path)  # Clean up the temporary file
        return jsonify({'error': f'File type not allowed. Allowed file types {",".join(app.config["ALLOWED_MIME_TYPES"])}' }), 400

    # Rename and move the validated file
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)

    #Checking for allow_rewrite setting and destination file already existing
    if not app.config['ALLOW_REWRITE'] and os.path.exists(file_path):
        os.remove(temp_path)  # Clean up the temporary file
        return jsonify({'error': 'Destination file already exist'}), 400
    else:
        os.rename(temp_path, file_path)

    # Generate the download URL
    download_url = f"{app.config['BASE_URL']}/{file.filename}"

    return jsonify({'message': 'File successfully uploaded', 'download_url': download_url}), 200


