#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SLD样式文件管理服务
"""

import os
import uuid
import logging
from datetime import datetime
from models.sld_styles import SLDStyleModel
from services.geoserver_service import GeoServerService
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

class SLDStyleService:
    """SLD样式文件管理服务"""
    
    def __init__(self):
        self.sld_model = SLDStyleModel()
        self.geoserver_service = GeoServerService()
        self.sld_upload_dir = os.path.join(os.getcwd(), 'sld_styles')
        
        # 确保上传目录存在
        if not os.path.exists(self.sld_upload_dir):
            os.makedirs(self.sld_upload_dir)
    
    def initialize_database(self):
        """初始化数据库表"""
        try:
            # 创建SLD样式文件表
            self.sld_model.create_sld_styles_table()
            # 创建图层SLD样式映射表
            self.sld_model.create_layer_sld_mapping_table()
            logger.info("SLD样式数据库初始化完成")
            return True
        except Exception as e:
            logger.error(f"SLD样式数据库初始化失败: {str(e)}")
            return False
    
    def upload_sld_file(self, file, name, description, geometry_type, created_by=None):
        """上传SLD文件"""
        try:
            # 验证文件类型
            if not file.filename.lower().endswith('.sld'):
                raise ValueError("只支持.sld文件")
            
            # 验证几何类型
            valid_geometry_types = ['point', 'line', 'polygon']
            if geometry_type not in valid_geometry_types:
                raise ValueError(f"不支持的几何类型: {geometry_type}")
            
            # 读取文件内容，尝试多种编码
            file_bytes = file.read()
            content = None
            encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'latin-1']
            
            for encoding in encodings:
                try:
                    content = file_bytes.decode(encoding)
                    logger.info(f"成功使用 {encoding} 编码读取文件")
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                raise ValueError("无法解码SLD文件，请确保文件使用UTF-8、GBK或GB2312编码")
            
            # 验证SLD文件格式
            if not self._validate_sld_content(content, geometry_type):
                # 提供更详细的错误信息
                error_msg = f"SLD文件格式无效或与指定的几何类型({geometry_type})不匹配。请确保SLD文件包含正确的{geometry_type}符号化器。"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # 生成唯一文件名
            file_extension = os.path.splitext(file.filename)[1]
            unique_filename = f"{uuid.uuid4().hex}{file_extension}"
            file_path = os.path.join(self.sld_upload_dir, unique_filename)
            
            # 保存文件到磁盘
            file.seek(0)  # 重置文件指针
            with open(file_path, 'wb') as f:
                f.write(file.read())
            
            # 获取文件大小
            file_size = os.path.getsize(file_path)
            
            # 保存到数据库
            result = self.sld_model.insert_sld_style(
                name=name,
                description=description,
                geometry_type=geometry_type,
                file_path=file_path,
                file_size=file_size,
                content=content,
                created_by=created_by
            )
            
            logger.info(f"SLD文件上传成功: {name} ({geometry_type})")
            return result
            
        except Exception as e:
            logger.error(f"SLD文件上传失败: {str(e)}")
            raise
    
    def get_sld_styles(self, geometry_type=None, page=1, page_size=20):
        """获取SLD样式文件列表"""
        try:
            return self.sld_model.get_sld_styles(geometry_type, True, page, page_size)
        except Exception as e:
            logger.error(f"获取SLD样式文件列表失败: {str(e)}")
            raise
    
    def get_sld_style_by_id(self, style_id):
        """根据ID获取SLD样式文件"""
        try:
            return self.sld_model.get_sld_style_by_id(style_id)
        except Exception as e:
            logger.error(f"获取SLD样式文件失败: {str(e)}")
            raise
    
    def download_sld_file(self, style_id):
        """下载SLD文件"""
        try:
            style = self.sld_model.get_sld_style_by_id(style_id)
            if not style:
                raise ValueError("SLD样式文件不存在")
            
            if not os.path.exists(style['file_path']):
                raise ValueError("SLD文件不存在")
            
            return {
                'file_path': style['file_path'],
                'filename': f"{style['name']}.sld",
                'content': style['content']
            }
        except Exception as e:
            logger.error(f"下载SLD文件失败: {str(e)}")
            raise
    
    def delete_sld_style(self, style_id):
        """删除SLD样式文件"""
        try:
            style = self.sld_model.get_sld_style_by_id(style_id)
            if not style:
                raise ValueError("SLD样式文件不存在")
            
            # 删除物理文件
            if os.path.exists(style['file_path']):
                os.remove(style['file_path'])
            
            # 软删除数据库记录
            result = self.sld_model.delete_sld_style(style_id)
            
            logger.info(f"SLD样式文件删除成功: {style_id}")
            return result
        except Exception as e:
            logger.error(f"删除SLD样式文件失败: {str(e)}")
            raise
    
    def update_sld_style(self, style_id, style_config):
        """更新SLD样式文件"""
        try:
            # 获取现有样式
            style = self.sld_model.get_sld_style_by_id(style_id)
            if not style:
                raise ValueError("SLD样式文件不存在")
            
            # 验证几何类型
            valid_geometry_types = ['point', 'line', 'polygon']
            geometry_type = style_config.get('geometry_type', style['geometry_type'])
            if geometry_type not in valid_geometry_types:
                raise ValueError(f"不支持的几何类型: {geometry_type}")
            
            # 生成新的SLD内容
            from services.sld_template_service import SLDTemplateService
            sld_template_service = SLDTemplateService()
            
            new_sld_content = sld_template_service.generate_sld_from_style_config(style_config, style_config.get('name', style['name']))
            
            # 更新文件内容
            with open(style['file_path'], 'w', encoding='utf-8') as f:
                f.write(new_sld_content)
            
            # 更新数据库记录
            update_data = {
                'name': style_config.get('name', style['name']),
                'description': style_config.get('description', style['description']),
                'geometry_type': geometry_type,
                'content': new_sld_content,
                'updated_at': datetime.now()
            }
            
            result = self.sld_model.update_sld_style(style_id, update_data)
            
            logger.info(f"SLD样式文件更新成功: {style_id}")
            return result
            
        except Exception as e:
            logger.error(f"更新SLD样式文件失败: {str(e)}")
            raise

    def update_sld_style_content(self, style_id, data):
        """直接更新SLD样式文件的文本内容"""
        try:
            # 获取现有样式
            style = self.sld_model.get_sld_style_by_id(style_id)
            if not style:
                raise ValueError("SLD样式文件不存在")
            
            # 获取更新数据
            name = data.get('name', style['name'])
            description = data.get('description', style['description'])
            geometry_type = data.get('geometry_type', style['geometry_type'])
            content = data.get('content')
            
            if not content:
                raise ValueError("SLD内容不能为空")
            
            # 验证几何类型
            valid_geometry_types = ['point', 'line', 'polygon']
            if geometry_type not in valid_geometry_types:
                raise ValueError(f"不支持的几何类型: {geometry_type}")
            
            # 验证SLD内容格式
            if not self._validate_sld_content(content, geometry_type):
                raise ValueError("SLD文件格式无效或与指定的几何类型不匹配")
            
            # 更新文件内容
            with open(style['file_path'], 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 更新数据库记录
            update_data = {
                'name': name,
                'description': description,
                'geometry_type': geometry_type,
                'content': content,
                'updated_at': datetime.now()
            }
            
            result = self.sld_model.update_sld_style(style_id, update_data)
            
            logger.info(f"SLD样式文件内容更新成功: {style_id}")
            return result
            
        except Exception as e:
            logger.error(f"更新SLD样式文件内容失败: {str(e)}")
            raise
    
    def apply_sld_style_to_layer(self, layer_id, sld_style_id, applied_by=None):
        """将SLD样式应用到GeoServer图层"""
        try:
            # 获取SLD样式信息
            style = self.sld_model.get_sld_style_by_id(sld_style_id)
            if not style:
                raise ValueError("SLD样式文件不存在")
            
            # 获取图层信息
            layer_info = self._get_layer_info(layer_id)
            if not layer_info:
                raise ValueError("图层不存在")
            
            # 验证几何类型匹配
            #if not self._validate_geometry_type_match(style['geometry_type'], layer_info):
                #raise ValueError(f"SLD样式几何类型({style['geometry_type']})与图层几何类型不匹配")
            
            # 从文件系统读取原始SLD文件内容，确保内容完整和编码正确
            sld_content = None
            file_path = style.get('file_path')
            if file_path and os.path.exists(file_path):
                try:
                    # 尝试多种编码读取文件
                    encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312']
                    for encoding in encodings:
                        try:
                            with open(file_path, 'r', encoding=encoding) as f:
                                sld_content = f.read()
                            logger.info(f"成功从文件系统读取SLD文件，使用编码: {encoding}")
                            break
                        except UnicodeDecodeError:
                            continue
                    
                    if sld_content is None:
                        # 如果所有编码都失败，尝试二进制读取后解码
                        with open(file_path, 'rb') as f:
                            file_bytes = f.read()
                        for encoding in encodings:
                            try:
                                sld_content = file_bytes.decode(encoding)
                                logger.info(f"成功从二进制读取SLD文件，使用编码: {encoding}")
                                break
                            except UnicodeDecodeError:
                                continue
                except Exception as e:
                    logger.warning(f"从文件系统读取SLD文件失败: {str(e)}，将使用数据库中的内容")
            
            # 如果从文件系统读取失败，使用数据库中的内容
            if sld_content is None:
                sld_content = style.get('content')
                if not sld_content:
                    raise ValueError("SLD内容为空，无法应用样式")
                logger.info("使用数据库中的SLD内容")
            
            # 记录SLD内容的前500个字符用于调试
            logger.debug(f"准备应用的SLD内容前500字符: {sld_content[:500]}")
            
            # 应用样式到GeoServer
            success = self.geoserver_service.update_layer_style(
                workspace=layer_info['workspace_name'],
                layer=layer_info['name'],
                style_name=style['name'],
                sld_content=sld_content
            )
            
            if not success:
                raise Exception("应用样式到GeoServer失败")
            
            # 保存映射关系到数据库
            mapping_result = self.sld_model.apply_sld_style_to_layer(
                layer_id, sld_style_id, applied_by
            )
            
            logger.info(f"SLD样式应用成功: 图层{layer_id} -> 样式{style['name']}")
            return mapping_result
            
        except Exception as e:
            logger.error(f"应用SLD样式到图层失败: {str(e)}")
            raise
    
    def get_layer_sld_style(self, layer_id):
        """获取图层的当前SLD样式"""
        try:
            return self.sld_model.get_layer_sld_style(layer_id)
        except Exception as e:
            logger.error(f"获取图层SLD样式失败: {str(e)}")
            raise
    
    def remove_layer_sld_style(self, layer_id):
        """移除图层的SLD样式"""
        try:
            # 获取图层信息
            layer_info = self._get_layer_info(layer_id)
            if not layer_info:
                raise ValueError("图层不存在")
            
            # 从GeoServer移除样式
            success = self.geoserver_service.remove_layer_style(
                workspace=layer_info['workspace_name'],
                layer=layer_info['name']
            )
            
            if not success:
                raise Exception("从GeoServer移除样式失败")
            
            # 从数据库移除映射关系
            result = self.sld_model.remove_layer_sld_style(layer_id)
            
            logger.info(f"图层SLD样式移除成功: {layer_id}")
            return result
            
        except Exception as e:
            logger.error(f"移除图层SLD样式失败: {str(e)}")
            raise
    
    def _validate_sld_content(self, content, geometry_type):
        """验证SLD文件内容"""
        try:
            # 记录验证开始
            logger.info(f"开始验证SLD内容，几何类型: {geometry_type}")
            logger.debug(f"SLD内容前500字符: {content[:500]}")
            
            # 尝试解析XML，处理可能的编码问题
            try:
                root = ET.fromstring(content)
            except ET.ParseError as parse_error:
                # 尝试使用不同的编码
                try:
                    # 尝试UTF-8 with BOM
                    if content.startswith('\ufeff'):
                        content = content[1:]
                    root = ET.fromstring(content)
                except:
                    # 尝试其他编码
                    try:
                        content_utf8 = content.encode('latin-1').decode('utf-8')
                        root = ET.fromstring(content_utf8)
                    except:
                        logger.error(f"SLD XML解析失败: {str(parse_error)}")
                        raise parse_error
            
            # 记录根标签信息
            root_tag = root.tag
            logger.info(f"SLD根标签: {root_tag}")
            
            # 检查基本结构 - 支持多种命名空间
            valid_root_tags = [
                '{http://www.opengis.net/sld}StyledLayerDescriptor',
                '{http://www.opengis.net/se}StyledLayerDescriptor',
                'StyledLayerDescriptor'  # 无命名空间的情况
            ]
            
            # 更宽松的根标签检查
            if root_tag not in valid_root_tags:
                # 检查是否包含StyledLayerDescriptor（忽略命名空间）
                if 'StyledLayerDescriptor' not in root_tag:
                    logger.warning(f"SLD根标签不匹配: {root_tag}，但继续验证符号化器")
                    # 不直接返回False，继续验证符号化器
            
            # 定义多种命名空间变体的符号化器标签
            geometry_tag_variants = {
                'point': [
                    '{http://www.opengis.net/sld}PointSymbolizer',
                    '{http://www.opengis.net/se}PointSymbolizer',
                    'PointSymbolizer'
                ],
                'line': [
                    '{http://www.opengis.net/sld}LineSymbolizer',
                    '{http://www.opengis.net/se}LineSymbolizer',
                    'LineSymbolizer'
                ],
                'polygon': [
                    '{http://www.opengis.net/sld}PolygonSymbolizer',
                    '{http://www.opengis.net/se}PolygonSymbolizer',
                    'PolygonSymbolizer'
                ]
            }
            
            tag_variants = geometry_tag_variants.get(geometry_type)
            if not tag_variants:
                logger.warning(f"不支持的几何类型: {geometry_type}")
                return False
            
            # 尝试查找任意一种命名空间变体的符号化器
            for tag in tag_variants:
                try:
                    symbolizers = root.findall(f'.//{tag}')
                    if len(symbolizers) > 0:
                        logger.info(f"找到{geometry_type}符号化器: {tag} (共{len(symbolizers)}个)")
                        return True
                except Exception as e:
                    logger.debug(f"查找符号化器 {tag} 时出错: {str(e)}")
                    continue
            
            # 如果精确匹配失败，尝试使用通配符查找（忽略命名空间）
            # 使用XPath查找所有可能的符号化器
            try:
                all_symbolizers = root.findall('.//*[local-name()="PointSymbolizer" or local-name()="LineSymbolizer" or local-name()="PolygonSymbolizer"]')
                
                if len(all_symbolizers) > 0:
                    logger.info(f"找到 {len(all_symbolizers)} 个符号化器（通过local-name）")
                    # 检查找到的符号化器是否匹配几何类型
                    expected_local_name = {
                        'point': 'PointSymbolizer',
                        'line': 'LineSymbolizer',
                        'polygon': 'PolygonSymbolizer'
                    }.get(geometry_type)
                    
                    for symbolizer in all_symbolizers:
                        local_name = symbolizer.tag.split('}')[-1] if '}' in symbolizer.tag else symbolizer.tag
                        logger.debug(f"检查符号化器: {symbolizer.tag} (本地名称: {local_name})")
                        if local_name == expected_local_name:
                            logger.info(f"通过本地名称找到{geometry_type}符号化器: {symbolizer.tag}")
                            return True
            except Exception as e:
                logger.debug(f"使用local-name查找符号化器时出错: {str(e)}")
            
            # 最后尝试：遍历所有元素查找符号化器
            try:
                for elem in root.iter():
                    tag_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                    expected_tag = {
                        'point': 'PointSymbolizer',
                        'line': 'LineSymbolizer',
                        'polygon': 'PolygonSymbolizer'
                    }.get(geometry_type)
                    
                    if tag_name == expected_tag:
                        logger.info(f"通过遍历找到{geometry_type}符号化器: {elem.tag}")
                        return True
            except Exception as e:
                logger.debug(f"遍历元素查找符号化器时出错: {str(e)}")
            
            # 如果所有方法都失败，记录详细信息
            logger.warning(f"未找到{geometry_type}类型的符号化器")
            logger.debug(f"根标签: {root_tag}")
            logger.debug(f"所有子元素标签: {[elem.tag for elem in root.iter()][:20]}")
            return False
            
        except ET.ParseError as e:
            logger.error(f"SLD XML解析失败: {str(e)}")
            logger.error(f"错误位置: 行 {e.position[0] if hasattr(e, 'position') else '未知'}")
            return False
        except Exception as e:
            logger.error(f"SLD内容验证失败: {str(e)}", exc_info=True)
            return False
    
    def _get_layer_info(self, layer_id):
        """获取图层信息"""
        try:
            from services.layer_service import LayerService
            
            layer_service = LayerService()
            layer_info = layer_service.get_layer_by_id(layer_id)
            
            if layer_info:
                return {
                    'id': layer_info['id'],
                    'name': layer_info['name'],
                    'workspace_id': layer_info['workspace_id'],
                    'workspace_name': layer_info['workspace_name'],
                    'layer_type': layer_info.get('layer_type'),
                    'geometry_type': self._get_geometry_type_from_layer(layer_info)
                }
            return None
            
        except Exception as e:
            logger.error(f"获取图层信息失败: {str(e)}")
            return None
    
    def _get_geometry_type_from_layer(self, layer_info):
        """从图层信息中获取几何类型"""
        try:
            logger.info(f"开始获取图层几何类型，图层信息: {layer_info}")
            
            # 如果有文件信息，从文件中获取几何类型
            if layer_info.get('file_id'):
                from models.db import execute_query
                query = "SELECT geometry_type FROM files WHERE id = %s"
                result = execute_query(query, (layer_info['file_id'],))
                if result and result[0].get('geometry_type'):
                    geom_type = result[0]['geometry_type']
                    logger.info(f"从文件获取几何类型: {geom_type}")
                    return geom_type
                else:
                    logger.warning(f"文件 {layer_info['file_id']} 没有几何类型信息")
            
            # 如果有要素类型信息，从属性中推断几何类型
            if layer_info.get('attributes'):
                attributes = layer_info['attributes']
                if isinstance(attributes, str):
                    import json
                    attributes = json.loads(attributes)
                
                logger.info(f"图层属性: {attributes}")
                
                # 查找几何字段
                for attr in attributes:
                    if attr.get('type', '').lower() in ['point', 'linestring', 'polygon', 'multipoint', 'multilinestring', 'multipolygon']:
                        geom_type = attr['type'].lower()
                        if geom_type.startswith('multi'):
                            geom_type = geom_type[5:]  # 去掉'multi'前缀
                        logger.info(f"从属性推断几何类型: {geom_type}")
                        return geom_type
            
            # 根据文件名或文件类型推断几何类型
            if layer_info.get('file_name'):
                file_name = layer_info['file_name'].lower()
                if any(keyword in file_name for keyword in ['点', 'point', 'poi']):
                    logger.info("根据文件名推断为点图层")
                    return 'point'
                elif any(keyword in file_name for keyword in ['线', 'line', 'road', 'river']):
                    logger.info("根据文件名推断为线图层")
                    return 'line'
                elif any(keyword in file_name for keyword in ['面', 'polygon', 'area', 'zone', '范围', '区域']):
                    logger.info("根据文件名推断为面图层")
                    return 'polygon'
            
            # 默认返回point
            logger.info("使用默认几何类型: point")
            return 'point'
            
        except Exception as e:
            logger.error(f"获取几何类型失败: {str(e)}")
            return 'point'
    
    def _validate_geometry_type_match(self, sld_geometry_type, layer_info):
        """验证SLD几何类型与图层几何类型是否匹配"""
        try:
            layer_geometry_type = layer_info.get('geometry_type', 'point')
            
            # 添加调试信息
            logger.info(f"验证几何类型匹配: SLD类型={sld_geometry_type}, 图层类型={layer_geometry_type}")
            
            # 几何类型映射
            geometry_mapping = {
                'point': ['point', 'multipoint'],
                'line': ['linestring', 'multilinestring'],
                'polygon': ['polygon', 'multipolygon']
            }
            
            # 检查SLD几何类型是否与图层几何类型匹配
            if sld_geometry_type in geometry_mapping:
                valid_types = geometry_mapping[sld_geometry_type]
                is_match = layer_geometry_type.lower() in valid_types
                logger.info(f"几何类型匹配结果: {is_match}, 有效类型: {valid_types}")
                return is_match
            
            logger.warning(f"未知的SLD几何类型: {sld_geometry_type}")
            return False
            
        except Exception as e:
            logger.error(f"几何类型验证失败: {str(e)}")
            return False
