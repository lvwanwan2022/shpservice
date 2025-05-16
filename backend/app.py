#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, jsonify
from flask_cors import CORS
from flasgger import Swagger

from routes.file_routes import file_bp
from routes.layer_routes import layer_bp
from routes.scene_routes import scene_bp
from routes.geoservice_routes import geoservice_bp

app = Flask(__name__)
app.config.from_object('config.APP_CONFIG')

# 启用CORS
CORS(app)

# 配置Swagger
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/apispec.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/swagger/"
}

swagger = Swagger(app, config=swagger_config)

# 注册蓝图
app.register_blueprint(file_bp, url_prefix='/api/file')
app.register_blueprint(layer_bp, url_prefix='/api/layer')
app.register_blueprint(scene_bp, url_prefix='/api/scene')
app.register_blueprint(geoservice_bp, url_prefix='/api/geoservice')

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口
    ---
    responses:
      200:
        description: 系统正常运行
    """
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=app.config['DEBUG']) 