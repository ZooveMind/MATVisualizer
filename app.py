# GENERIC MAT ACCESS
from flask import Flask, render_template, request, jsonify
import os
import shutil
from scripts.process_mat import process_mat_file

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '' or not file.filename.endswith('.mat'):
        return jsonify({'error': 'Invalid file type. Please upload a .mat file'}), 400

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    results = process_mat_file(file_path)
    
    return render_template('results.html', results=results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)

# EBSSA FILE 
from flask import Flask, render_template, request, jsonify
import os
import shutil
from scripts.process_mat import process_mat_file
from scripts.EBVisualizer import EVizTool, load_event_file

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '' or not file.filename.endswith(('.mat', '.h5')):
        return jsonify({'error': 'Invalid file type. Please upload a .mat or .h5 file'}), 400

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    try:
        event_name, event_df, sensor_dim = load_event_file(file_path)
        eviz_obj = EVizTool(event_name, event_df, sensor_dim)
        results = eviz_obj.visualize_event_data()
    except KeyError as e:
        return jsonify({'error': str(e)}), 400
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    return render_template('results.html', results=results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)

# # import os
# # import json
# # import base64
# # from flask import Flask, request, jsonify, render_template
# # from flask_cors import CORS
# # from scripts.process_mat import process_mat_file
# # from scripts.gpt_integration import send_to_gpt, save_visualizations

# # # Initialize Flask app
# # app = Flask(__name__)
# # CORS(app)  # Enable CORS for frontend access

# # UPLOAD_FOLDER = 'uploads'
# # os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# # @app.route("/")
# # def index():
# #     return render_template("index.html")

# # @app.route("/upload", methods=["POST"])
# # def upload_file():
# #     """ Handles file uploads, processes `.mat` files, and calls GPT """
# #     if "file" not in request.files:
# #         return jsonify({"error": "No file uploaded"}), 400

# #     file = request.files["file"]
# #     file_path = os.path.join(UPLOAD_FOLDER, file.filename)
# #     file.save(file_path)

# #     # Extract relevant data from `.mat` file
# #     extracted_data = process_mat_file(file_path)
# #     if "error" in extracted_data:
# #         return jsonify(extracted_data), 400

# #     # Send processed data to GPT for analysis & visualization
# #     gpt_response = send_to_gpt(extracted_data)
# #     if "visualizations" not in gpt_response or "summary" not in gpt_response:
# #         return jsonify({"error": "GPT failed to generate insights"}), 500

# #     saved_images = save_visualizations(gpt_response["visualizations"])

# #     return jsonify({
# #         "summary": gpt_response["summary"],
# #         "images": saved_images
# #     })

# # if __name__ == "__main__":
# #     app.run(debug=True)


