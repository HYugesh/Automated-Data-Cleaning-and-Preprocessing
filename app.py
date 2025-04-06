from flask import Flask, render_template, request, jsonify, send_file
from data_cleaner import DataCleaner
import os
import tempfile
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
app.config['CLEANED_FOLDER'] = 'cleaned_data'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB limit

# Ensure cleaned data folder exists
os.makedirs(app.config['CLEANED_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sign')
def sign():
    return render_template('sign.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    import numpy as np  # Add import here to avoid confusion

    def make_json_safe(obj):
        if isinstance(obj, dict):
            return {k: make_json_safe(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [make_json_safe(elem) for elem in obj]
        elif isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj

    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        cleaner = DataCleaner(filepath)
        cleaned_df, report = cleaner.clean_data()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        cleaned_filename = f"cleaned_{os.path.splitext(filename)[0]}_{timestamp}.csv"
        cleaned_path = os.path.join(app.config['CLEANED_FOLDER'], cleaned_filename)
        cleaned_df.to_csv(cleaned_path, index=False)

        preview_data = cleaned_df.head(20).to_dict('records')

        # 🔧 Make JSON-safe versions of report & preview
        safe_report = make_json_safe(report)
        safe_preview = make_json_safe(preview_data)

        response = {
            'status': 'success',
            'report': safe_report,
            'preview': safe_preview,
            'cleaned_filename': cleaned_filename
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download(filename):
    try:
        cleaned_path = os.path.join(app.config['CLEANED_FOLDER'], filename)
        
        if not os.path.exists(cleaned_path):
            return jsonify({'error': 'File not found'}), 404
            
        return send_file(
            cleaned_path,
            as_attachment=True,
            download_name=f"cleaned_{filename}",
            mimetype='text/csv'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)