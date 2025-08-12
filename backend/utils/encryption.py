#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
加密工具类 - 用于保护服务连接中的敏感信息
支持多种加密方式：AES对称加密、RSA非对称加密、数据库字段加密
"""

import os
import base64
import json
import hashlib
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import secrets


class EncryptionService:
    """统一的加密服务类"""
    
    def __init__(self):
        self.backend = default_backend()
        # 从环境变量或配置文件获取主密钥
        self.master_key = self._get_or_create_master_key()
        self.fernet = Fernet(self.master_key)
        # 生成RSA密钥对用于API通信
        self.rsa_private_key, self.rsa_public_key = self._get_or_create_rsa_keys()
    
    def _get_or_create_master_key(self):
        """获取或创建主加密密钥"""
        key_file = os.path.join(os.path.dirname(__file__), '..', '.encryption_key')
        
        if os.path.exists(key_file):
            try:
                with open(key_file, 'rb') as f:
                    return f.read()
            except Exception as e:
                print(f"⚠️ 读取加密密钥失败: {e}")
        
        # 创建新的密钥
        key = Fernet.generate_key()
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(key_file), exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(key)
            print(f"✅ 已生成新的加密密钥: {key_file}")
        except Exception as e:
            print(f"⚠️ 保存加密密钥失败: {e}")
        
        return key
    
    def _get_or_create_rsa_keys(self):
        """获取或创建RSA密钥对"""
        private_key_file = os.path.join(os.path.dirname(__file__), '..', '.rsa_private_key.pem')
        public_key_file = os.path.join(os.path.dirname(__file__), '..', '.rsa_public_key.pem')
        
        # 尝试加载已存在的密钥
        try:
            if os.path.exists(private_key_file) and os.path.exists(public_key_file):
                with open(private_key_file, 'rb') as f:
                    private_key = serialization.load_pem_private_key(
                        f.read(), 
                        password=None, 
                        backend=self.backend
                    )
                with open(public_key_file, 'rb') as f:
                    public_key = serialization.load_pem_public_key(
                        f.read(), 
                        backend=self.backend
                    )
                return private_key, public_key
        except Exception as e:
            print(f"⚠️ 读取RSA密钥失败: {e}")
        
        # 生成新的RSA密钥对
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=self.backend
        )
        public_key = private_key.public_key()
        
        try:
            # 保存私钥
            with open(private_key_file, 'wb') as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            # 保存公钥
            with open(public_key_file, 'wb') as f:
                f.write(public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ))
            
            print(f"✅ 已生成新的RSA密钥对")
        except Exception as e:
            print(f"⚠️ 保存RSA密钥失败: {e}")
        
        return private_key, public_key
    
    # =================== AES对称加密 ===================
    
    def encrypt_text(self, text):
        """使用AES加密文本"""
        if not text:
            return None
        
        try:
            # 转换为bytes
            if isinstance(text, str):
                text = text.encode('utf-8')
            
            # 加密
            encrypted = self.fernet.encrypt(text)
            # 返回base64编码的字符串
            return base64.b64encode(encrypted).decode('utf-8')
        except Exception as e:
            print(f"❌ AES加密失败: {e}")
            return None
    
    def decrypt_text(self, encrypted_text):
        """使用AES解密文本"""
        if not encrypted_text:
            return None
        
        try:
            # 从base64解码
            encrypted_bytes = base64.b64decode(encrypted_text.encode('utf-8'))
            # 解密
            decrypted = self.fernet.decrypt(encrypted_bytes)
            return decrypted.decode('utf-8')
        except Exception as e:
            print(f"❌ AES解密失败: {e}")
            return None
    
    # =================== RSA非对称加密 ===================
    
    def get_public_key_pem(self):
        """获取公钥的PEM格式"""
        return self.rsa_public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
    
    def rsa_encrypt(self, text, public_key_pem=None):
        """使用RSA公钥加密（用于前端发送敏感数据）"""
        if not text:
            return None
        
        try:
            # 使用指定的公钥或默认公钥
            public_key = self.rsa_public_key
            if public_key_pem:
                public_key = serialization.load_pem_public_key(
                    public_key_pem.encode('utf-8'),
                    backend=self.backend
                )
            
            # RSA加密（适用于小数据）
            if isinstance(text, str):
                text = text.encode('utf-8')
            
            encrypted = public_key.encrypt(
                text,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            return base64.b64encode(encrypted).decode('utf-8')
        except Exception as e:
            print(f"❌ RSA加密失败: {e}")
            return None
    
    def rsa_decrypt(self, encrypted_text):
        """使用RSA私钥解密"""
        if not encrypted_text:
            return None
        
        try:
            encrypted_bytes = base64.b64decode(encrypted_text.encode('utf-8'))
            
            decrypted = self.rsa_private_key.decrypt(
                encrypted_bytes,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            return decrypted.decode('utf-8')
        except Exception as e:
            print(f"❌ RSA解密失败: {e}")
            return None
    
    # =================== 数据库字段加密 ===================
    
    def encrypt_database_field(self, value):
        """加密数据库字段值"""
        if value is None:
            return None
        
        # 处理不同类型的数据
        if isinstance(value, dict):
            value = json.dumps(value, ensure_ascii=False)
        elif not isinstance(value, str):
            value = str(value)
        
        return self.encrypt_text(value)
    
    def decrypt_database_field(self, encrypted_value):
        """解密数据库字段值"""
        if not encrypted_value:
            return None
        
        decrypted = self.decrypt_text(encrypted_value)
        
        # 尝试解析为JSON
        if decrypted:
            try:
                return json.loads(decrypted)
            except (json.JSONDecodeError, TypeError):
                return decrypted
        
        return None
    
    # =================== API通信加密 ===================
    
    def encrypt_api_payload(self, data):
        """加密API请求/响应数据"""
        if not data:
            return None
        
        try:
            # 序列化为JSON
            json_data = json.dumps(data, ensure_ascii=False)
            # 加密
            return self.encrypt_text(json_data)
        except Exception as e:
            print(f"❌ API数据加密失败: {e}")
            return None
    
    def decrypt_api_payload(self, encrypted_data):
        """解密API请求/响应数据"""
        if not encrypted_data:
            return None
        
        try:
            # 解密
            decrypted_json = self.decrypt_text(encrypted_data)
            if decrypted_json:
                # 反序列化JSON
                return json.loads(decrypted_json)
        except Exception as e:
            print(f"❌ API数据解密失败: {e}")
        
        return None
    
    # =================== 工具方法 ===================
    
    def hash_password(self, password, salt=None):
        """哈希密码（用于密码存储，不可逆）"""
        if salt is None:
            salt = secrets.token_hex(32)
        
        # 使用PBKDF2进行密码哈希
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.encode('utf-8'),
            iterations=100000,
            backend=self.backend
        )
        
        key = base64.b64encode(kdf.derive(password.encode('utf-8'))).decode('utf-8')
        return f"{salt}${key}"
    
    def verify_password(self, password, hashed_password):
        """验证密码"""
        try:
            salt, stored_key = hashed_password.split('$')
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt.encode('utf-8'),
                iterations=100000,
                backend=self.backend
            )
            
            key = base64.b64encode(kdf.derive(password.encode('utf-8'))).decode('utf-8')
            return key == stored_key
        except Exception:
            return False
    
    def generate_session_token(self, user_id, expiry_hours=24):
        """生成会话令牌"""
        expiry = datetime.now() + timedelta(hours=expiry_hours)
        token_data = {
            'user_id': user_id,
            'expiry': expiry.isoformat(),
            'nonce': secrets.token_hex(16)
        }
        
        return self.encrypt_api_payload(token_data)
    
    def validate_session_token(self, token):
        """验证会话令牌"""
        token_data = self.decrypt_api_payload(token)
        
        if not token_data:
            return None
        
        try:
            expiry = datetime.fromisoformat(token_data['expiry'])
            if datetime.now() > expiry:
                return None  # 令牌已过期
            
            return token_data['user_id']
        except Exception:
            return None


# 全局加密服务实例
encryption_service = EncryptionService()


class ServiceConnectionEncryption:
    """服务连接专用加密处理类"""
    
    def __init__(self):
        self.encryption = encryption_service
        # 定义需要加密的敏感字段
        self.sensitive_fields = {
            'password',           # 密码
            'api_key',           # API密钥
            'file_service_password',  # 文件服务密码
            'username',          # 用户名（可选加密）
            'file_service_username'   # 文件服务用户名（可选加密）
        }
    
    def encrypt_connection_config(self, config):
        """加密连接配置中的敏感字段"""
        if not isinstance(config, dict):
            return config
        
        encrypted_config = config.copy()
        
        for field in self.sensitive_fields:
            if field in encrypted_config and encrypted_config[field]:
                encrypted_value = self.encryption.encrypt_text(encrypted_config[field])
                if encrypted_value:
                    encrypted_config[field] = encrypted_value
                    # 添加加密标记
                    encrypted_config[f"{field}_encrypted"] = True
        
        return encrypted_config
    
    def decrypt_connection_config(self, config):
        """解密连接配置中的敏感字段"""
        if not isinstance(config, dict):
            return config
        
        decrypted_config = config.copy()
        
        for field in self.sensitive_fields:
            if f"{field}_encrypted" in decrypted_config and decrypted_config.get(f"{field}_encrypted"):
                if field in decrypted_config and decrypted_config[field]:
                    decrypted_value = self.encryption.decrypt_text(decrypted_config[field])
                    if decrypted_value:
                        decrypted_config[field] = decrypted_value
                    # 移除加密标记
                    del decrypted_config[f"{field}_encrypted"]
        
        return decrypted_config
    
    def mask_sensitive_fields(self, config):
        """在返回给前端时遮蔽敏感字段"""
        if not isinstance(config, dict):
            return config
        
        masked_config = config.copy()
        
        for field in self.sensitive_fields:
            if field in masked_config and masked_config[field]:
                # 保留前2位和后2位，中间用*替代
                original_value = str(masked_config[field])
                if len(original_value) > 4:
                    masked_config[field] = original_value[:2] + '*' * (len(original_value) - 4) + original_value[-2:]
                else:
                    masked_config[field] = '*' * len(original_value)
        
        return masked_config


# 全局服务连接加密实例
service_connection_encryption = ServiceConnectionEncryption()