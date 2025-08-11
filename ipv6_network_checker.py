#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IPv6网络连通性检查工具
专门针对中国移动宽带的IPv6配置问题诊断
"""

import subprocess
import re
import socket
import urllib.request
import json
import sys
import platform
from datetime import datetime

class IPv6NetworkChecker:
    def __init__(self):
        self.system = platform.system()
        self.results = {}
        
    def print_separator(self, title):
        """打印分隔线"""
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
        
    def run_command(self, cmd):
        """执行系统命令"""
        try:
            if self.system == "Windows":
                result = subprocess.run(cmd, shell=True, capture_output=True, 
                                      text=True, encoding='gbk', timeout=30)
            else:
                result = subprocess.run(cmd, shell=True, capture_output=True, 
                                      text=True, timeout=30)
            return result.stdout, result.stderr, result.returncode
        except Exception as e:
            return "", str(e), -1
    
    def check_ipv6_addresses(self):
        """检查IPv6地址配置"""
        self.print_separator("1. IPv6地址检查")
        
        if self.system == "Windows":
            stdout, stderr, code = self.run_command("ipconfig")
            ipv6_pattern = r'IPv6 地址.*?:\s*([0-9a-fA-F:]+)'
        else:
            stdout, stderr, code = self.run_command("ip -6 addr show")
            ipv6_pattern = r'inet6\s+([0-9a-fA-F:]+)/\d+'
        
        ipv6_addresses = re.findall(ipv6_pattern, stdout)
        
        local_addresses = []
        global_addresses = []
        
        for addr in ipv6_addresses:
            if addr.startswith('fe80:'):
                local_addresses.append(addr)
            elif not addr.startswith('::1') and not addr.startswith('fc00:') and not addr.startswith('fd00:'):
                global_addresses.append(addr)
        
        print(f"🔍 本地链路地址 (fe80::): {len(local_addresses)} 个")
        for addr in local_addresses[:3]:  # 只显示前3个
            print(f"   - {addr}")
            
        print(f"🌐 全球单播地址: {len(global_addresses)} 个")
        for addr in global_addresses:
            print(f"   - {addr}")
            
        self.results['local_ipv6'] = local_addresses
        self.results['global_ipv6'] = global_addresses
        
        if not global_addresses:
            print("❌ 未检测到全球单播IPv6地址！")
            print("💡 这通常表示光猫或路由器的IPv6配置有问题")
            return False
        else:
            print("✅ 检测到全球单播IPv6地址")
            return True
    
    def check_ipv6_gateway(self):
        """检查IPv6网关"""
        self.print_separator("2. IPv6网关检查")
        
        if self.system == "Windows":
            stdout, stderr, code = self.run_command("route print -6")
            # 查找默认路由
            gateway_pattern = r'::/0\s+([0-9a-fA-F:]+)'
        else:
            stdout, stderr, code = self.run_command("ip -6 route show default")
            gateway_pattern = r'default via ([0-9a-fA-F:]+)'
        
        gateways = re.findall(gateway_pattern, stdout)
        
        if gateways:
            print(f"✅ 检测到IPv6默认网关:")
            for gw in set(gateways):
                print(f"   - {gw}")
            self.results['ipv6_gateway'] = gateways
            return True
        else:
            print("❌ 未检测到IPv6默认网关！")
            print("💡 这表示路由器没有正确分发IPv6路由信息")
            self.results['ipv6_gateway'] = []
            return False
    
    def check_dns_servers(self):
        """检查DNS服务器"""
        self.print_separator("3. DNS服务器检查")
        
        if self.system == "Windows":
            stdout, stderr, code = self.run_command("nslookup")
            print("📋 当前DNS配置:")
            print(stdout[:500] if stdout else "无法获取DNS信息")
        
        # 测试IPv6 DNS解析
        test_domains = ['ipv6.google.com', 'ipv6.test-ipv6.com']
        dns_working = False
        
        for domain in test_domains:
            try:
                result = socket.getaddrinfo(domain, None, socket.AF_INET6)
                if result:
                    print(f"✅ IPv6 DNS解析正常: {domain}")
                    dns_working = True
                    break
            except Exception as e:
                print(f"❌ IPv6 DNS解析失败: {domain} - {e}")
        
        self.results['dns_working'] = dns_working
        return dns_working
    
    def check_ipv6_connectivity(self):
        """检查IPv6连通性"""
        self.print_separator("4. IPv6连通性测试")
        
        # 测试IPv6网站连接
        test_sites = [
            ('ipv6.google.com', '谷歌IPv6'),
            ('ipv6.test-ipv6.com', 'IPv6测试站点'),
            ('2001:4860:4860::8888', '谷歌DNS'),
        ]
        
        connectivity_working = False
        
        for site, name in test_sites:
            if self.system == "Windows":
                stdout, stderr, code = self.run_command(f"ping -6 -n 3 {site}")
                if "TTL=" in stdout or "生存时间" in stdout:
                    print(f"✅ {name} 连通性正常")
                    connectivity_working = True
                else:
                    print(f"❌ {name} 连通性失败")
            else:
                stdout, stderr, code = self.run_command(f"ping6 -c 3 {site}")
                if code == 0:
                    print(f"✅ {name} 连通性正常")
                    connectivity_working = True
                else:
                    print(f"❌ {name} 连通性失败")
        
        self.results['connectivity_working'] = connectivity_working
        return connectivity_working
    
    def check_port_accessibility(self):
        """检查端口可访问性"""
        self.print_separator("5. 端口可访问性检查")
        
        ports_to_check = [8080, 5030, 3000, 22, 80, 443]
        
        print("🔍 检查本机监听的端口:")
        if self.system == "Windows":
            stdout, stderr, code = self.run_command("netstat -an | findstr LISTENING")
        else:
            stdout, stderr, code = self.run_command("netstat -tlnp")
        
        listening_ports = []
        for port in ports_to_check:
            if f":{port}" in stdout:
                listening_ports.append(port)
                print(f"✅ 端口 {port} 正在监听")
            else:
                print(f"❌ 端口 {port} 未监听")
        
        self.results['listening_ports'] = listening_ports
        
        if not listening_ports:
            print("⚠️  没有检测到您的服务端口在监听")
            print("💡 请确保您的服务(前端8080, 后端5030, Martin3000)正在运行")
    
    def check_firewall_status(self):
        """检查防火墙状态"""
        self.print_separator("6. 防火墙检查")
        
        if self.system == "Windows":
            stdout, stderr, code = self.run_command("netsh advfirewall show allprofiles state")
            print("🛡️ Windows防火墙状态:")
            print(stdout if stdout else "无法获取防火墙状态")
            
            # 检查防火墙规则
            print("\n🔍 检查防火墙入站规则:")
            stdout2, stderr2, code2 = self.run_command("netsh advfirewall firewall show rule name=all dir=in | findstr -i \"端口\\|port\"")
            if stdout2:
                print(stdout2[:1000])
            else:
                print("未找到相关端口规则")
    
    def generate_diagnosis_report(self):
        """生成诊断报告"""
        self.print_separator("🏥 诊断报告")
        
        print(f"📋 检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🖥️  操作系统: {self.system}")
        
        # 分析问题
        issues = []
        recommendations = []
        
        if not self.results.get('global_ipv6'):
            issues.append("❌ 未获取到IPv6公网地址")
            recommendations.extend([
                "1. 检查光猫IPv6功能是否开启",
                "2. 检查路由器IPv6功能是否开启",
                "3. 重启光猫和路由器",
                "4. 联系中国移动确认IPv6服务是否开通"
            ])
        
        if not self.results.get('ipv6_gateway'):
            issues.append("❌ 未检测到IPv6网关")
            recommendations.extend([
                "5. 检查路由器IPv6 DHCP服务是否启用",
                "6. 检查路由器IPv6前缀分发是否正常"
            ])
        
        if not self.results.get('connectivity_working'):
            issues.append("❌ IPv6连通性异常")
            recommendations.extend([
                "7. 检查运营商IPv6网络状态",
                "8. 尝试手动配置IPv6 DNS服务器"
            ])
        
        if not self.results.get('listening_ports'):
            issues.append("❌ 服务端口未监听")
            recommendations.extend([
                "9. 确保您的应用服务正在运行",
                "10. 检查应用是否绑定到IPv6地址"
            ])
        
        print(f"\n🔍 发现的问题 ({len(issues)} 个):")
        for issue in issues:
            print(f"   {issue}")
        
        print(f"\n💡 建议的解决方案:")
        for rec in recommendations:
            print(f"   {rec}")
        
        # 给出具体的设备检查指导
        self.print_device_check_guide()
    
    def print_device_check_guide(self):
        """打印设备检查指导"""
        self.print_separator("🔧 中国移动宽带设备检查指南")
        
        print("""
🏠 光猫检查步骤:
1. 浏览器打开 http://192.168.1.1 (光猫管理页面)
2. 使用 useradmin/password 或设备标签上的账号登录
3. 查看 [网络配置] → [IPv6配置]:
   ✅ IPv6功能: 启用
   ✅ IPv6地址获取方式: DHCP或SLAAC
   ✅ IPv6前缀: 应该显示运营商分配的前缀
4. 查看 [状态] → [网络状态]:
   ✅ IPv6连接状态: 已连接
   ✅ IPv6地址: 应该有全球单播地址

📡 路由器检查步骤:
1. 浏览器打开路由器管理页面 (通常是 192.168.0.1 或 192.168.1.1)
2. 登录后查看 [高级设置] → [IPv6]:
   ✅ IPv6功能: 启用
   ✅ 连接类型: 桥接模式 或 Native IPv6
   ✅ 前缀分发: 启用
   ✅ DHCP v6: 启用
3. 查看 [状态] 页面:
   ✅ IPv6 WAN地址: 有效
   ✅ IPv6 LAN前缀: 有效

🛠️  服务器应用检查:
1. 确保应用绑定到 IPv6 地址:
   - 前端: 监听 [::]:8080
   - 后端: 监听 [::]:5030  
   - Martin: 监听 [::]:3000
2. 检查防火墙规则是否允许这些端口

🔍 如果问题依然存在，请检查:
1. 运营商是否真正开通了IPv6服务
2. 是否需要向中国移动申请IPv6公网前缀
3. 小区网络是否支持IPv6

📞 中国移动客服: 10086 (说明需要开通IPv6服务)
        """)

def main():
    """主函数"""
    print("🚀 IPv6网络连通性检查工具")
    print("📱 专为中国移动宽带用户设计")
    print("🔧 帮助诊断DDNS解析正常但无法远程访问的问题\n")
    
    checker = IPv6NetworkChecker()
    
    # 执行所有检查
    checker.check_ipv6_addresses()
    checker.check_ipv6_gateway()
    checker.check_dns_servers()
    checker.check_ipv6_connectivity()
    checker.check_port_accessibility()
    checker.check_firewall_status()
    
    # 生成诊断报告
    checker.generate_diagnosis_report()
    
    print(f"\n🏁 检查完成！请根据诊断报告进行相应的配置调整。")
    print(f"📝 如需要详细的设备配置教程，请查看上面的设备检查指南。")

if __name__ == '__main__':
    main() 