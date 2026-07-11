import os
import uuid
from flask import Flask, request, send_from_directory, render_template_string, jsonify

app = Flask(__name__)
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024 * 1024  # 50 GB limit

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Catbox Clone</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-dark: #0f172a;
            --glass-bg: rgba(30, 41, 59, 0.7);
            --glass-border: rgba(255, 255, 255, 0.1);
            --accent: #3b82f6;
            --accent-hover: #60a5fa;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
        }
        body {
            margin: 0;
            padding: 0;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background: radial-gradient(circle at top right, #1e1b4b, var(--bg-dark));
            font-family: 'Inter', sans-serif;
            color: var(--text-main);
        }
        .container {
            width: 100%;
            max-width: 500px;
            padding: 2.5rem;
            background: var(--glass-bg);
            backdrop-filter: blur(12px);
            border: 1px solid var(--glass-border);
            border-radius: 24px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            text-align: center;
            transition: transform 0.3s ease;
        }
        .container:hover {
            transform: translateY(-5px);
        }
        h1 {
            font-weight: 800;
            font-size: 2rem;
            margin-bottom: 0.5rem;
            background: linear-gradient(to right, #38bdf8, #818cf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        p {
            color: var(--text-muted);
            margin-bottom: 2rem;
        }
        .upload-area {
            border: 2px dashed var(--glass-border);
            border-radius: 16px;
            padding: 3rem 1.5rem;
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
        }
        .upload-area:hover, .upload-area.dragover {
            border-color: var(--accent);
            background: rgba(59, 130, 246, 0.1);
        }
        .upload-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
        }
        #fileInput {
            display: none;
        }
        .btn {
            background: var(--accent);
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            font-weight: 600;
            font-family: 'Inter', sans-serif;
            cursor: pointer;
            transition: background 0.3s ease;
            margin-top: 1.5rem;
            width: 100%;
            font-size: 1rem;
        }
        .btn:hover {
            background: var(--accent-hover);
        }
        .btn:disabled {
            background: var(--text-muted);
            cursor: not-allowed;
        }
        #progressContainer {
            display: none;
            margin-top: 1.5rem;
        }
        .progress-bar-bg {
            background: var(--glass-border);
            height: 8px;
            border-radius: 4px;
            overflow: hidden;
            margin-bottom: 0.5rem;
        }
        .progress-bar-fill {
            background: linear-gradient(90deg, #38bdf8, #818cf8);
            height: 100%;
            width: 0%;
            transition: width 0.2s ease;
        }
        #result {
            margin-top: 1.5rem;
            padding: 1rem;
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.2);
            border-radius: 12px;
            display: none;
            word-break: break-all;
        }
        #result a {
            color: #34d399;
            font-weight: 600;
            text-decoration: none;
        }
        #result a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>

<div class="container">
    <h1>Catbox Clone</h1>
    <p>Upload files of any size directly to your server</p>

    <div class="upload-area" id="dropZone" onclick="document.getElementById('fileInput').click()">
        <div class="upload-icon">☁️</div>
        <div>Click or drag & drop files here</div>
    </div>
    <input type="file" id="fileInput">
    
    <button class="btn" id="uploadBtn" disabled onclick="uploadFile()">Upload File</button>

    <div id="progressContainer">
        <div class="progress-bar-bg">
            <div class="progress-bar-fill" id="progressBar"></div>
        </div>
        <div id="progressText" style="font-size: 0.875rem; color: var(--text-muted);">0%</div>
    </div>

    <div id="result"></div>
</div>

<script>
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const uploadBtn = document.getElementById('uploadBtn');
    let selectedFile = null;

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false)
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.add('dragover'), false)
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.remove('dragover'), false)
    });

    dropZone.addEventListener('drop', (e) => {
        let dt = e.dataTransfer;
        let files = dt.files;
        if(files.length) handleFile(files[0]);
    });

    fileInput.addEventListener('change', (e) => {
        if(fileInput.files.length) handleFile(fileInput.files[0]);
    });

    function handleFile(file) {
        selectedFile = file;
        dropZone.innerHTML = `<div style="color: var(--accent-hover); font-weight: 600;">📁 ${file.name}</div><div style="font-size: 0.875rem; margin-top:0.5rem; color: var(--text-muted);">${(file.size / (1024*1024)).toFixed(2)} MB</div>`;
        uploadBtn.disabled = false;
    }

    function uploadFile() {
        if(!selectedFile) return;
        
        uploadBtn.disabled = true;
        document.getElementById('progressContainer').style.display = 'block';
        document.getElementById('result').style.display = 'none';
        
        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/api/upload', true);
        
        xhr.upload.onprogress = function(e) {
            if (e.lengthComputable) {
                const percentComplete = (e.loaded / e.total) * 100;
                document.getElementById('progressBar').style.width = percentComplete + '%';
                document.getElementById('progressText').innerText = percentComplete.toFixed(0) + '%';
            }
        };
        
        xhr.onload = function() {
            if (xhr.status === 200) {
                const res = JSON.parse(xhr.responseText);
                document.getElementById('progressContainer').style.display = 'none';
                document.getElementById('result').style.display = 'block';
                document.getElementById('result').innerHTML = `Upload successful!<br><br><a href="${res.url}" target="_blank">${res.url}</a>`;
            } else {
                alert('Upload failed!');
                uploadBtn.disabled = false;
            }
        };
        
        const formData = new FormData();
        formData.append('fileToUpload', selectedFile);
        xhr.send(formData);
    }
</script>

</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/upload', methods=['POST'])
def upload():
    if 'fileToUpload' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['fileToUpload']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    ext = os.path.splitext(file.filename)[1]
    unique_name = str(uuid.uuid4().hex)[:12] + ext
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
    file.save(file_path)
    
    host_url = request.host_url.rstrip('/')
    download_url = f"{host_url}/f/{unique_name}"
    
    return jsonify({'url': download_url})

@app.route('/f/<filename>')
def download(filename):
    # This automatically serves files inline (directly playable) exactly like Catbox.moe
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
