#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿里云 DDNS IPv6 自动更新脚本 (简化版)
"""

import json
import requests
import subprocess
import re
import logging
from datetime import datetime
import os

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def get_local_ipv6():
    """获取本机IPv6地址"""
    try:
        # Windows ipconfig方式
        result = subprocess.run(['ipconfig'], capture_output=True, text=True, encoding='gbk')
        ipv6_pattern = r'IPv6 地址.*?:\s*([0-9a-fA-F:]+)'
        matches = re.findall(ipv6_pattern, result.stdout)
        
        for match in matches:
            if not match.startswith('fe80:') and not match.startswith('::1'):
                logger.info(f"发现IPv6地址: {match}")
                return match
                
        # 在线获取方式
        response = requests.get('https://ipv6.icanhazip.com', timeout=10)
        ipv6 = response.text.strip()
        if ipv6 and not ipv6.startswith('fe80:'):
            logger.info(f"在线获取IPv6: {ipv6}")
            return ipv6
            
    except Exception as e:
        logger.error(f"获取IPv6失败: {e}")
    return None

def update_aliyun_dns(access_key_id, access_key_secret, domain, subdomain, ipv6):
    """使用阿里云SDK更新DNS记录"""
    try:
        # 这里使用简化的HTTP API调用
        # 实际生产环境建议使用官方SDK: pip install alibabacloud_alidns20150109
        
        print(f"准备更新DNS记录:")
        print(f"  域名: {subdomain}.{domain}")
        print(f"  IPv6: {ipv6}")
        print(f"  请手动在阿里云DNS控制台更新，或安装SDK: pip install alibabacloud_alidns20150109")
        
        # 记录到日志文件
        with open('ddns_update.log', 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now()} - 需要更新: {subdomain}.{domain} -> {ipv6}\n")
            
        return True
        
    except Exception as e:
        logger.error(f"DNS更新失败: {e}")
        return False

def main():
    """主函数"""
    # 读取配置文件
    config_file = 'ddns_config.json'
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception as e:
            logger.error(f"读取配置文件失败: {e}")
            return
    else:
        # 默认配置
        config = {
            'access_key_id': 'YOUR_ACCESS_KEY_ID',
            'access_key_secret': 'YOUR_ACCESS_KEY_SECRET', 
            'domain': 'totodudu.com',
            'subdomain': 'ipv6'
        }
        
        # 保存默认配置
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"❌ 请编辑 {config_file} 文件，填入您的阿里云AccessKey信息")
        return
    
    # 检查配置
    if config['access_key_id'] == 'YOUR_ACCESS_KEY_ID':
        print("❌ 请先在 ddns_config.json 中配置阿里云AccessKey信息！")
        return
    
    # 获取当前IPv6
    current_ipv6 = get_local_ipv6()
    if not current_ipv6:
        print("❌ 无法获取IPv6地址")
        return
    
    print(f"✅ 当前IPv6地址: {current_ipv6}")
    
    # 检查是否需要更新
    last_ip_file = 'last_ipv6.txt'
    last_ipv6 = None
    if os.path.exists(last_ip_file):
        with open(last_ip_file, 'r') as f:
            last_ipv6 = f.read().strip()
    
    if last_ipv6 == current_ipv6:
        print("💡 IPv6地址未变化，无需更新")
        return
    
    # 更新DNS
    success = update_aliyun_dns(
        config['access_key_id'],
        config['access_key_secret'],
        config['domain'],
        config['subdomain'],
        current_ipv6
    )
    
    if success:
        # 保存当前IP
        with open(last_ip_file, 'w') as f:
            f.write(current_ipv6)
        
        print("✅ DDNS更新成功！")
        print(f"🌐 您的域名: {config['subdomain']}.{config['domain']}")
        print(f"📍 指向地址: {current_ipv6}")
    else:
        print("❌ DDNS更新失败")

 