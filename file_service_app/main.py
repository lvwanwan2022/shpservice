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
import hashlib  # For chunk verification
import uuid  # For upload session IDs
import re  # For filename validation
import urllib.parse  # For URL encoding Chinese filenames

# Global variables for config
CONFIG = {}
server_thread = None  # To hold the server thread
stop_event = threading.Event()  # Event to signal server stop
upload_sessions = {}  # Store active upload sessions

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

def safe_filename(filename):
    """
    Create a safe filename that supports Chinese characters.
    Remove only dangerous characters while preserving Unicode characters.
    """
    if not filename:
        return "untitled"
    
    # Remove or replace dangerous characters
    # Keep Unicode characters (including Chinese)
    # Remove: / \ : * ? " < > |
    filename = re.sub(r'[/\\:*?"<>|]', '_', filename)
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Ensure filename is not empty after cleaning
    if not filename:
        return "untitled"
    
    # Limit filename length (Windows has 255 char limit)
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[:200-len(ext)] + ext
    
    return filename

def create_gui():
    root = tk.Tk()
    root.title("文件服务设置 - 作者: @Lvwan")  # 汉化标题并添加作者信息

    # Copyright label
    copyright_label = tk.Label(root, text="© 2024 文件服务 | 作者: @Lvwan | 邮箱: 793145268@qq.com", 
                              font=("Arial", 8), fg="gray")
    copyright_label.grid(row=0, column=0, columnspan=3, pady=(5, 10))

    # Port
    tk.Label(root, text="端口:").grid(row=1, column=0)
    port_entry = tk.Entry(root)
    port_entry.grid(row=1, column=1)
    port_entry.insert(0, "5055")

    # Folder
    tk.Label(root, text="文件夹路径:").grid(row=2, column=0)
    folder_entry = tk.Entry(root)
    folder_entry.grid(row=2, column=1)
    tk.Button(root, text="浏览", command=lambda: folder_entry.insert(0, filedialog.askdirectory())).grid(row=2, column=2)  # 汉化按钮

    # Max Capacity (MB)
    tk.Label(root, text="最大容量 (MB):").grid(row=3, column=0)
    max_size_entry = tk.Entry(root)
    max_size_entry.grid(row=3, column=1)
    max_size_entry.insert(0, "10240")

    # Username
    tk.Label(root, text="用户名:").grid(row=4, column=0)
    user_entry = tk.Entry(root)
    user_entry.grid(row=4, column=1)
    user_entry.insert(0, "admin")

    # Password
    tk.Label(root, text="密码:").grid(row=5, column=0)
    pass_entry = tk.Entry(root, show="*")
    pass_entry.grid(row=5, column=1)

    # API Key (optional)
    tk.Label(root, text="API密钥 (可选):").grid(row=6, column=0)
    api_key_entry = tk.Entry(root)
    api_key_entry.grid(row=6, column=1)

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

    tk.Button(root, text="启动服务", command=start_server).grid(row=7, column=1)  # 汉化按钮
    root.mainloop()

    if not CONFIG:
        sys.exit(0)

# Flask app
app = Flask(__name__)
app.secret_key = 'super_secret_key'  # For session
app.config['JSON_AS_ASCII'] = False  # Support Chinese characters in JSON responses
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
    
    filename = safe_filename(file.filename)
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

@app.route('/files/<path:filename>', methods=['GET'])
@requires_api_auth
def download_file(filename):
    try:
        # Ensure the filename is safe (no directory traversal)
        safe_name = os.path.basename(filename)
        file_path = os.path.join(CONFIG['folder'], safe_name)
        
        # Check if file exists
        if not os.path.exists(file_path):
            abort(404)
            
        # Send file with proper Chinese filename handling
        response = send_from_directory(CONFIG['folder'], safe_name, as_attachment=True)
        
        # Set proper Content-Disposition header for Chinese filenames
        # Use RFC 5987 encoding for UTF-8 filenames
        encoded_filename = urllib.parse.quote(filename.encode('utf-8'))
        response.headers['Content-Disposition'] = f"attachment; filename*=UTF-8''{encoded_filename}"
        
        return response
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
    
    filename = safe_filename(file.filename)
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
    file_path = os.path.join(CONFIG['folder'], safe_filename(filename))
    
    if not os.path.exists(file_path):
        return jsonify({'error': f'File {filename} not found'}), 404
    
    try:
        os.remove(file_path)
        return jsonify({
            'message': f'File {filename} deleted successfully'
        }), 200
    except Exception as e:
        return jsonify({'error': f'Failed to delete file: {str(e)}'}), 500

# Chunked upload endpoints
@app.route('/api/upload/init', methods=['POST'])
@requires_api_auth
def init_chunked_upload():
    """Initialize a chunked upload session."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    filename = data.get('filename', '')
    total_size = data.get('total_size', 0)
    chunk_size = data.get('chunk_size', 1024 * 1024)  # Default 1MB chunks
    
    if not filename:
        return jsonify({'error': 'Filename is required'}), 400
    
    filename = safe_filename(filename)
    file_path = os.path.join(CONFIG['folder'], filename)
    
    # Check if file already exists
    if os.path.exists(file_path):
        return jsonify({'error': f'File {filename} already exists'}), 409
    
    # Check capacity
    total_size_mb = total_size / (1024 * 1024)
    if not check_disk_usage(CONFIG['folder'], total_size_mb, CONFIG['max_size_mb']):
        return jsonify({
            'error': 'Upload would exceed maximum capacity',
            'file_size_mb': round(total_size_mb, 2),
            'available_mb': round(CONFIG['max_size_mb'] - get_folder_size_mb(CONFIG['folder']), 2)
        }), 507
    
    # Create upload session
    upload_id = str(uuid.uuid4())
    total_chunks = (total_size + chunk_size - 1) // chunk_size
    
    upload_sessions[upload_id] = {
        'filename': filename,
        'original_filename': data.get('filename', ''),  # Keep original filename for display
        'file_path': file_path,
        'total_size': total_size,
        'chunk_size': chunk_size,
        'total_chunks': total_chunks,
        'received_chunks': set(),
        'temp_dir': os.path.join(CONFIG['folder'], f'.upload_{upload_id}')
    }
    
    # Create temporary directory for chunks
    os.makedirs(upload_sessions[upload_id]['temp_dir'], exist_ok=True)
    
    return jsonify({
        'upload_id': upload_id,
        'total_chunks': total_chunks,
        'chunk_size': chunk_size
    }), 200

@app.route('/api/upload/chunk', methods=['POST'])
@requires_api_auth
def upload_chunk():
    """Upload a single chunk."""
    upload_id = request.form.get('upload_id')
    chunk_index = request.form.get('chunk_index')
    
    if not upload_id or upload_id not in upload_sessions:
        return jsonify({'error': 'Invalid upload session'}), 400
    
    if not chunk_index:
        return jsonify({'error': 'Chunk index is required'}), 400
    
    try:
        chunk_index = int(chunk_index)
    except ValueError:
        return jsonify({'error': 'Invalid chunk index'}), 400
    
    if 'chunk' not in request.files:
        return jsonify({'error': 'No chunk data provided'}), 400
    
    chunk_file = request.files['chunk']
    session_data = upload_sessions[upload_id]
    
    # Save chunk to temporary file
    chunk_path = os.path.join(session_data['temp_dir'], f'chunk_{chunk_index}')
    chunk_file.save(chunk_path)
    
    # Mark chunk as received
    session_data['received_chunks'].add(chunk_index)
    
    # Calculate progress
    progress = len(session_data['received_chunks']) / session_data['total_chunks'] * 100
    
    return jsonify({
        'chunk_index': chunk_index,
        'progress': round(progress, 2),
        'received_chunks': len(session_data['received_chunks']),
        'total_chunks': session_data['total_chunks']
    }), 200

@app.route('/api/upload/complete', methods=['POST'])
@requires_api_auth
def complete_chunked_upload():
    """Complete the chunked upload by combining all chunks."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    upload_id = data.get('upload_id')
    
    if not upload_id or upload_id not in upload_sessions:
        return jsonify({'error': 'Invalid upload session'}), 400
    
    session_data = upload_sessions[upload_id]
    
    # Check if all chunks are received
    if len(session_data['received_chunks']) != session_data['total_chunks']:
        missing_chunks = set(range(session_data['total_chunks'])) - session_data['received_chunks']
        return jsonify({
            'error': 'Upload incomplete',
            'missing_chunks': list(missing_chunks)
        }), 400
    
    try:
        # Combine chunks into final file
        with open(session_data['file_path'], 'wb') as final_file:
            for chunk_index in range(session_data['total_chunks']):
                chunk_path = os.path.join(session_data['temp_dir'], f'chunk_{chunk_index}')
                with open(chunk_path, 'rb') as chunk_file:
                    final_file.write(chunk_file.read())
        
        # Verify file size
        actual_size = os.path.getsize(session_data['file_path'])
        if actual_size != session_data['total_size']:
            os.remove(session_data['file_path'])
            return jsonify({
                'error': 'File size mismatch',
                'expected': session_data['total_size'],
                'actual': actual_size
            }), 500
        
        # Clean up temporary files
        shutil.rmtree(session_data['temp_dir'])
        
        # Remove session
        del upload_sessions[upload_id]
        
        return jsonify({
            'message': 'File uploaded successfully',
            'filename': session_data['filename'],
            'size_mb': round(session_data['total_size'] / (1024 * 1024), 2),
            'download_url': f'/files/{session_data["filename"]}'
        }), 201
        
    except Exception as e:
        # Clean up on error
        if os.path.exists(session_data['file_path']):
            os.remove(session_data['file_path'])
        if os.path.exists(session_data['temp_dir']):
            shutil.rmtree(session_data['temp_dir'])
        if upload_id in upload_sessions:
            del upload_sessions[upload_id]
        
        return jsonify({'error': f'Failed to complete upload: {str(e)}'}), 500

@app.route('/api/upload/cancel', methods=['POST'])
@requires_api_auth
def cancel_chunked_upload():
    """Cancel an active upload session."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    upload_id = data.get('upload_id')
    
    if not upload_id or upload_id not in upload_sessions:
        return jsonify({'error': 'Invalid upload session'}), 400
    
    session_data = upload_sessions[upload_id]
    
    try:
        # Clean up temporary files
        if os.path.exists(session_data['temp_dir']):
            shutil.rmtree(session_data['temp_dir'])
        
        # Remove session
        del upload_sessions[upload_id]
        
        return jsonify({'message': 'Upload cancelled successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to cancel upload: {str(e)}'}), 500

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
            <div style="text-align: center; margin-top: 30px; color: #888; font-size: 12px;">
                © 2024 文件服务 | 作者: @Lvwan | 联系邮箱: 793145268@qq.com
            </div>
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
                filename = safe_filename(file.filename)
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
                position: relative;
            }
            
            .upload-area:hover {
                background: #f0f2ff;
                border-color: #5a67d8;
            }
            
            .upload-icon {
                font-size: 24px;
                color: #667eea;
                margin-bottom: 2px;
            }
            
            input[type="file"] {
                display: none;
            }
            
            .file-label {
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                background: transparent;
                color: #667eea;
                cursor: pointer;
                font-size: 16px;
                font-weight: 600;
                transition: all 0.3s ease;
                border-radius: 15px;
            }
            
            .file-label:hover {
                background: rgba(102, 126, 234, 0.05);
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
            }
            
            .upload-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(72, 187, 120, 0.3);
            }
            
            .upload-btn:disabled {
                background: #ccc;
                cursor: not-allowed;
                transform: none;
                box-shadow: none;
            }
            
            .progress-container {
                display: none;
                margin-top: 20px;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 10px;
                border: 1px solid #e9ecef;
            }
            
            .progress-bar-container {
                background: #e1e5e9;
                border-radius: 10px;
                height: 20px;
                margin: 10px 0;
                overflow: hidden;
                position: relative;
            }
            
            .progress-bar {
                background: linear-gradient(90deg, #48bb78, #38a169);
                height: 100%;
                border-radius: 10px;
                transition: width 0.3s ease;
                width: 0%;
            }
            
            .progress-text {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                color: #333;
                font-weight: 600;
                font-size: 12px;
            }
            
            .upload-info {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
                font-size: 14px;
                color: #666;
            }
            
            .cancel-btn {
                background: linear-gradient(135deg, #e53e3e 0%, #c53030 100%);
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                margin-left: 10px;
            }
            
            .cancel-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 15px rgba(229, 62, 62, 0.3);
            }
            
            .speed-info {
                font-size: 12px;
                color: #888;
                margin-top: 5px;
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
                
                .upload-btn {
                    display: block;
                    margin: 20px auto 0;
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
                    <div class="upload-area" id="uploadArea">
                        <label for="fileInput" class="file-label">
                            <div class="upload-icon">☁️</div>
                            <div style="font-size: 16px; font-weight: 600; margin-bottom: 10px;">选择文件或拖拽到此处</div>
                            <div id="fileName" style="color: #666; font-size: 14px;"></div>
                            <div id="fileSizeInfo" style="color: #888; font-size: 12px; margin-top: 5px;"></div>
                        </label>
                        <input type="file" name="file" id="fileInput" onchange="handleFileSelect(this.files[0])">
                    </div>
                    <div style="text-align: center; margin-top: 20px;">
                        <button type="button" class="upload-btn" id="uploadBtn" onclick="startUpload()" disabled>🚀 开始上传</button>
                    </div>
                </form>
                
                <!-- Progress Container -->
                <div class="progress-container" id="progressContainer">
                    <div class="upload-info">
                        <span id="uploadFileName"></span>
                        <span>
                            <button type="button" class="cancel-btn" id="cancelBtn" onclick="cancelUpload()">❌ 取消上传</button>
                        </span>
                    </div>
                    <div class="progress-bar-container">
                        <div class="progress-bar" id="progressBar"></div>
                        <div class="progress-text" id="progressText">0%</div>
                    </div>
                    <div class="upload-info">
                        <span id="uploadSpeed"></span>
                        <span id="uploadStatus">准备上传...</span>
                    </div>
                    <div class="speed-info" id="detailInfo"></div>
                </div>
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
        
        <footer style="text-align: center; padding: 20px; color: #666; background: #f8f9fa; margin-top: 40px; border-top: 1px solid #e9ecef;">
            <p style="margin: 0; font-size: 14px;">© 2024 文件管理系统 | 作者: @Lvwan | 联系邮箱: 793145268@qq.com</p>
        </footer>
        
        <script>
            let selectedFile = null;
            let uploadSession = null;
            let isUploading = false;
            let startTime = null;
            
            // File size formatting
            function formatFileSize(bytes) {
                if (bytes === 0) return '0 Bytes';
                const k = 1024;
                const sizes = ['Bytes', 'KB', 'MB', 'GB'];
                const i = Math.floor(Math.log(bytes) / Math.log(k));
                return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
            }
            
            // Format upload speed
            function formatSpeed(bytesPerSecond) {
                if (bytesPerSecond === 0) return '0 B/s';
                const k = 1024;
                const sizes = ['B/s', 'KB/s', 'MB/s', 'GB/s'];
                const i = Math.floor(Math.log(bytesPerSecond) / Math.log(k));
                return parseFloat((bytesPerSecond / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
            }
            
            // Handle file selection
            function handleFileSelect(file) {
                selectedFile = file;
                const fileName = document.getElementById('fileName');
                const fileSizeInfo = document.getElementById('fileSizeInfo');
                const uploadBtn = document.getElementById('uploadBtn');
                
                if (file) {
                    fileName.textContent = '已选择: ' + file.name;
                    fileSizeInfo.textContent = '文件大小: ' + formatFileSize(file.size);
                    uploadBtn.disabled = false;
                    
                    // Show chunk info for large files
                    if (file.size > 5 * 1024 * 1024) { // 5MB
                        fileSizeInfo.textContent += ' (将使用分片上传)';
                    }
                } else {
                    fileName.textContent = '';
                    fileSizeInfo.textContent = '';
                    uploadBtn.disabled = true;
                }
            }
            
            // Drag and drop support
            function setupDragAndDrop() {
                const uploadArea = document.getElementById('uploadArea');
                
                ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                    uploadArea.addEventListener(eventName, preventDefaults, false);
                });
                
                ['dragenter', 'dragover'].forEach(eventName => {
                    uploadArea.addEventListener(eventName, highlight, false);
                });
                
                ['dragleave', 'drop'].forEach(eventName => {
                    uploadArea.addEventListener(eventName, unhighlight, false);
                });
                
                uploadArea.addEventListener('drop', handleDrop, false);
                
                function preventDefaults(e) {
                    e.preventDefault();
                    e.stopPropagation();
                }
                
                function highlight(e) {
                    uploadArea.style.background = '#f0f2ff';
                    uploadArea.style.borderColor = '#5a67d8';
                }
                
                function unhighlight(e) {
                    uploadArea.style.background = '#f8f9ff';
                    uploadArea.style.borderColor = '#667eea';
                }
                
                function handleDrop(e) {
                    const dt = e.dataTransfer;
                    const files = dt.files;
                    if (files.length > 0) {
                        handleFileSelect(files[0]);
                    }
                }
            }
            
            // Start upload process
            async function startUpload() {
                if (!selectedFile || isUploading) return;
                
                isUploading = true;
                startTime = Date.now();
                
                // Show progress container
                document.getElementById('progressContainer').style.display = 'block';
                document.getElementById('uploadBtn').disabled = true;
                document.getElementById('uploadFileName').textContent = selectedFile.name;
                document.getElementById('uploadStatus').textContent = '初始化上传...';
                
                try {
                    // Determine if we need chunked upload (files > 5MB)
                    const useChunkedUpload = selectedFile.size > 5 * 1024 * 1024;
                    
                    if (useChunkedUpload) {
                        await uploadFileChunked();
                    } else {
                        await uploadFileNormal();
                    }
                    
                } catch (error) {
                    console.error('Upload failed:', error);
                    showUploadError('上传失败: ' + error.message);
                } finally {
                    isUploading = false;
                    document.getElementById('uploadBtn').disabled = false;
                }
            }
            
            // Normal upload for small files
            async function uploadFileNormal() {
                const formData = new FormData();
                formData.append('file', selectedFile);
                
                const xhr = new XMLHttpRequest();
                
                // Track upload progress
                xhr.upload.addEventListener('progress', (e) => {
                    if (e.lengthComputable) {
                        const percentComplete = (e.loaded / e.total) * 100;
                        updateProgress(percentComplete, e.loaded, e.total);
                    }
                });
                
                return new Promise((resolve, reject) => {
                    xhr.onload = function() {
                        if (xhr.status === 200) {
                            showUploadSuccess();
                            resolve();
                        } else {
                            reject(new Error('Upload failed'));
                        }
                    };
                    
                    xhr.onerror = function() {
                        reject(new Error('Network error'));
                    };
                    
                    xhr.open('POST', '/files');
                    xhr.send(formData);
                });
            }
            
            // Chunked upload for large files
            async function uploadFileChunked() {
                const chunkSize = 1024 * 1024; // 1MB chunks
                const totalChunks = Math.ceil(selectedFile.size / chunkSize);
                
                document.getElementById('uploadStatus').textContent = '初始化分片上传...';
                
                // Initialize upload session
                const initResponse = await fetch('/api/upload/init', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        filename: selectedFile.name,
                        total_size: selectedFile.size,
                        chunk_size: chunkSize
                    })
                });
                
                if (!initResponse.ok) {
                    const error = await initResponse.json();
                    throw new Error(error.error || 'Failed to initialize upload');
                }
                
                uploadSession = await initResponse.json();
                
                document.getElementById('uploadStatus').textContent = `上传中 (${totalChunks} 个分片)...`;
                document.getElementById('detailInfo').textContent = `分片大小: ${formatFileSize(chunkSize)}`;
                
                // Upload chunks
                for (let i = 0; i < totalChunks; i++) {
                    if (!isUploading) break; // Check if cancelled
                    
                    const start = i * chunkSize;
                    const end = Math.min(start + chunkSize, selectedFile.size);
                    const chunk = selectedFile.slice(start, end);
                    
                    await uploadChunk(i, chunk);
                }
                
                if (isUploading) {
                    // Complete upload
                    document.getElementById('uploadStatus').textContent = '合并文件中...';
                    
                    const completeResponse = await fetch('/api/upload/complete', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            upload_id: uploadSession.upload_id
                        })
                    });
                    
                    if (!completeResponse.ok) {
                        const error = await completeResponse.json();
                        throw new Error(error.error || 'Failed to complete upload');
                    }
                    
                    showUploadSuccess();
                }
            }
            
            // Upload a single chunk
            async function uploadChunk(chunkIndex, chunk) {
                const formData = new FormData();
                formData.append('upload_id', uploadSession.upload_id);
                formData.append('chunk_index', chunkIndex.toString());
                formData.append('chunk', chunk);
                
                const response = await fetch('/api/upload/chunk', {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.error || 'Failed to upload chunk');
                }
                
                const result = await response.json();
                
                // Update progress
                const bytesUploaded = (chunkIndex + 1) * uploadSession.chunk_size;
                updateProgress(result.progress, Math.min(bytesUploaded, selectedFile.size), selectedFile.size);
                
                document.getElementById('detailInfo').textContent = 
                    `已上传分片: ${result.received_chunks}/${result.total_chunks}`;
            }
            
            // Update progress display
            function updateProgress(percentage, uploaded, total) {
                const progressBar = document.getElementById('progressBar');
                const progressText = document.getElementById('progressText');
                const uploadSpeed = document.getElementById('uploadSpeed');
                
                progressBar.style.width = percentage + '%';
                progressText.textContent = Math.round(percentage) + '%';
                
                // Calculate upload speed
                if (startTime) {
                    const elapsed = (Date.now() - startTime) / 1000;
                    const speed = uploaded / elapsed;
                    uploadSpeed.textContent = '上传速度: ' + formatSpeed(speed);
                    
                    // Estimate remaining time
                    if (percentage > 0 && percentage < 100) {
                        const remaining = (total - uploaded) / speed;
                        const minutes = Math.floor(remaining / 60);
                        const seconds = Math.floor(remaining % 60);
                        uploadSpeed.textContent += ` | 剩余时间: ${minutes}:${seconds.toString().padStart(2, '0')}`;
                    }
                }
            }
            
            // Cancel upload
            async function cancelUpload() {
                if (!isUploading) return;
                
                isUploading = false;
                
                if (uploadSession) {
                    try {
                        await fetch('/api/upload/cancel', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                upload_id: uploadSession.upload_id
                            })
                        });
                    } catch (error) {
                        console.error('Failed to cancel upload:', error);
                    }
                    uploadSession = null;
                }
                
                // Reset UI
                document.getElementById('progressContainer').style.display = 'none';
                document.getElementById('uploadBtn').disabled = false;
                document.getElementById('progressBar').style.width = '0%';
                document.getElementById('progressText').textContent = '0%';
                document.getElementById('uploadStatus').textContent = '上传已取消';
            }
            
            // Show upload success
            function showUploadSuccess() {
                document.getElementById('uploadStatus').textContent = '上传完成!';
                document.getElementById('progressBar').style.width = '100%';
                document.getElementById('progressText').textContent = '100%';
                
                // Auto-hide progress and refresh page
                setTimeout(() => {
                    window.location.reload();
                }, 2000);
            }
            
            // Show upload error
            function showUploadError(message) {
                document.getElementById('uploadStatus').textContent = message;
                document.getElementById('progressContainer').style.display = 'none';
                
                // Show error message
                alert(message);
            }
            
            // Initialize drag and drop when page loads
            window.addEventListener('DOMContentLoaded', setupDragAndDrop);
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
    icon.title = "文件服务 - @Lvwan"  # 汉化标题并添加作者信息
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