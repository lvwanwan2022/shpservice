#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from typing import Dict, Any, Optional

class SLDTemplateService:
    """SLD模板服务类，用于根据前端样式配置生成标准的SLD文件"""
    
    def __init__(self):
        pass
    
    def generate_sld_from_style_config(self, style_config: Dict[str, Any], style_name: str) -> str:
        """
        根据前端样式配置生成SLD文件
        
        Args:
            style_config: 前端样式配置
            style_name: 样式名称
            
        Returns:
            生成的SLD XML字符串
        """
        # 设置默认样式
        default_styles = {
            'point': {
                'color': '#FFEE00',
                'size': 4,
                'shape': 'square',
                'opacity': 1.0
            },
            'line': {
                'color': '#D3C2A8',
                'width': 1.0,
                'style': 'solid',
                'opacity': 1.0
            },
            'polygon': {
                'fillColor': '#DDDDDD',
                'fillOpacity': 1.0,
                'strokeColor': None,
                'strokeWidth': 0,
                'strokeOpacity': 1.0
            }
        }
        
        # 合并用户配置与默认配置
        point_style = {**default_styles['point'], **style_config.get('point', {})}
        line_style = {**default_styles['line'], **style_config.get('line', {})}
        polygon_style = {**default_styles['polygon'], **style_config.get('polygon', {})}
        
        # 确定主要几何类型并生成对应的SLD
        if 'point' in style_config:
            return self._generate_point_sld(style_name, point_style)
        elif 'line' in style_config:
            return self._generate_line_sld(style_name, line_style)
        elif 'polygon' in style_config:
            return self._generate_polygon_sld(style_name, polygon_style)
        else:
            # 如果没有指定类型，生成通用样式
            return self._generate_generic_sld(style_name, point_style, line_style, polygon_style)
    
    def _generate_point_sld(self, style_name: str, point_style: Dict) -> str:
        """生成点样式SLD"""
        
        # 获取点形状的WellKnownName
        shape_map = {
            'circle': 'circle',
            'square': 'square',
            'triangle': 'triangle',
            'star': 'star',
            'cross': 'cross',
            'x': 'x'
        }
        
        well_known_name = shape_map.get(point_style.get('shape', 'square'), 'square')
        
        sld_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.0.0" 
 xsi:schemaLocation="http://www.opengis.net/sld StyledLayerDescriptor.xsd" 
 xmlns="http://www.opengis.net/sld" 
 xmlns:ogc="http://www.opengis.net/ogc" 
 xmlns:xlink="http://www.w3.org/1999/xlink" 
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <!-- a Named Layer is the basic building block of an SLD document -->
  <NamedLayer>
    <Name>{style_name}</Name>
    <UserStyle>
    <!-- Styles can have names, titles and abstracts -->
      <Title>Custom Point Style</Title>
      <Abstract>A sample style for point features</Abstract>
      <!-- FeatureTypeStyles describe how to render different features -->
      <!-- A FeatureTypeStyle for rendering points -->
      <FeatureTypeStyle>
        <Rule>
          <Name>point_rule</Name>
          <Title>Point Style</Title>
          <Abstract>Point symbolizer</Abstract>
            <PointSymbolizer>
              <Graphic>
                <Mark>
                  <WellKnownName>{well_known_name}</WellKnownName>
                  <Fill>
                    <CssParameter name="fill">{point_style['color']}</CssParameter>
                    <CssParameter name="fill-opacity">{point_style['opacity']}</CssParameter>
                  </Fill>
                </Mark>
              <Size>{point_style['size']}</Size>
            </Graphic>
          </PointSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>'''
        
        return sld_content
    
    def _generate_line_sld(self, style_name: str, line_style: Dict) -> str:
        """生成线样式SLD"""
        
        # 处理虚线样式
        dash_array = self._get_stroke_dash_array(line_style.get('style', 'solid'))
        dash_param = f'              <CssParameter name="stroke-dasharray">{dash_array}</CssParameter>\n' if dash_array else ''
        
        sld_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld"
    xmlns:sld="http://www.opengis.net/sld"
    xmlns:ogc="http://www.opengis.net/ogc"
    xmlns:gml="http://www.opengis.net/gml"
    version="1.0.0">
  <NamedLayer>
    <Name>{style_name}</Name>
    <UserStyle>
      <Title>Custom Line Style</Title>
      <Abstract>A sample style for line features</Abstract>
      <FeatureTypeStyle>
        <Rule>
          <Title>Line Style</Title>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">{line_style['color']}</CssParameter>
              <CssParameter name="stroke-width">{line_style['width']}</CssParameter>
              <CssParameter name="stroke-opacity">{line_style['opacity']}</CssParameter>
{dash_param}            </Stroke>
          </LineSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>'''
        
        return sld_content
    
    def _generate_polygon_sld(self, style_name: str, polygon_style: Dict) -> str:
        """生成面样式SLD"""
        
        # 处理描边
        stroke_section = ""
        if polygon_style.get('strokeColor') and polygon_style.get('strokeWidth', 0) > 0:
            stroke_section = f'''
            <Stroke>
              <CssParameter name="stroke">{polygon_style['strokeColor']}</CssParameter>
              <CssParameter name="stroke-width">{polygon_style['strokeWidth']}</CssParameter>
              <CssParameter name="stroke-opacity">{polygon_style['strokeOpacity']}</CssParameter>
            </Stroke>'''
        
        sld_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.0.0" xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc"
  xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
  <NamedLayer>
    <Name>{style_name}</Name>
    <UserStyle>
    <Title>Custom Polygon Style</Title>
    <Abstract>A sample style for polygon features</Abstract>
      <FeatureTypeStyle>
        <Rule>
          <PolygonSymbolizer>
            <Fill>
              <CssParameter name="fill">
                <ogc:Literal>{polygon_style['fillColor']}</ogc:Literal>
              </CssParameter>
              <CssParameter name="fill-opacity">
                <ogc:Literal>{polygon_style['fillOpacity']}</ogc:Literal>
              </CssParameter>
            </Fill>{stroke_section}
          </PolygonSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>'''
        
        return sld_content
    
    def _generate_generic_sld(self, style_name: str, point_style: Dict, line_style: Dict, polygon_style: Dict) -> str:
        """生成通用样式SLD（包含点、线、面）"""
        
        # 如果需要支持多种几何类型，生成包含多个规则的SLD
        # 这里简化处理，默认生成点样式
        return self._generate_point_sld(style_name, point_style)
    
    def _get_stroke_dash_array(self, line_style: str) -> Optional[str]:
        """获取线型对应的虚线数组"""
        dash_patterns = {
            'solid': None,
            'dashed': '5 5',
            'dotted': '2 2',
            'dashdot': '5 2 2 2',
            'longdash': '10 5',
            'shortdash': '3 3'
        }
        return dash_patterns.get(line_style, None)
    
    def generate_simple_sld_template(self, geometry_type: str, style_name: str) -> str:
        """
        生成简单的SLD模板（基于几何类型）
        
        Args:
            geometry_type: 几何类型 ('point', 'line', 'polygon')
            style_name: 样式名称
            
        Returns:
            SLD XML字符串
        """
        if geometry_type.lower() == 'point':
            return self._generate_simple_point_sld(style_name)
        elif geometry_type.lower() == 'line':
            return self._generate_simple_line_sld(style_name)
        elif geometry_type.lower() == 'polygon':
            return self._generate_simple_polygon_sld(style_name)
        else:
            raise ValueError(f"不支持的几何类型: {geometry_type}")
    
    def _generate_simple_point_sld(self, style_name: str) -> str:
        """生成简单的点样式SLD"""
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.0.0" 
 xsi:schemaLocation="http://www.opengis.net/sld StyledLayerDescriptor.xsd" 
 xmlns="http://www.opengis.net/sld" 
 xmlns:ogc="http://www.opengis.net/ogc" 
 xmlns:xlink="http://www.w3.org/1999/xlink" 
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <NamedLayer>
    <Name>{style_name}</Name>
    <UserStyle>
      <Title>Default Point Style</Title>
      <Abstract>A simple point style</Abstract>
      <FeatureTypeStyle>
        <Rule>
          <PointSymbolizer>
            <Graphic>
              <Mark>
                <WellKnownName>square</WellKnownName>
                <Fill>
                  <CssParameter name="fill">#FFEE00</CssParameter>
                </Fill>
              </Mark>
              <Size>4</Size>
            </Graphic>
          </PointSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>'''
    
    def _generate_simple_line_sld(self, style_name: str) -> str:
        """生成简单的线样式SLD"""
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld"
    xmlns:sld="http://www.opengis.net/sld"
    xmlns:ogc="http://www.opengis.net/ogc"
    xmlns:gml="http://www.opengis.net/gml"
    version="1.0.0">
  <NamedLayer>
    <Name>{style_name}</Name>
    <UserStyle>
      <Title>Default Line Style</Title>
      <Abstract>A simple line style</Abstract>
      <FeatureTypeStyle>
        <Rule>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#D3C2A8</CssParameter>
              <CssParameter name="stroke-width">1.0</CssParameter>
            </Stroke>
          </LineSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>'''
    
    def _generate_simple_polygon_sld(self, style_name: str) -> str:
        """生成简单的面样式SLD"""
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.0.0" xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc"
  xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
  <NamedLayer>
    <Name>{style_name}</Name>
    <UserStyle>
    <Title>Default Polygon Style</Title>
    <Abstract>A simple polygon style</Abstract>
      <FeatureTypeStyle>
        <Rule>
          <PolygonSymbolizer>
            <Fill>
              <CssParameter name="fill">
                <ogc:Literal>#DDDDDD</ogc:Literal>
              </CssParameter>
              <CssParameter name="fill-opacity">
                <ogc:Literal>1.0</ogc:Literal>
              </CssParameter>
            </Fill>
          </PolygonSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>''' 