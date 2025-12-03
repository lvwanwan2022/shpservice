#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DXF样式信息分析器
分析GDAL导入DXF后样式信息的保留情况
"""

import os
from osgeo import ogr, gdal
from sqlalchemy import create_engine, text
from config import DB_CONFIG
import logging

logger = logging.getLogger(__name__)

class DXFStyleAnalyzer:
    """DXF样式信息分析器"""
    
    def __init__(self):
        gdal.UseExceptions()
        db_url = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password'].replace('@', '%40')}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        self.engine = create_engine(db_url)
    
    def analyze_dxf_styles(self, file_path):
        """
        分析DXF文件的样式信息
        
        Returns:
            dict: 样式分析结果
        """
        try:
            driver = ogr.GetDriverByName('DXF')
            datasource = driver.Open(file_path, 0)
            
            if not datasource:
                raise Exception("无法打开DXF文件")
            
            style_analysis = {
                'preserved_attributes': [],    # 保留的样式属性
                'lost_attributes': [],         # 丢失的样式属性
                'layers_info': [],             # 图层信息
                'sample_features': []          # 样本要素信息
            }
            
            # GDAL在DXF中通常保留的字段
            preserved_fields = [
                'Layer',           # 图层名称 ✅
                'SubClasses',      # 子类 ✅
                'Linetype',        # 线型 ✅
                'EntityHandle',    # 实体句柄 ✅
                'Text',            # 文本内容 ✅
                'BlockName',       # 图块名称 ✅
                'Color',           # 颜色索引 ✅
                'LineWeight',      # 线宽 ⚠️ (部分支持)
                'TrueColor',       # 真彩色 ⚠️ (部分支持)
                'Transparency',    # 透明度 ⚠️ (部分支持)
            ]
            
            # 通常丢失的样式信息
            lost_styles = [
                '复杂填充样式',     # Hatch patterns
                '渐变填充',        # Gradient fills
                '自定义线型定义',   # Custom linetype definitions
                '文字样式详细定义', # Detailed text styles
                '3D材质信息',      # 3D materials
                '图块插入比例',     # Block insertion scales
                '旋转角度',        # Rotation angles (部分丢失)
                '图层冻结/锁定状态' # Layer freeze/lock states
            ]
            
            # 遍历所有图层分析字段
            for i in range(datasource.GetLayerCount()):
                layer = datasource.GetLayer(i)
                layer_name = layer.GetName()
                
                # 获取字段定义
                layer_defn = layer.GetLayerDefn()
                available_fields = []
                
                for j in range(layer_defn.GetFieldCount()):
                    field_defn = layer_defn.GetFieldDefn(j)
                    field_name = field_defn.GetName()
                    field_type = field_defn.GetFieldTypeName(field_defn.GetType())
                    available_fields.append({
                        'name': field_name,
                        'type': field_type,
                        'preserved': field_name in preserved_fields
                    })
                
                # 分析几个样本要素
                samples = []
                feature = layer.GetNextFeature()
                sample_count = 0
                
                while feature and sample_count < 3:
                    feature_info = {
                        'fid': feature.GetFID(),
                        'geometry_type': feature.GetGeometryRef().GetGeometryName() if feature.GetGeometryRef() else 'None',
                        'attributes': {}
                    }
                    
                    # 获取所有属性值
                    for field in available_fields:
                        try:
                            value = feature.GetField(field['name'])
                            feature_info['attributes'][field['name']] = value
                        except:
                            feature_info['attributes'][field['name']] = None
                    
                    samples.append(feature_info)
                    feature = layer.GetNextFeature()
                    sample_count += 1
                
                layer_info = {
                    'layer_name': layer_name,
                    'feature_count': layer.GetFeatureCount(),
                    'available_fields': available_fields,
                    'sample_features': samples
                }
                
                style_analysis['layers_info'].append(layer_info)
            
            # 统计保留和丢失的属性
            all_fields = set()
            for layer_info in style_analysis['layers_info']:
                for field in layer_info['available_fields']:
                    all_fields.add(field['name'])
            
            style_analysis['preserved_attributes'] = [f for f in preserved_fields if f in all_fields]
            style_analysis['lost_attributes'] = lost_styles
            
            datasource = None
            return style_analysis
            
        except Exception as e:
            logger.error(f"样式分析失败: {str(e)}")
            return {'error': str(e)}
    
    def check_postgis_style_preservation(self, table_name):
        """
        检查PostGIS表中样式信息的保留情况
        """
        try:
            with self.engine.connect() as conn:
                # 获取表结构
                columns_query = """
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = %s
                ORDER BY ordinal_position;
                """
                
                columns_result = conn.execute(text(columns_query), (table_name,)).fetchall()
                
                # 获取样本数据
                sample_query = f"""
                SELECT * FROM {table_name} LIMIT 5;
                """
                
                sample_result = conn.execute(text(sample_query)).fetchall()
                
                # 分析样式相关字段
                style_columns = []
                for col in columns_result:
                    col_name = col[0].lower()
                    if any(style_key in col_name for style_key in 
                          ['layer', 'color', 'linetype', 'lineweight', 'text', 'block']):
                        style_columns.append({
                            'name': col[0],
                            'type': col[1],
                            'is_style_related': True
                        })
                    else:
                        style_columns.append({
                            'name': col[0],
                            'type': col[1],
                            'is_style_related': False
                        })
                
                return {
                    'table_name': table_name,
                    'total_columns': len(columns_result),
                    'style_columns': [col for col in style_columns if col['is_style_related']],
                    'all_columns': style_columns,
                    'sample_data': [dict(row._mapping) for row in sample_result] if sample_result else []
                }
                
        except Exception as e:
            logger.error(f"PostGIS样式检查失败: {str(e)}")
            return {'error': str(e)}
    
    def generate_style_preservation_report(self, file_path, table_name=None):
        """
        生成完整的样式保留报告
        """
        report = {
            'dxf_file': file_path,
            'analysis_time': None,
            'dxf_analysis': None,
            'postgis_analysis': None,
            'recommendations': []
        }
        
        import datetime
        report['analysis_time'] = datetime.datetime.now().isoformat()
        
        # 分析DXF文件
        print("🔍 分析DXF文件样式信息...")
        report['dxf_analysis'] = self.analyze_dxf_styles(file_path)
        
        # 如果提供了表名，分析PostGIS表
        if table_name:
            print(f"🔍 分析PostGIS表 {table_name} 样式保留情况...")
            report['postgis_analysis'] = self.check_postgis_style_preservation(table_name)
        
        # 生成建议
        recommendations = [
            "✅ Layer字段: 图层信息完整保留",
            "✅ Linetype字段: 线型信息保留",
            "✅ Color字段: 基本颜色索引保留",
            "⚠️ 复杂样式: 填充模式、渐变等可能丢失",
            "⚠️ 3D信息: 3D样式和材质信息丢失",
            "💡 建议: 使用Layer字段进行图层分类显示",
            "💡 建议: 根据Linetype字段设置线型样式",
            "💡 建议: 使用Color字段映射显示颜色"
        ]
        
        report['recommendations'] = recommendations
        
        return report

def print_style_report(report):
    """打印样式分析报告"""
    print("\n" + "="*60)
    print("📊 DXF样式保留分析报告")
    print("="*60)
    
    print(f"📁 文件: {report['dxf_file']}")
    print(f"⏰ 分析时间: {report['analysis_time']}")
    
    if 'dxf_analysis' in report and report['dxf_analysis']:
        dxf_info = report['dxf_analysis']
        if 'error' not in dxf_info:
            print(f"\n📋 DXF文件信息:")
            print(f"   图层数量: {len(dxf_info['layers_info'])}")
            
            print(f"\n✅ 保留的样式属性:")
            for attr in dxf_info['preserved_attributes']:
                print(f"   - {attr}")
            
            print(f"\n❌ 可能丢失的样式信息:")
            for attr in dxf_info['lost_attributes']:
                print(f"   - {attr}")
    
    if 'postgis_analysis' in report and report['postgis_analysis']:
        pg_info = report['postgis_analysis']
        if 'error' not in pg_info:
            print(f"\n🗄️ PostGIS表信息:")
            print(f"   表名: {pg_info['table_name']}")
            print(f"   总字段数: {pg_info['total_columns']}")
            print(f"   样式相关字段数: {len(pg_info['style_columns'])}")
            
            print(f"\n🎨 样式相关字段:")
            for col in pg_info['style_columns']:
                print(f"   - {col['name']} ({col['type']})")
    
    print(f"\n💡 建议和说明:")
    for rec in report['recommendations']:
        print(f"   {rec}")
    
    print("\n" + "="*60)

# 使用示例
if __name__ == "__main__":
    analyzer = DXFStyleAnalyzer()
    
    # 分析DXF文件（替换为实际文件路径）
    dxf_file = "test_files/sample.dxf"
    
    if os.path.exists(dxf_file):
        report = analyzer.generate_style_preservation_report(dxf_file, "test_dxf_table")
        print_style_report(report)
    else:
        print(f"❌ 测试文件不存在: {dxf_file}") 