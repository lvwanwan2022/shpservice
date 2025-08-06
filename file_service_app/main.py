import tkinter as tk
from tkinter import filedialog, messagebox
import os
import sys
import threading
from flask import Flask, request, send_from_directory, abort, Response
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

def check_disk_usage(path, max_size_mb):
    """Check if adding a file would exceed max capacity."""
    total, used, free = shutil.disk_usage(path)
    used_mb = used / (1024 * 1024)
    return used_mb < max_size_mb

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

    def start_server():
        global CONFIG
        try:
            CONFIG['port'] = int(port_entry.get())
            CONFIG['folder'] = folder_entry.get()
            CONFIG['max_size_mb'] = float(max_size_entry.get())
            CONFIG['username'] = user_entry.get()
            CONFIG['password_hash'] = generate_password_hash(pass_entry.get())
            
            if not os.path.exists(CONFIG['folder']):
                os.makedirs(CONFIG['folder'])
            
            root.destroy()
        except ValueError as e:
            messagebox.showerror("错误", f"无效输入: {e}")  # 汉化错误消息
            return

    tk.Button(root, text="启动服务", command=start_server).grid(row=5, column=1)  # 汉化按钮
    root.mainloop()

    if not CONFIG:
        sys.exit(0)

# Flask app
app = Flask(__name__)

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.username != CONFIG['username'] or not check_password_hash(CONFIG['password_hash'], auth.password):
            return Response('Unauthorized', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})
        return f(*args, **kwargs)
    return decorated

@app.route('/upload', methods=['POST'])
@requires_auth
def upload_file():
    if 'file' not in request.files:
        return 'No file part', 400
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400
    
    filename = secure_filename(file.filename)
    file_path = os.path.join(CONFIG['folder'], filename)
    
    # Check capacity (approximate: check current + file size)
    file_size_mb = request.content_length / (1024 * 1024) if request.content_length else 0
    if not check_disk_usage(CONFIG['folder'], CONFIG['max_size_mb'] - file_size_mb):
        return 'Exceeded max capacity', 507
    
    file.save(file_path)
    return 'File uploaded successfully', 200

@app.route('/files/<filename>', methods=['GET'])
@requires_auth
def download_file(filename):
    try:
        return send_from_directory(CONFIG['folder'], filename)
    except FileNotFoundError:
        abort(404)

@app.route('/list', methods=['GET'])
@requires_auth
def list_files():
    files = os.listdir(CONFIG['folder'])
    return {'files': files}, 200

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