# app.py
import os
from flask import Flask, render_template, request, redirect, url_for
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
from models import db, OCRResult
import pytesseract
from PIL import Image
from datetime import datetime

UPLOAD_FOLDER = 'static/uploads'

app = Flask(__name__)
app.config.from_object('config.Config')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db.init_app(app)
migrate = Migrate(app, db)

# Buat tabel di database saat pertama kali dijalankan
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    results = OCRResult.query.all()
    return render_template('index.html', results=results)

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['image']
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    text = pytesseract.image_to_string(Image.open(filepath))

    new_result = OCRResult(image_filename=filename, extracted_text=text)
    db.session.add(new_result)
    db.session.commit()

    return redirect(url_for('index'))

@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        file = request.files['image']
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        text = pytesseract.image_to_string(Image.open(filepath))

        new_result = OCRResult(
            image_filename=filename,
            extracted_text=text,
            date_created=datetime.now()
        )
        db.session.add(new_result)
        db.session.commit()

        return redirect(url_for('index'))
    return render_template('create.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    result = OCRResult.query.get_or_404(id)
    if request.method == 'POST':
        # Jika file baru diunggah
        if 'image' in request.files and request.files['image'].filename != '':
            # Hapus file lama
            old_filepath = os.path.join(app.config['UPLOAD_FOLDER'], result.image_filename)
            if os.path.exists(old_filepath):
                os.remove(old_filepath)

            # Simpan file baru
            file = request.files['image']
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Perbarui data file
            result.image_filename = filename
            result.extracted_text = pytesseract.image_to_string(Image.open(filepath))

        # Perbarui tanggal input
        result.date_created = datetime.now()

        # Simpan perubahan ke database
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('edit.html', result=result)

@app.route('/delete/<int:id>', methods=['GET', 'POST'])
def delete(id):
    result = OCRResult.query.get_or_404(id)
    if request.method == 'POST':
        # Hapus file dari sistem
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], result.image_filename))

        # Hapus data dari database
        db.session.delete(result)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('delete.html', result=result)

#Ekstrak Teks Proses
@app.route('/extract-text', methods=['POST'])
def extract_text():
    if 'image' not in request.files:
        return {'error': 'No file uploaded'}, 400

    file = request.files['image']
    if file.filename == '':
        return {'error': 'No file selected'}, 400

    try:
        # Simpan file sementara
        filename = secure_filename(file.filename)
        temp_filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_{filename}")
        file.save(temp_filepath)

        # Ekstraksi teks menggunakan pytesseract
        extracted_text = pytesseract.image_to_string(Image.open(temp_filepath))

        # Hapus file sementara
        os.remove(temp_filepath)

        return {'extracted_text': extracted_text}, 200
    except Exception as e:
        return {'error': str(e)}, 500

if __name__ == '__main__':
    app.run(debug=True)
