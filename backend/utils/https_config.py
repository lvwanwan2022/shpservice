#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HTTPS配置工具
用于配置SSL/TLS加密传输，保护网络通信安全
"""

import os
import ssl
import subprocess
from datetime import datetime, timedelta
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend


class HTTPSConfig:
    """HTTPS配置管理类"""
    
    def __init__(self, cert_dir=None):
        self.cert_dir = cert_dir or os.path.join(os.path.dirname(__file__), '..', 'ssl')
        self.ensure_cert_dir()
    
    def ensure_cert_dir(self):
        """确保证书目录存在"""
        os.makedirs(self.cert_dir, exist_ok=True)
    
    def generate_self_signed_cert(self, 
                                 common_name='localhost',
                                 alt_names=None,
                                 days_valid=365):
        """
        生成自签名SSL证书用于开发环境
        
        Args:
            common_name: 证书的通用名称（域名）
            alt_names: 替代名称列表
            days_valid: 证书有效期（天）
        
        Returns:
            tuple: (证书文件路径, 私钥文件路径)
        """
        try:
            print(f"🔒 生成自签名SSL证书...")
            
            # 生成私钥
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            
            # 证书主体信息
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "CN"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Beijing"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "Beijing"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "ShpService"),
                x509.NameAttribute(NameOID.COMMON_NAME, common_name),
            ])
            
            # 构建证书
            cert_builder = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.utcnow()
            ).not_valid_after(
                datetime.utcnow() + timedelta(days=days_valid)
            )
            
            # 添加扩展
            import ipaddress
            san_list = [
                x509.DNSName(common_name),
                x509.DNSName("127.0.0.1"),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
                x509.IPAddress(ipaddress.IPv6Address("::1")),
            ]
            
            # 添加额外的替代名称
            for name in (alt_names or []):
                try:
                    # 尝试解析为IP地址
                    ip_addr = ipaddress.ip_address(name)
                    san_list.append(x509.IPAddress(ip_addr))
                except ValueError:
                    # 如果不是IP地址，作为DNS名称添加
                    san_list.append(x509.DNSName(name))
            
            cert_builder = cert_builder.add_extension(
                x509.SubjectAlternativeName(san_list),
                critical=False,
            )
            
            # 添加基本约束
            cert_builder = cert_builder.add_extension(
                x509.BasicConstraints(ca=False, path_length=None),
                critical=True,
            )
            
            # 添加密钥用途
            cert_builder = cert_builder.add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    key_encipherment=True,
                    key_agreement=False,
                    key_cert_sign=False,
                    crl_sign=False,
                    content_commitment=False,
                    data_encipherment=False,
                    encipher_only=False,
                    decipher_only=False
                ),
                critical=True,
            )
            
            # 签名证书
            certificate = cert_builder.sign(private_key, hashes.SHA256(), default_backend())
            
            # 保存证书和私钥
            cert_path = os.path.join(self.cert_dir, 'server.crt')
            key_path = os.path.join(self.cert_dir, 'server.key')
            
            # 写入证书文件
            with open(cert_path, 'wb') as f:
                f.write(certificate.public_bytes(serialization.Encoding.PEM))
            
            # 写入私钥文件
            with open(key_path, 'wb') as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            # 设置文件权限
            os.chmod(cert_path, 0o644)
            os.chmod(key_path, 0o600)
            
            print(f"✅ SSL证书生成成功:")
            print(f"   证书文件: {cert_path}")
            print(f"   私钥文件: {key_path}")
            print(f"   通用名称: {common_name}")
            print(f"   有效期: {days_valid} 天")
            
            return cert_path, key_path
            
        except Exception as e:
            print(f"❌ 生成SSL证书失败: {e}")
            return None, None
    
    def get_cert_info(self, cert_path):
        """获取证书信息"""
        try:
            with open(cert_path, 'rb') as f:
                cert = x509.load_pem_x509_certificate(f.read(), default_backend())
            
            return {
                'subject': cert.subject.rfc4514_string(),
                'issuer': cert.issuer.rfc4514_string(),
                'serial_number': str(cert.serial_number),
                'not_valid_before': cert.not_valid_before.isoformat(),
                'not_valid_after': cert.not_valid_after.isoformat(),
                'is_expired': datetime.utcnow() > cert.not_valid_after
            }
        except Exception as e:
            print(f"❌ 读取证书信息失败: {e}")
            return None
    
    def check_cert_expiry(self, cert_path, warning_days=30):
        """检查证书过期时间"""
        try:
            with open(cert_path, 'rb') as f:
                cert = x509.load_pem_x509_certificate(f.read(), default_backend())
            
            now = datetime.utcnow()
            expires = cert.not_valid_after
            days_left = (expires - now).days
            
            if days_left < 0:
                print(f"⚠️ SSL证书已过期: {abs(days_left)} 天前")
                return False
            elif days_left < warning_days:
                print(f"⚠️ SSL证书将在 {days_left} 天后过期")
                return True
            else:
                print(f"✅ SSL证书有效，还有 {days_left} 天过期")
                return True
                
        except Exception as e:
            print(f"❌ 检查证书过期时间失败: {e}")
            return False
    
    def create_flask_ssl_context(self, cert_path=None, key_path=None):
        """为Flask应用创建SSL上下文"""
        try:
            cert_path = cert_path or os.path.join(self.cert_dir, 'server.crt')
            key_path = key_path or os.path.join(self.cert_dir, 'server.key')
            
            # 检查证书文件是否存在
            if not os.path.exists(cert_path) or not os.path.exists(key_path):
                print("❌ SSL证书文件不存在，正在生成...")
                cert_path, key_path = self.generate_self_signed_cert()
                if not cert_path:
                    return None
            
            # 检查证书有效性
            if not self.check_cert_expiry(cert_path):
                print("⚠️ 证书已过期或即将过期，建议重新生成")
            
            # 创建SSL上下文
            context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
            context.load_cert_chain(cert_path, key_path)
            
            # 配置安全选项
            context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
            
            print(f"✅ SSL上下文创建成功")
            return context
            
        except Exception as e:
            print(f"❌ 创建SSL上下文失败: {e}")
            return None
    
    def generate_nginx_config(self, 
                            server_name='localhost',
                            listen_port=443,
                            proxy_pass='http://127.0.0.1:5000'):
        """生成Nginx HTTPS配置"""
        config_template = f"""
# HTTPS configuration for ShpService
server {{
    listen {listen_port} ssl http2;
    server_name {server_name};

    # SSL Configuration
    ssl_certificate {os.path.join(self.cert_dir, 'server.crt')};
    ssl_certificate_key {os.path.join(self.cert_dir, 'server.key')};
    
    # SSL Security Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-CHACHA20-POLY1305;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_session_tickets off;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Proxy Configuration
    location / {{
        proxy_pass {proxy_pass};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }}
    
    # Static files (if serving directly)
    location /static/ {{
        alias /path/to/your/static/files/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }}
}}

# Redirect HTTP to HTTPS
server {{
    listen 80;
    server_name {server_name};
    return 301 https://$server_name$request_uri;
}}
"""
        
        config_path = os.path.join(self.cert_dir, 'nginx_https.conf')
        with open(config_path, 'w') as f:
            f.write(config_template.strip())
        
        print(f"✅ Nginx HTTPS配置已生成: {config_path}")
        return config_path


def setup_https_for_development():
    """为开发环境设置HTTPS"""
    https_config = HTTPSConfig()
    
    # 生成自签名证书
    cert_path, key_path = https_config.generate_self_signed_cert(
        common_name='localhost',
        alt_names=['127.0.0.1', '::1'],
        days_valid=365
    )
    
    if cert_path and key_path:
        # 生成Nginx配置
        nginx_config = https_config.generate_nginx_config()
        
        print("\n🔒 HTTPS开发环境设置完成!")
        print("\n📋 后续步骤:")
        print("1. 将生成的证书添加到浏览器信任列表")
        print("2. 更新应用配置以使用HTTPS")
        print("3. 如使用Nginx，应用生成的配置文件")
        print("\n⚠️ 注意: 自签名证书仅适用于开发环境")
        
        return https_config
    
    return None


if __name__ == "__main__":
    setup_https_for_development()