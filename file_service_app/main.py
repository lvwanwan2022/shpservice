import tkinter as tk
from tkinter import filedialog, messagebox
import os
import sys
import threading
from flask import Flask, request, send_from_directory, abort, Response, render_template_string, redirect, url_for, session, jsonify  # Add jsonify
from flask_cors import CORS  # Add CORS import
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
import shutil
from functools import wraps
import pystray  # Add for system tray
from PIL import Image  # Add for icon image
import io  # For creating icon image
import requests  # Add this import

# Global variables for config
CONFIG = {}
server_thread = None  # To hold the server thread
stop_event = threading.Event()  # Event to signal server stop

def get_folder_size_mb(folder_path):
    """Calculate total size of folder in MB."""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if os.path.exists(filepath):
                total_size += os.path.getsize(filepath)
    return total_size / (1024 * 1024)

def check_disk_usage(path, file_size_mb, max_size_mb):
    """Check if adding a file would exceed max capacity."""
    current_size_mb = get_folder_size_mb(path)
    return (current_size_mb + file_size_mb) <= max_size_mb

def create_gui():
    root = tk.Tk()
    root.title("文件服务设置")  # 汉化标题

    # Port
    tk.Label(root, text="端口:").grid(row=0, column=0)
    port_entry = tk.Entry(root)
    port_entry.grid(row=0, column=1)
    port_entry.insert(0, "5055")

    # Folder
    tk.Label(root, text="文件夹路径:").grid(row=1, column=0)
    folder_entry = tk.Entry(root)
    folder_entry.grid(row=1, column=1)
    tk.Button(root, text="浏览", command=lambda: folder_entry.insert(0, filedialog.askdirectory())).grid(row=1, column=2)  # 汉化按钮

    # Max Capacity (MB)
    tk.Label(root, text="最大容量 (MB):").grid(row=2, column=0)
    max_size_entry = tk.Entry(root)
    max_size_entry.grid(row=2, column=1)
    max_size_entry.insert(0, "1024")

    # Username
    tk.Label(root, text="用户名:").grid(row=3, column=0)
    user_entry = tk.Entry(root)
    user_entry.grid(row=3, column=1)
    user_entry.insert(0, "admin")

    # Password
    tk.Label(root, text="密码:").grid(row=4, column=0)
    pass_entry = tk.Entry(root, show="*")
    pass_entry.grid(row=4, column=1)

    # API Key (optional)
    tk.Label(root, text="API密钥 (可选):").grid(row=5, column=0)
    api_key_entry = tk.Entry(root)
    api_key_entry.grid(row=5, column=1)

    def start_server():
        global CONFIG
        try:
            CONFIG['port'] = int(port_entry.get())
            CONFIG['folder'] = folder_entry.get()
            CONFIG['max_size_mb'] = float(max_size_entry.get())
            CONFIG['username'] = user_entry.get()
            CONFIG['password_hash'] = generate_password_hash(pass_entry.get())
            CONFIG['api_key'] = api_key_entry.get() if api_key_entry.get() else None
            
            if not os.path.exists(CONFIG['folder']):
                os.makedirs(CONFIG['folder'])
            
            root.destroy()
        except ValueError as e:
            messagebox.showerror("错误", f"无效输入: {e}")  # 汉化错误消息
            return

    tk.Button(root, text="启动服务", command=start_server).grid(row=6, column=1)  # 汉化按钮
    root.mainloop()

    if not CONFIG:
        sys.exit(0)

# Flask app
app = Flask(__name__)
app.secret_key = 'super_secret_key'  # For session
CORS(app) # Enable CORS for all routes

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def requires_api_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Check for session-based auth first
        if 'logged_in' in session:
            return f(*args, **kwargs)
        
        # Check for basic auth for API access
        auth = request.authorization
        if auth and auth.username == CONFIG['username'] and check_password_hash(CONFIG['password_hash'], auth.password):
            return f(*args, **kwargs)
        
        # Check for API key in headers
        api_key = request.headers.get('X-API-Key')
        if api_key and api_key == CONFIG.get('api_key', ''):
            return f(*args, **kwargs)
            
        return jsonify({'error': 'Authentication required'}), 401
    return decorated

@app.route('/upload', methods=['POST'])
@requires_api_auth
def upload_file():
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400
    
    filename = secure_filename(file.filename)
    file_path = os.path.join(CONFIG['folder'], filename)
    
    # Get exact file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Reset position
    file_size_mb = file_size / (1024 * 1024)

    # Check capacity
    if not check_disk_usage(CONFIG['folder'], file_size_mb, CONFIG['max_size_mb']):
        return jsonify({'message': 'Exceeded max capacity'}), 507
    
    file.save(file_path)
    return jsonify({'message': 'File uploaded successfully'}), 200

@app.route('/files/<filename>', methods=['GET'])
@requires_api_auth
def download_file(filename):
    try:
        return send_from_directory(CONFIG['folder'], filename)
    except FileNotFoundError:
        abort(404)

@app.route('/list', methods=['GET'])
@requires_api_auth
def list_files():
    files = os.listdir(CONFIG['folder'])
    return jsonify({'files': files}), 200

# API endpoints for external systems
@app.route('/api/status', methods=['GET'])
@requires_api_auth
def api_status():
    """Get server status and storage information."""
    current_size_mb = get_folder_size_mb(CONFIG['folder'])
    file_count = len(os.listdir(CONFIG['folder']))
    
    return jsonify({
        'status': 'online',
        'storage': {
            'used_mb': round(current_size_mb, 2),
            'max_mb': CONFIG['max_size_mb'],
            'used_percentage': round((current_size_mb / CONFIG['max_size_mb']) * 100, 1),
            'available_mb': round(CONFIG['max_size_mb'] - current_size_mb, 2)
        },
        'file_count': file_count
    }), 200

@app.route('/api/files', methods=['GET'])
@requires_api_auth
def api_list_files():
    """Get detailed file list with metadata."""
    files = []
    for filename in os.listdir(CONFIG['folder']):
        file_path = os.path.join(CONFIG['folder'], filename)
        if os.path.isfile(file_path):
            stat = os.stat(file_path)
            files.append({
                'name': filename,
                'size_bytes': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'modified': stat.st_mtime,
                'download_url': f'/files/{filename}'
            })
    
    return jsonify({
        'files': files,
        'total_count': len(files),
        'total_size_mb': round(sum(f['size_mb'] for f in files), 2)
    }), 200

@app.route('/api/upload', methods=['POST'])
@requires_api_auth
def api_upload_file():
    """Upload file via API with detailed response."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in request'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    filename = secure_filename(file.filename)
    file_path = os.path.join(CONFIG['folder'], filename)
    
    # Check if file already exists
    if os.path.exists(file_path):
        return jsonify({'error': f'File {filename} already exists'}), 409
    
    # Get exact file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    file_size_mb = file_size / (1024 * 1024)
    
    # Check capacity
    if not check_disk_usage(CONFIG['folder'], file_size_mb, CONFIG['max_size_mb']):
        return jsonify({
            'error': 'Upload would exceed maximum capacity',
            'file_size_mb': round(file_size_mb, 2),
            'available_mb': round(CONFIG['max_size_mb'] - get_folder_size_mb(CONFIG['folder']), 2)
        }), 507
    
    try:
        file.save(file_path)
        return jsonify({
            'message': 'File uploaded successfully',
            'filename': filename,
            'size_mb': round(file_size_mb, 2),
            'download_url': f'/files/{filename}'
        }), 201
    except Exception as e:
        return jsonify({'error': f'Failed to save file: {str(e)}'}), 500

@app.route('/api/files/<filename>', methods=['DELETE'])
@requires_api_auth
def api_delete_file(filename):
    """Delete a file via API."""
    file_path = os.path.join(CONFIG['folder'], secure_filename(filename))
    
    if not os.path.exists(file_path):
        return jsonify({'error': f'File {filename} not found'}), 404
    
    try:
        os.remove(file_path)
        return jsonify({
            'message': f'File {filename} deleted successfully'
        }), 200
    except Exception as e:
        return jsonify({'error': f'Failed to delete file: {str(e)}'}), 500

# Login page
@app.route('/', methods=['GET'])
def login():
    return render_template_string('''
    <!doctype html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>文件服务登录</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .login-container {
                background: rgba(255, 255, 255, 0.95);
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
                backdrop-filter: blur(10px);
                max-width: 400px;
                width: 100%;
                margin: 20px;
            }
            
            h1 {
                color: #333;
                margin-bottom: 30px;
                font-size: 28px;
                font-weight: 600;
                text-align: center;
            }
            
            .form-group {
                margin-bottom: 20px;
            }
            
            input[type="text"], input[type="password"] {
                width: 100%;
                padding: 15px;
                border: 2px solid #e1e1e1;
                border-radius: 10px;
                font-size: 16px;
                transition: all 0.3s ease;
                background: #f8f9fa;
            }
            
            input[type="text"]:focus, input[type="password"]:focus {
                outline: none;
                border-color: #667eea;
                background: white;
                box-shadow: 0 0 10px rgba(102, 126, 234, 0.2);
            }
            
            input[type="submit"] {
                width: 100%;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px;
                border: none;
                border-radius: 10px;
                font-size: 18px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                margin-top: 10px;
            }
            
            input[type="submit"]:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
            }
            
            .logo {
                text-align: center;
                margin-bottom: 20px;
                font-size: 48px;
                color: #667eea;
            }
        </style>
    </head>
    <body>
        <div class="login-container">
            <div class="logo">📁</div>
            <h1>文件服务登录</h1>
            <form method="post" action="{{ url_for('do_login') }}">
                <div class="form-group">
                    <input type="text" name="username" placeholder="用户名" required>
                </div>
                <div class="form-group">
                    <input type="password" name="password" placeholder="密码" required>
                </div>
                <input type="submit" value="登录">
            </form>
        </div>
    </body>
    </html>
    ''')

@app.route('/login', methods=['POST'])
def do_login():
    username = request.form['username']
    password = request.form['password']
    if username == CONFIG['username'] and check_password_hash(CONFIG['password_hash'], password):
        session['logged_in'] = True
        return redirect(url_for('file_list'))
    else:
        return render_template_string('''
        <!doctype html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>登录失败</title>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .error-container {
                    background: rgba(255, 255, 255, 0.95);
                    border-radius: 20px;
                    padding: 40px;
                    text-align: center;
                    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
                    max-width: 400px;
                    width: 100%;
                    margin: 20px;
                }
                .error-icon {
                    font-size: 48px;
                    color: #e53e3e;
                    margin-bottom: 20px;
                }
                h1 {
                    color: #e53e3e;
                    margin-bottom: 20px;
                }
                p {
                    color: #666;
                    margin-bottom: 30px;
                }
                .back-btn {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 15px 30px;
                    text-decoration: none;
                    border-radius: 10px;
                    font-weight: 600;
                    transition: all 0.3s ease;
                }
                .back-btn:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
                    color: white;
                    text-decoration: none;
                }
            </style>
        </head>
        <body>
            <div class="error-container">
                <div class="error-icon">🚫</div>
                <h1>登录失败</h1>
                <p>用户名或密码错误，请重试</p>
                <a href="{{ url_for('login') }}" class="back-btn">返回登录</a>
            </div>
            <script>
                setTimeout(function() {
                    window.location.href = "{{ url_for('login') }}";
                }, 3000);
            </script>
        </body>
        </html>
        '''), 401

# File list page with upload and download
@app.route('/files', methods=['GET', 'POST'])
@requires_auth
def file_list():
    error = None
    if request.method == 'POST':
        if 'file' not in request.files:
            error = '没有文件部分'
        else:
            file = request.files['file']
            if file.filename == '':
                error = '没有选择文件'
            else:
                filename = secure_filename(file.filename)
                file_path = os.path.join(CONFIG['folder'], filename)
                
                # Get exact file size
                file.seek(0, os.SEEK_END)
                file_size = file.tell()
                file.seek(0)  # Reset position
                file_size_mb = file_size / (1024 * 1024)
                
                # Check capacity
                current_used_mb = get_folder_size_mb(CONFIG['folder'])
                if current_used_mb + file_size_mb > CONFIG['max_size_mb']:
                    error = '上传将超过最大容量'
                else:
                    file.save(file_path)
                    return redirect(url_for('file_list'))
    
    files = os.listdir(CONFIG['folder'])
    file_list_html = '<ul>' + ''.join(f'<li><a href="/files/{f}" download>{f}</a></li>' for f in files) + '</ul>'
    
    # Calculate storage info
    current_size_mb = get_folder_size_mb(CONFIG['folder'])
    used_percentage = (current_size_mb / CONFIG['max_size_mb']) * 100
    
    return render_template_string('''
    <!doctype html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>文件管理系统</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: #f5f7fa;
                min-height: 100vh;
                color: #333;
            }
            
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px 0;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 0 20px;
            }
            
            .header h1 {
                text-align: center;
                font-size: 32px;
                font-weight: 600;
            }
            
            .main-content {
                padding: 40px 20px;
                max-width: 1200px;
                margin: 0 auto;
            }
            
            .storage-info {
                background: white;
                border-radius: 15px;
                padding: 25px;
                margin-bottom: 30px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            }
            
            .storage-bar {
                background: #e1e5e9;
                border-radius: 10px;
                height: 20px;
                margin: 15px 0;
                overflow: hidden;
            }
            
            .storage-used {
                background: linear-gradient(90deg, #667eea, #764ba2);
                height: 100%;
                border-radius: 10px;
                transition: width 0.3s ease;
            }
            
            .upload-section {
                background: white;
                border-radius: 15px;
                padding: 30px;
                margin-bottom: 30px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            }
            
            .upload-area {
                border: 3px dashed #667eea;
                border-radius: 15px;
                padding: 40px;
                text-align: center;
                background: #f8f9ff;
                transition: all 0.3s ease;
                cursor: pointer;
            }
            
            .upload-area:hover {
                background: #f0f2ff;
                border-color: #5a67d8;
            }
            
            .upload-icon {
                font-size: 48px;
                color: #667eea;
                margin-bottom: 20px;
            }
            
            input[type="file"] {
                display: none;
            }
            
            .file-label {
                display: inline-block;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px 30px;
                border-radius: 10px;
                cursor: pointer;
                font-size: 16px;
                font-weight: 600;
                transition: all 0.3s ease;
                margin-bottom: 20px;
            }
            
            .file-label:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
            }
            
            .upload-btn {
                background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
                color: white;
                padding: 15px 30px;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                margin-left: 15px;
            }
            
            .upload-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(72, 187, 120, 0.3);
            }
            
            .files-section {
                background: white;
                border-radius: 15px;
                padding: 30px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            }
            
            .files-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }
            
            .file-card {
                background: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 12px;
                padding: 20px;
                transition: all 0.3s ease;
                text-align: center;
            }
            
            .file-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
                background: white;
            }
            
            .file-icon {
                font-size: 40px;
                margin-bottom: 15px;
                color: #667eea;
            }
            
            .file-name {
                font-weight: 600;
                margin-bottom: 15px;
                word-break: break-word;
                color: #333;
            }
            
            .download-btn {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 10px 20px;
                text-decoration: none;
                border-radius: 8px;
                display: inline-block;
                font-weight: 500;
                transition: all 0.3s ease;
            }
            
            .download-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 15px rgba(102, 126, 234, 0.3);
                color: white;
                text-decoration: none;
            }
            
            .error {
                background: #fed7d7;
                border: 1px solid #feb2b2;
                color: #c53030;
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 20px;
                text-align: center;
                font-weight: 600;
            }
            
            .success {
                background: #c6f6d5;
                border: 1px solid #9ae6b4;
                color: #2d7d32;
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 20px;
                text-align: center;
                font-weight: 600;
            }
            
            .logout-btn {
                position: fixed;
                top: 20px;
                right: 20px;
                background: rgba(255, 255, 255, 0.2);
                color: white;
                padding: 10px 20px;
                text-decoration: none;
                border-radius: 25px;
                font-weight: 500;
                transition: all 0.3s ease;
                backdrop-filter: blur(10px);
            }
            
            .logout-btn:hover {
                background: rgba(255, 255, 255, 0.3);
                color: white;
                text-decoration: none;
            }
            
            .section-title {
                font-size: 24px;
                font-weight: 600;
                margin-bottom: 20px;
                color: #333;
            }
            
            .stats {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
            }
            
            @media (max-width: 768px) {
                .files-grid {
                    grid-template-columns: 1fr;
                }
                
                .main-content {
                    padding: 20px 10px;
                }
                
                .upload-area {
                    padding: 20px;
                }
                
                .file-label, .upload-btn {
                    display: block;
                    margin: 10px 0;
                }
            }
        </style>
    </head>
    <body>
        <div class="header">
            <div class="container">
                <h1>📁 文件管理系统</h1>
            </div>
        </div>
        
        <a href="{{ url_for('logout') }}" class="logout-btn">🚪 登出</a>
        
        <div class="main-content">
            {% if error %}
                <div class="error">❌ {{ error }}</div>
            {% endif %}
            
            <div class="storage-info">
                <h2 class="section-title">💾 存储空间</h2>
                <div class="stats">
                    <span>已使用: {{ "%.2f"|format(current_size) }} MB</span>
                    <span>总容量: {{ max_size }} MB</span>
                    <span>使用率: {{ "%.1f"|format(used_percentage) }}%</span>
                </div>
                <div class="storage-bar">
                    <div class="storage-used" style="width: {{ used_percentage }}%"></div>
                </div>
            </div>
            
            <div class="upload-section">
                <h2 class="section-title">📤 上传文件</h2>
                <form method="post" enctype="multipart/form-data" id="uploadForm">
                    <div class="upload-area" onclick="document.getElementById('fileInput').click()">
                        <div class="upload-icon">☁️</div>
                        <label for="fileInput" class="file-label">选择文件</label>
                        <input type="file" name="file" id="fileInput" onchange="showFileName()">
                        <div id="fileName" style="margin-top: 10px; color: #666;"></div>
                        <div style="margin-top: 20px;">
                            <button type="submit" class="upload-btn">🚀 开始上传</button>
                        </div>
                    </div>
                </form>
            </div>
            
            <div class="files-section">
                <h2 class="section-title">📋 文件列表 ({{ file_count }} 个文件)</h2>
                {% if files %}
                    <div class="files-grid">
                        {% for file in files %}
                            <div class="file-card">
                                <div class="file-icon">📄</div>
                                <div class="file-name">{{ file }}</div>
                                <a href="/files/{{ file }}" class="download-btn" download>⬇️ 下载</a>
                            </div>
                        {% endfor %}
                    </div>
                {% else %}
                    <div style="text-align: center; padding: 40px; color: #666;">
                        <div style="font-size: 48px; margin-bottom: 20px;">📂</div>
                        <p>暂无文件，请上传第一个文件</p>
                    </div>
                {% endif %}
            </div>
        </div>
        
        <script>
            function showFileName() {
                const input = document.getElementById('fileInput');
                const fileName = document.getElementById('fileName');
                if (input.files.length > 0) {
                    fileName.textContent = '已选择: ' + input.files[0].name;
                } else {
                    fileName.textContent = '';
                }
            }
        </script>
    </body>
    </html>
    ''', error=error, files=files, file_count=len(files), 
        current_size=current_size_mb, max_size=CONFIG['max_size_mb'], 
        used_percentage=used_percentage)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

def run_server():
    app.run(host='0.0.0.0', port=CONFIG['port'], threaded=True, use_reloader=False)
    # No join here, we'll manage in main

def stop_server():
    # Signal to stop the server
    stop_event.set()
    # To gracefully shutdown Flask, we can make a request to a shutdown endpoint if implemented, but for simplicity, we'll just let the thread run and exit on program close
    # Note: Flask doesn't have built-in shutdown, so we'll add a shutdown route

@app.route('/shutdown', methods=['POST'])
@requires_auth
def shutdown():
    request.environ.get('werkzeug.server.shutdown')()  # This works if not in production mode
    return 'Server shutting down...', 200

if __name__ == '__main__':
    create_gui()
    if not CONFIG:
        sys.exit(0)
    
    # Start server in thread
    server_thread = threading.Thread(target=run_server)
    server_thread.start()
    
    # Create system tray icon
    def create_image():
        # Simple icon (red circle)
        image = Image.new('RGB', (64, 64), color=(255, 0, 0))
        return image
    
    def on_stop(icon, item):
        # Stop the server
        try:
            requests.post(f"http://localhost:{CONFIG['port']}/shutdown", auth=(CONFIG['username'], 'password'))  # Need actual password, but for demo
        except:
            pass  # If fails, force stop
        icon.stop()
        os._exit(0)
    

    
    icon = pystray.Icon('file_service')
    icon.icon = create_image()
    icon.title = "文件服务"  # 汉化标题
    icon.menu = pystray.Menu(
        pystray.MenuItem("停止服务", on_stop),  # 汉化菜单项
    )
    
    # Run tray in separate thread or main
    tray_thread = threading.Thread(target=icon.run)
    tray_thread.start()
    
    # Show startup message
    messagebox.showinfo("服务已启动", f"文件服务运行在端口 {CONFIG['port']}\n文件夹: {CONFIG['folder']}\n请查看系统托盘进行控制。")  # 汉化消息
    
    # Wait for threads
    server_thread.join()
    tray_thread.join() 