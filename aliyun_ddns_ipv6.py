#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿里云 DDNS IPv6 自动更新脚本
支持自动检测本机IPv6地址并更新到阿里云DNS
"""

import json
import time
import hashlib
import hmac
import base64
import urllib.parse
import urllib.request
import re
import subprocess
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ddns_ipv6.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AliyunDDNS:
    def __init__(self, access_key_id, access_key_secret, domain, subdomain="ipv6"):
        """
        初始化阿里云DDNS客户端
        
        Args:
            access_key_id: 阿里云AccessKey ID
            access_key_secret: 阿里云AccessKey Secret
            domain: 主域名 (如: totodudu.com)
            subdomain: 子域名 (如: ipv6, 默认为ipv6)
        """
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.domain = domain
        self.subdomain = subdomain
        self.full_domain = f"{subdomain}.{domain}" if subdomain else domain
        self.endpoint = "https://alidns.aliyuncs.com"
        
    def _get_local_ipv6(self):
        """获取本机公网IPv6地址"""
        try:
            # 方法1: 通过ipconfig获取
            result = subprocess.run(['ipconfig'], capture_output=True, text=True, encoding='gbk')
            ipv6_pattern = r'IPv6 地址.*?:\s*([0-9a-fA-F:]+)'
            matches = re.findall(ipv6_pattern, result.stdout)
            
            for match in matches:
                # 排除本地链路地址
                if not match.startswith('fe80:') and not match.startswith('::1'):
                    # 验证是否为有效的全球单播地址
                    if self._is_global_ipv6(match):
                        logger.info(f"检测到IPv6地址: {match}")
                        return match
                        
            # 方法2: 通过在线服务获取
            try:
                req = urllib.request.Request('https://ipv6.icanhazip.com')
                req.add_header('User-Agent', 'DDNS-Client/1.0')
                with urllib.request.urlopen(req, timeout=10) as response:
                    ipv6 = response.read().decode().strip()
                    if self._is_global_ipv6(ipv6):
                        logger.info(f"通过在线服务获取IPv6地址: {ipv6}")
                        return ipv6
            except Exception as e:
                logger.warning(f"在线获取IPv6地址失败: {e}")
                
        except Exception as e:
            logger.error(f"获取IPv6地址失败: {e}")
            
        return None
    
    def _is_global_ipv6(self, ipv6):
        """检查是否为全球单播IPv6地址"""
        if not ipv6:
            return False
        # 排除本地地址
        exclude_prefixes = ['fe80:', '::1', 'fc00:', 'fd00:']
        return not any(ipv6.lower().startswith(prefix) for prefix in exclude_prefixes)
    
    def _sign_request(self, params):
        """生成阿里云API签名"""
        # 排序参数
        sorted_params = sorted(params.items())
        # 构建查询字符串
        query_string = '&'.join([f"{k}={urllib.parse.quote(str(v), safe='')}" for k, v in sorted_params])
        # 构建待签名字符串
        string_to_sign = f"GET&%2F&{urllib.parse.quote(query_string, safe='')}"
        # 计算签名
        signature = base64.b64encode(
            hmac.new(
                (self.access_key_secret + '&').encode('utf-8'),
                string_to_sign.encode('utf-8'),
                hashlib.sha1
            ).digest()
        ).decode('utf-8')
        
        return signature
    
    def _make_request(self, action, params=None):
        """发送API请求"""
        if params is None:
            params = {}
            
        # 公共参数
        common_params = {
            'Format': 'JSON',
            'Version': '2015-01-09',
            'AccessKeyId': self.access_key_id,
            'SignatureMethod': 'HMAC-SHA1',
            'Timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            'SignatureVersion': '1.0',
            'SignatureNonce': str(int(time.time() * 1000)),
            'Action': action
        }
        
        # 合并参数
        all_params = {**common_params, **params}
        
        # 生成签名
        signature = self._sign_request(all_params)
        all_params['Signature'] = signature
        
        # 构建URL
        query_string = '&'.join([f"{k}={urllib.parse.quote(str(v))}" for k, v in all_params.items()])
        url = f"{self.endpoint}/?{query_string}"
        
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'DDNS-Client/1.0')
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode())
        except Exception as e:
            logger.error(f"API请求失败: {e}")
            return None
    
    def get_domain_records(self):
        """获取域名记录"""
        params = {
            'DomainName': self.domain,
            'RRKeyWord': self.subdomain,
            'Type': 'AAAA'
        }
        
        result = self._make_request('DescribeDomainRecords', params)
        if result and 'DomainRecords' in result:
            records = result['DomainRecords']['Record']
            return records if isinstance(records, list) else [records] if records else []
        return []
    
    def add_domain_record(self, ipv6):
        """添加域名记录"""
        params = {
            'DomainName': self.domain,
            'RR': self.subdomain,
            'Type': 'AAAA',
            'Value': ipv6,
            'TTL': 600  # 10分钟TTL，便于快速更新
        }
        
        result = self._make_request('AddDomainRecord', params)
        if result and result.get('RecordId'):
            logger.info(f"成功添加AAAA记录: {self.full_domain} -> {ipv6}")
            return result['RecordId']
        else:
            logger.error(f"添加记录失败: {result}")
            return None
    
    def update_domain_record(self, record_id, ipv6):
        """更新域名记录"""
        params = {
            'RecordId': record_id,
            'RR': self.subdomain,
            'Type': 'AAAA',
            'Value': ipv6,
            'TTL': 600
        }
        
        result = self._make_request('UpdateDomainRecord', params)
        if result and result.get('RecordId'):
            logger.info(f"成功更新AAAA记录: {self.full_domain} -> {ipv6}")
            return True
        else:
            logger.error(f"更新记录失败: {result}")
            return False
    
    def update_ddns(self):
        """执行DDNS更新"""
        logger.info("开始DDNS更新...")
        
        # 获取当前IPv6地址
        current_ipv6 = self._get_local_ipv6()
        if not current_ipv6:
            logger.error("无法获取IPv6地址")
            return False
        
        # 获取现有记录
        records = self.get_domain_records()
        
        if records:
            # 检查是否需要更新
            existing_record = records[0]
            if existing_record['Value'] == current_ipv6:
                logger.info(f"IPv6地址未变化: {current_ipv6}")
                return True
            
            # 更新记录
            logger.info(f"IPv6地址变化: {existing_record['Value']} -> {current_ipv6}")
            return self.update_domain_record(existing_record['RecordId'], current_ipv6)
        else:
            # 添加新记录
            logger.info(f"添加新的IPv6记录: {current_ipv6}")
            return self.add_domain_record(current_ipv6) is not None

def main():
    """主函数"""
    # 配置信息 - 请填写您的实际信息
    config = {
        'access_key_id': 'YOUR_ACCESS_KEY_ID',          # 替换为您的AccessKey ID
        'access_key_secret': 'YOUR_ACCESS_KEY_SECRET',   # 替换为您的AccessKey Secret
        'domain': 'totodudu.com',                        # 您的域名
        'subdomain': 'ipv6'                              # 子域名，最终域名为 ipv6.totodudu.com
    }
    
    # 检查配置
    if config['access_key_id'] == 'YOUR_ACCESS_KEY_ID':
        print("❌ 请先配置阿里云AccessKey信息！")
        print("请编辑脚本中的config部分，填入您的实际AccessKey信息")
        return
    
    # 创建DDNS客户端
    ddns = AliyunDDNS(**config)
    
    # 执行更新
    success = ddns.update_ddns()
    if success:
        logger.info("✅ DDNS更新成功")
        print(f"✅ IPv6 DDNS更新成功！")
        print(f"🌐 您的服务现在可以通过以下域名访问：")
        print(f"   前端: http://{ddns.full_domain}:8080")
        print(f"   后端: http://{ddns.full_domain}:5030")
        print(f"   Martin: http://{ddns.full_domain}:3000")
    else:
        logger.error("❌ DDNS更新失败")
        print("❌ DDNS更新失败，请检查配置和网络连接")

if __name__ == '__main__':
    main() 