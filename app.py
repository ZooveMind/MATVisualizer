import os
import datetime
from flask import Flask, request, jsonify
from scripts.process_mat import process_mat_file
from scripts.EBVisualizer import EVizTool, load_event_file
from flask_cors import CORS
import time
import threading
import uuid


app = Flask(__name__,static_folder='static')
CORS(app)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

LOGS_FOLDER = 'logs'
app.config['LOGS_FOLDER'] = LOGS_FOLDER

# app.config['SERVER_NAME'] = '192.168.1.13:5000'

@app.route('/')
def index():
    return "Hello from Flask on Render!"


def cleanup_files(paths, delay):
    """
    Delete the given file paths after 'delay' seconds.
    Spawns a background thread so it won't block the main request.
    """
    def remove_later():
        time.sleep(delay)
        for p in paths:
            if os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass  # ignore if already removed or no permissions

    thread = threading.Thread(target=remove_later, daemon=True)
    thread.start()

@app.route('/upload', methods=['POST'])
def upload_file():
    # 1) Receives file from client check for file and mode(how to process 0-ebssa 1-generic)
    start_time = datetime.now()

    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '' or not file.filename.endswith(('.mat', '.h5')):
        return jsonify({'error': 'Invalid file type. Please upload a .mat .h5 file'}), 400

    mode_str = request.form.get('mode', None)
    if mode_str is None:
        return jsonify({'error': 'No mode provided'}), 400
    # Convert mode to integer
    mode = int(mode_str)
    if mode not in (0,1):
        return jsonify({'error': 'No valid mode provided'}), 400

    userName = request.form.get("userName",None)
    if userName is None:
        return jsonify({'error': 'No userName found'}), 400
    
    fileSize = request.form.get("fileSize")
    
    # 2) Create a new subfolder named by today's date (e.g. "2025-02-24")
    date_str = datetime.datetime.now().strftime('%Y-%m-%d')
    date_folder = os.path.join(app.config['UPLOAD_FOLDER'], date_str)
    if not os.path.exists(date_folder):
        os.makedirs(date_folder)

    # 3) Create a new subfolder named by today's date for log files (e.g. "2025-02-24")
    LogDate_folder = os.path.join(app.config['LOGS_FOLDER'], date_str)
    if not os.path.exists(LogDate_folder):
        os.makedirs(LogDate_folder)  

    job_id = str(uuid.uuid4())
    
    # 4) Rename file to include a timestamp (e.g. "originalname_14-30-00_USERID.ext")
    #TODO REMBER TO ADD USERID
    time_str = datetime.datetime.now().strftime('%H-%M-%S')
    original_name, ext = os.path.splitext(file.filename)
    new_filename = f"{original_name}_{time_str}{ext}"

    file_path = os.path.join(date_folder, new_filename)
    file.save(file_path)

    #without strong the files
    # file_content = file.read()
    # file_bytes = BytesIO(file_content)
    # filename = file.filename
    # ext = os.path.splitext(filename)[1].lower()

    if mode == 0:
        #ebssa logic
        try:                   
            event_name, event_df, sensor_dim = load_event_file(file_path)
            eviz_obj = EVizTool(event_name, event_df, sensor_dim)
            results = eviz_obj.visualize_event_data()
        except KeyError as e:
            return jsonify({'error': str(e)}), 400
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
    elif mode== 1:
        # GENERIC logic
        results = process_mat_file(file_path)
    
    files_to_remove = []
    files_to_remove.append(file_path)
    # add each generated image for clean up process
    for r in results:
        if 'file_pathLocal' in r and r['file_pathLocal']:
            files_to_remove.append(r['file_pathLocal'])

    cleanup_files(files_to_remove, delay=300)

    # log file generated
    end_time = datetime.now()
    log_filename = os.path.join(LogDate_folder, f'{job_id+"_"+userName}.log')
    with open(log_filename, 'a', encoding='utf-8') as logf:
        logf.write(f"=== Job Log ===\n")
        logf.write(f"User Name   : {userName}\n")
        logf.write(f"Job ID      : {job_id}\n")
        logf.write(f"Start Time  : {start_time}\n")
        logf.write(f"End Time    : {end_time}\n")
        logf.write(f"File Type   : {ext}\n")
        logf.write(f"File size   : {fileSize}\n")
        logf.write(f"--------------\n\n")

    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0', port=5000)


    """
   
    if mode == 0:
        #ebssa logic
        try:
            if ext == '.mat':
                file_bytes.seek(0)
                mat_data = scipy.io.loadmat(file_bytes)
                event_name, event_df, sensor_dim = load_event_file(mat_data)
            elif ext in ('.h5', '.hdf5'):
                file_bytes.seek(0)
                with h5py.File(file_bytes, 'r') as h5file:
                    event_name, event_df, sensor_dim = load_event_file(h5file)

            eviz_obj = EVizTool(event_name, event_df, sensor_dim)
            results = eviz_obj.visualize_event_data()
        except KeyError as e:
            return jsonify({'error': str(e)}), 400
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
    elif mode== 1:
        # GENERIC logic
        if ext == '.mat':
            file_bytes.seek(0)
            mat_data = scipy.io.loadmat(file_bytes)
            results = process_mat_file(mat_data)
        elif ext in ('.h5', '.hdf5'):
            file_bytes.seek(0)
            with h5py.File(file_bytes, 'r') as h5file:
                results = process_mat_file(h5file)
     """
    # return "got it",200
    # return render_template('results.html', results=results)

    
# EBSSA FILE 
# from flask import Flask, render_template, request, jsonify
# import os
# import shutil
# from scripts.process_mat import process_mat_file
# from scripts.EBVisualizer import EVizTool, load_event_file

# app = Flask(__name__)

# UPLOAD_FOLDER = 'uploads'
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# @app.route('/')
# def index():
#     return render_template('index.html')

# @app.route('/upload', methods=['POST'])
# def upload_file():
#     if 'file' not in request.files:
#         return jsonify({'error': 'No file uploaded'}), 400

#     file = request.files['file']
#     if file.filename == '' or not file.filename.endswith(('.mat', '.h5')):
#         return jsonify({'error': 'Invalid file type. Please upload a .mat or .h5 file'}), 400

#     file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
#     file.save(file_path)

#     try:
#         event_name, event_df, sensor_dim = load_event_file(file_path)
#         eviz_obj = EVizTool(event_name, event_df, sensor_dim)
#         results = eviz_obj.visualize_event_data()
#     except KeyError as e:
#         return jsonify({'error': str(e)}), 400
#     except ValueError as e:
#         return jsonify({'error': str(e)}), 400

#     return render_template('results.html', results=results)

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=8000, debug=True)

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


