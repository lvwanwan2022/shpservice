#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TIF Martin服务类
将TIF文件使用GDAL转换为MBTiles格式，然后通过Martin发布为瓦片服务
"""

import os
import json
import uuid
import tempfile
import shutil
import subprocess
from pathlib import Path
from models.db import execute_query, insert_with_snowflake_id
from config import DB_CONFIG, MARTIN_CONFIG, FILE_STORAGE
import logging

# 尝试导入GDAL
try:
    from osgeo import gdal, osr
    GDAL_AVAILABLE = True
    # 配置GDAL以避免输出过多信息
    gdal.UseExceptions()
    print("✅ GDAL Python绑定可用")
except ImportError:
    GDAL_AVAILABLE = False
    print("⚠️ GDAL Python绑定不可用，将尝试使用命令行工具")

logger = logging.getLogger(__name__)

class TifMartinService:
    """TIF Martin服务类，提供TIF到MBTiles转换和Martin服务发布功能
    
    注意：保持原始坐标系，不强制转换为Web Mercator
    """
    
    def __init__(self):
        """初始化服务"""
        self.upload_folder = FILE_STORAGE['upload_folder']
        self.mbtiles_folder = os.path.join(self.upload_folder, 'mbtiles')
        self.temp_folder = FILE_STORAGE.get('temp_folder', 'temp')
        
        # 确保目录存在
        os.makedirs(self.mbtiles_folder, exist_ok=True)
        os.makedirs(self.temp_folder, exist_ok=True)
        
        print("✅ TIF Martin服务初始化完成（智能坐标系模式）")
    
    def _get_file_coordinate_system(self, file_id):
        """从数据库获取文件的坐标系信息"""
        try:
            sql = "SELECT coordinate_system FROM files WHERE id = %s"
            result = execute_query(sql, (file_id,))
            if result and result[0]['coordinate_system']:
                return result[0]['coordinate_system']
            return None
        except Exception as e:
            print(f"⚠️ 获取数据库坐标系信息失败: {str(e)}")
            return None
    
    def _determine_profile_and_conversion(self, tif_info, db_coordinate_system):
        """根据坐标系信息确定GDAL2Tiles profile和是否需要转换"""
        try:
            # 获取文件中的坐标系信息
            file_coord_system = tif_info['info'].get('coordinate_system', {})
            file_epsg = file_coord_system.get('epsg')
            
            print(f"🔍 分析坐标系信息:")
            print(f"  - 文件EPSG: {file_epsg}")
            print(f"  - 数据库坐标系: {db_coordinate_system}")
            
            # 支持的坐标系列表
            supported_coordinates = {
                'EPSG:4326': 'geodetic',  # WGS84地理坐标系
                'EPSG:3857': 'mercator',   # Web Mercator投影
                'EPSG:900913': 'mercator', # Google Mercator (旧版本)
                'EPSG:4490': 'geodetic',   # CGCS2000地理坐标系
                'EPSG:4214': 'geodetic',   # 北京54地理坐标系
                'EPSG:4610': 'geodetic',   # 西安80地理坐标系
            }
            
            # 确定目标坐标系
            target_coordinate = None
            if db_coordinate_system:
                # 优先使用数据库中的坐标系
                target_coordinate = db_coordinate_system
                print(f"✅ 使用数据库中的坐标系: {target_coordinate}")
            elif file_epsg:
                # 如果数据库没有，使用文件中的坐标系
                target_coordinate = f"EPSG:{file_epsg}"
                print(f"✅ 使用文件中的坐标系: {target_coordinate}")
            else:
                # 默认使用WGS84
                target_coordinate = 'EPSG:4326'
                print(f"⚠️ 未检测到坐标系，使用默认WGS84: {target_coordinate}")
            
            # 确定profile
            profile = supported_coordinates.get(target_coordinate, 'raster')
            
            # 判断是否需要坐标系转换
            needs_conversion = False
            conversion_reason = ""
            
            if file_epsg and target_coordinate:
                file_epsg_full = f"EPSG:{file_epsg}" if not file_epsg.startswith('EPSG:') else file_epsg
                if file_epsg_full != target_coordinate:
                    needs_conversion = True
                    conversion_reason = f"文件坐标系({file_epsg_full})与目标坐标系({target_coordinate})不匹配"
            
            # 特殊处理：如果目标坐标系不在支持列表中，使用raster profile
            if target_coordinate not in supported_coordinates:
                profile = 'raster'
                conversion_reason = f"目标坐标系({target_coordinate})不在标准支持列表中，使用raster profile保持原始投影"
            
            result = {
                'profile': profile,
                'target_coordinate': target_coordinate,
                'needs_conversion': needs_conversion,
                'conversion_reason': conversion_reason,
                'file_epsg': file_epsg,
                'db_coordinate_system': db_coordinate_system
            }
            
            print(f"📋 坐标系分析结果:")
            print(f"  - Profile: {profile}")
            print(f"  - 目标坐标系: {target_coordinate}")
            print(f"  - 需要转换: {needs_conversion}")
            if conversion_reason:
                print(f"  - 转换原因: {conversion_reason}")
            
            return result
            
        except Exception as e:
            print(f"❌ 坐标系分析失败: {str(e)}")
            # 返回默认配置
            return {
                'profile': 'raster',
                'target_coordinate': 'EPSG:4326',
                'needs_conversion': False,
                'conversion_reason': f"分析失败，使用默认配置: {str(e)}",
                'file_epsg': None,
                'db_coordinate_system': db_coordinate_system
            }
    
    def _smart_preprocess_tif(self, input_path, temp_dir, tif_info, db_coordinate_system):
        """智能预处理TIF文件，根据坐标系信息决定是否转换"""
        try:
            # 分析坐标系和确定处理策略
            analysis = self._determine_profile_and_conversion(tif_info, db_coordinate_system)
            
            info = tif_info['info']
            processed_path = os.path.join(temp_dir, 'processed.tif')
            
            # 检查是否有地理参考信息
            has_georeference = info.get('has_georeference', False)
            
            if not has_georeference:
                print("⚠️ 文件缺少地理参考信息，进行基本优化")
                if GDAL_AVAILABLE:
                    translate_options = gdal.TranslateOptions(
                        creationOptions=['TILED=YES', 'COMPRESS=LZW']
                    )
                    gdal.Translate(processed_path, input_path, options=translate_options)
                else:
                    cmd = [
                        'gdal_translate',
                        '-co', 'TILED=YES',
                        '-co', 'COMPRESS=LZW',
                        input_path,
                        processed_path
                    ]
                    subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                return processed_path
            
            # 如果需要坐标系转换
            if analysis['needs_conversion']:
                print(f"🔄 执行坐标系转换: {analysis['conversion_reason']}")
                
                if GDAL_AVAILABLE:
                    # 使用Python GDAL进行坐标系转换
                    warp_options = gdal.WarpOptions(
                        dstSRS=analysis['target_coordinate'],
                        resampleAlg=gdal.GRA_Bilinear,
                        creationOptions=['TILED=YES', 'COMPRESS=LZW']
                    )
                    gdal.Warp(processed_path, input_path, options=warp_options)
                else:
                    # 使用命令行工具进行坐标系转换
                    cmd = [
                        'gdalwarp',
                        '-t_srs', analysis['target_coordinate'],
                        '-r', 'bilinear',
                        '-co', 'TILED=YES',
                        '-co', 'COMPRESS=LZW',
                        input_path,
                        processed_path
                    ]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                    if result.returncode != 0:
                        print(f"⚠️ 坐标系转换失败: {result.stderr}")
                        return input_path
                
                print(f"✅ 坐标系转换完成: {analysis['target_coordinate']}")
                return processed_path
            else:
                # 不需要转换，进行基本优化
                print(f"📋 保持原始坐标系，进行基本优化")
                if GDAL_AVAILABLE:
                    translate_options = gdal.TranslateOptions(
                        creationOptions=['TILED=YES', 'COMPRESS=LZW']
                    )
                    gdal.Translate(processed_path, input_path, options=translate_options)
                else:
                    cmd = [
                        'gdal_translate',
                        '-co', 'TILED=YES',
                        '-co', 'COMPRESS=LZW',
                        input_path,
                        processed_path
                    ]
                    subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                
                return processed_path
                
        except Exception as e:
            print(f"⚠️ 智能预处理失败，使用原始文件: {str(e)}")
            return input_path
        
    def tif_to_mbtiles_and_publish(self, file_id, file_path, original_filename, user_id=None, max_zoom=20):
        """将TIF文件转换为MBTiles并发布为Martin服务
        
        Args:
            file_id: 文件ID
            file_path: TIF文件路径
            original_filename: 原始文件名
            user_id: 用户ID
            max_zoom: 最大缩放级别，默认20
            
        Returns:
            发布结果字典
        """
        temp_dir = None
        try:
            print(f"🔄 开始处理TIF文件: {original_filename}")
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return {
                    'success': False,
                    'error': f'TIF文件不存在: {file_path}'
                }
            
            # 检查GDAL工具是否可用
            if not self._check_gdal_tools():
                return {
                    'success': False,
                    'error': 'GDAL工具不可用，请确保已安装GDAL并添加到PATH'
                }
            
            # 获取数据库中的坐标系信息
            db_coordinate_system = self._get_file_coordinate_system(file_id)
            print(f"📊 数据库中的坐标系信息: {db_coordinate_system}")
            
            # 生成MBTiles文件名
            file_uuid = uuid.uuid4().hex
            mbtiles_filename = f"{file_uuid}.mbtiles"
            mbtiles_path = os.path.join(self.mbtiles_folder, mbtiles_filename)
            
            # 创建临时工作目录
            temp_dir = tempfile.mkdtemp(prefix='tif_conversion_')
            print(f"📁 临时工作目录: {temp_dir}")
            
            # 第一步：验证TIF文件
            tif_info = self._validate_tif_file(file_path)
            if not tif_info['valid']:
                return {
                    'success': False,
                    'error': f'TIF文件验证失败: {tif_info["error"]}'
                }
            
            print(f"📊 TIF文件信息: {tif_info['info']}")
            
            # 第二步：智能坐标系处理
            processed_tif_path = self._smart_preprocess_tif(
                file_path, temp_dir, tif_info, db_coordinate_system
            )
            
            # 第三步：使用GDAL将TIF转换为MBTiles
            # 获取坐标系分析结果
            analysis = self._determine_profile_and_conversion(tif_info, db_coordinate_system)
            
            conversion_result = self._convert_tif_to_mbtiles(
                processed_tif_path, 
                mbtiles_path, 
                max_zoom,
                temp_dir,
                analysis['profile']  # 传递分析得到的profile
            )
            
            if not conversion_result['success']:
                return {
                    'success': False,
                    'error': f'TIF转MBTiles失败: {conversion_result["error"]}'
                }
            
            print(f"✅ MBTiles文件已生成: {mbtiles_path}")
            
            # 第四步：验证生成的MBTiles文件
            mbtiles_info = self._validate_mbtiles_file(mbtiles_path)
            if not mbtiles_info['valid']:
                return {
                    'success': False,
                    'error': f'生成的MBTiles文件无效: {mbtiles_info["error"]}'
                }
            
            # 第五步：发布为Martin服务
            publish_result = self._publish_mbtiles_to_martin(
                file_id=file_id,
                mbtiles_path=mbtiles_path,
                original_filename=original_filename,
                user_id=user_id,
                tif_info=tif_info,
                mbtiles_info=mbtiles_info,
                conversion_stats=conversion_result['stats'],
                coordinate_analysis=analysis  # 传递坐标系分析结果
            )
            
            if not publish_result['success']:
                # 如果发布失败，删除生成的MBTiles文件
                if os.path.exists(mbtiles_path):
                    os.remove(mbtiles_path)
                return publish_result
            
            print(f"🎉 TIF文件成功转换并发布为Martin服务")
            
            return {
                'success': True,
                'message': 'TIF文件成功转换为MBTiles并发布为Martin服务',
                'mbtiles_path': mbtiles_path,
                'mbtiles_filename': mbtiles_filename,
                'tif_info': tif_info['info'],
                'mbtiles_info': mbtiles_info['info'],
                'conversion_stats': conversion_result['stats'],
                'coordinate_analysis': analysis,  # 添加坐标系分析结果
                'martin_service': publish_result
            }
            
        except Exception as e:
            print(f"❌ TIF转MBTiles并发布失败: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # 清理可能生成的文件
            if 'mbtiles_path' in locals() and os.path.exists(mbtiles_path):
                try:
                    os.remove(mbtiles_path)
                except:
                    pass
            
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            # 清理临时目录
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                    print(f"🧹 临时目录已清理: {temp_dir}")
                except Exception as e:
                    print(f"⚠️ 清理临时目录失败: {e}")
    
    def _check_gdal_tools(self):
        """检查GDAL工具是否可用"""
        # 如果有Python GDAL绑定，优先使用
        if GDAL_AVAILABLE:
            print("✅ 使用GDAL Python绑定")
            return True
        
        # 否则尝试命令行工具
        try:
            # 检查gdalinfo（最基础的工具）
            result = subprocess.run(['gdalinfo', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                return False
            
            # 检查gdal_translate
            result = subprocess.run(['gdal_translate', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                return False
            
            # 检查gdalwarp
            result = subprocess.run(['gdalwarp', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                return False
            
            print("✅ 使用GDAL命令行工具")
            return True
            
        except Exception as e:
            print(f"❌ GDAL工具检查失败: {str(e)}")
            return False
    
    def _validate_tif_file(self, tif_path):
        """验证TIF文件并获取基本信息"""
        try:
            if GDAL_AVAILABLE:
                # 使用Python GDAL
                dataset = gdal.Open(tif_path, gdal.GA_ReadOnly)
                if dataset is None:
                    return {
                        'valid': False,
                        'error': 'GDAL无法打开TIF文件'
                    }
                
                # 获取基本信息
                width = dataset.RasterXSize
                height = dataset.RasterYSize
                band_count = dataset.RasterCount
                geotransform = dataset.GetGeoTransform()
                
                # 获取坐标系信息
                projection = dataset.GetProjection()
                srs = osr.SpatialReference()
                if projection:
                    srs.ImportFromWkt(projection)
                
                # 获取数据类型
                data_type = None
                if band_count > 0:
                    band = dataset.GetRasterBand(1)
                    data_type = gdal.GetDataTypeName(band.DataType)
                
                coordinate_system = {
                    'wkt': projection,
                    'epsg': srs.GetAuthorityCode(None) if srs.GetAuthorityCode(None) else None
                }
                
                dataset = None  # 关闭数据集
                
                return {
                    'valid': True,
                    'info': {
                        'width': width,
                        'height': height,
                        'band_count': band_count,
                        'data_type': data_type,
                        'coordinate_system': coordinate_system,
                        'geotransform': geotransform,
                        'has_georeference': bool(geotransform and any(geotransform))
                    }
                }
            else:
                # 使用命令行工具
                cmd = ['gdalinfo', '-json', tif_path]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode != 0:
                    return {
                        'valid': False,
                        'error': f'gdalinfo执行失败: {result.stderr}'
                    }
                
                info = json.loads(result.stdout)
                
                # 提取关键信息
                size = info.get('size', [])
                bands = info.get('bands', [])
                coordinate_system = info.get('coordinateSystem', {})
                geotransform = info.get('geoTransform', [])
                
                return {
                    'valid': True,
                    'info': {
                        'width': size[0] if len(size) > 0 else 0,
                        'height': size[1] if len(size) > 1 else 0,
                        'band_count': len(bands),
                        'data_type': bands[0].get('type') if bands else None,
                        'coordinate_system': coordinate_system,
                        'geotransform': geotransform,
                        'has_georeference': bool(geotransform and any(geotransform))
                    }
                }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'TIF文件验证失败: {str(e)}'
            }
    
    def _preprocess_tif(self, input_path, temp_dir, tif_info):
        """预处理TIF文件（数据类型转换等，保持原始坐标系）"""
        try:
            info = tif_info['info']
            processed_path = os.path.join(temp_dir, 'processed.tif')
            
            # 检查是否有地理参考信息
            has_georeference = info.get('has_georeference', False)
            coord_system = info.get('coordinate_system', {})
            
            print(f"📊 文件坐标系信息: {coord_system}")
            print(f"📊 是否有地理参考: {has_georeference}")
            
            # 不强制转换坐标系，保持原始投影
            # 只在没有地理参考信息时进行基本的数据类型转换
            needs_processing = not has_georeference
            
            if GDAL_AVAILABLE:
                # 使用Python GDAL进行处理
                if needs_processing:
                    print("🔄 进行数据优化处理（保持原始坐标系）")
                    # 使用gdal.Translate进行格式优化，不改变坐标系
                    translate_options = gdal.TranslateOptions(
                        creationOptions=['TILED=YES', 'COMPRESS=LZW']
                    )
                    gdal.Translate(processed_path, input_path, options=translate_options)
                else:
                    print("📋 使用原始文件（已具备地理参考）")
                    # 直接使用原始文件，不进行任何转换
                    return input_path
                
                # 检查输出文件是否存在
                if os.path.exists(processed_path):
                    print("✅ TIF文件预处理完成")
                    return processed_path
                else:
                    print("⚠️ 预处理失败，使用原始文件")
                    return input_path
                    
            else:
                # 使用命令行工具
                if needs_processing:
                    print("🔄 进行数据优化处理（保持原始坐标系）")
                    cmd = [
                        'gdal_translate',
                        '-co', 'TILED=YES',
                        '-co', 'COMPRESS=LZW',
                        input_path,
                        processed_path
                    ]
                else:
                    print("📋 使用原始文件（已具备地理参考）")
                    # 直接使用原始文件，不进行任何转换
                    return input_path
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                
                if result.returncode != 0:
                    print(f"⚠️ 预处理失败，使用原始文件: {result.stderr}")
                    return input_path
                
                print(f"✅ TIF文件预处理完成")
                return processed_path
            
        except Exception as e:
            print(f"⚠️ TIF预处理失败，使用原始文件: {str(e)}")
            return input_path
    
    def _convert_tif_to_mbtiles(self, tif_path, mbtiles_path, max_zoom, temp_dir, profile='raster'):
        """使用GDAL将TIF转换为MBTiles（智能坐标系处理）"""
        try:
            print(f"🔄 开始转换TIF为MBTiles，最大级别: {max_zoom}，Profile: {profile}")
            
            # 定义进度回调函数
            def progress_callback(complete, message=""):
                """
                GDAL风格的进度回调函数
                complete: 0.0 到 1.0 的完成度
                message: 可选的消息
                """
                progress_percent = int(complete * 100)
                if progress_percent % 10 == 0 or progress_percent == 100:
                    dots = "." * (progress_percent // 10)
                    print(f"进度: {progress_percent:3d}% [{dots:10s}] {message}")
                return True  # 返回True继续处理，False中断
            
            if GDAL_AVAILABLE:
                # 方法1：如果有Python GDAL，尝试使用gdal2tiles（如果系统中有脚本）
                print("💡 尝试使用Python gdal2tiles...")
                if self._try_gdal2tiles_python(tif_path, mbtiles_path, max_zoom, temp_dir, progress_callback, profile):
                    return self._get_conversion_stats(mbtiles_path)
            
                # 方法2：使用Python GDAL生成瓦片
                print("💡 使用Python GDAL生成瓦片...")
                if self._generate_tiles_with_python_gdal(tif_path, mbtiles_path, max_zoom, temp_dir, progress_callback):
                    return self._get_conversion_stats(mbtiles_path)
            else:
                # 方法3：尝试使用命令行gdal2tiles.py
                print("💡 尝试使用命令行gdal2tiles...")
                if self._try_gdal2tiles(tif_path, mbtiles_path, max_zoom, profile):
                    return self._get_conversion_stats(mbtiles_path)
            
            # 方法4：使用手动瓦片生成（最后的备选方案）
            print("💡 使用手动瓦片生成...")
            progress_callback(0.0, "开始手动瓦片生成")
            
            # 创建瓦片目录
            tiles_dir = os.path.join(temp_dir, 'tiles')
            os.makedirs(tiles_dir, exist_ok=True)
            
            # 生成瓦片
            if not self._generate_tiles_manual(tif_path, tiles_dir, max_zoom, progress_callback):
                return {
                    'success': False,
                    'error': '瓦片生成失败'
                }
            
            progress_callback(0.8, "瓦片生成完成，开始打包MBTiles")
            
            # 将瓦片打包为MBTiles
            if not self._pack_tiles_to_mbtiles(tiles_dir, mbtiles_path, max_zoom):
                return {
                    'success': False,
                    'error': 'MBTiles打包失败'
                }
            
            progress_callback(1.0, "转换完成")
            return self._get_conversion_stats(mbtiles_path)
            
        except Exception as e:
            return {
                'success': False,
                'error': f'转换过程失败: {str(e)}'
            }
    
    def _try_gdal2tiles_python(self, tif_path, mbtiles_path, max_zoom, temp_dir, progress_callback=None, profile='raster'):
        """尝试使用Python调用gdal2tiles进行转换（智能坐标系处理）"""
        try:
            # 如果有gdal2tiles模块，直接调用
            try:
                from osgeo_utils import gdal2tiles
                
                # 创建临时瓦片目录
                temp_tiles_dir = os.path.join(temp_dir, 'temp_tiles')
                os.makedirs(temp_tiles_dir, exist_ok=True)
                
                # 设置参数 - 使用分析得到的profile
                argv = [
                    f'--profile={profile}',  # 使用分析得到的profile
                    '--webviewer=none',
                    f'--zoom=0-{max_zoom}',
                    '--quiet',
                    tif_path,
                    temp_tiles_dir
                ]
                
                print(f"🔧 使用Python gdal2tiles: {' '.join(argv)}")
                
                # 调用gdal2tiles主函数
                gdal2tiles.main(argv)
                
                # 将瓦片目录转换为MBTiles
                success = self._pack_tiles_to_mbtiles(temp_tiles_dir, mbtiles_path, max_zoom)
                
                # 清理临时瓦片目录
                if os.path.exists(temp_tiles_dir):
                    shutil.rmtree(temp_tiles_dir)
                
                return success
                
            except ImportError:
                print("⚠️ gdal2tiles Python模块不可用")
                return False
                
        except Exception as e:
            print(f"⚠️ Python gdal2tiles方法失败: {str(e)}")
            return False

    def _generate_tiles_with_python_gdal(self, tif_path, mbtiles_path, max_zoom, temp_dir, progress_callback=None):
        """使用Python GDAL生成瓦片"""
        try:
            print("🔧 使用Python GDAL生成瓦片...")
            
            # 打开数据集
            dataset = gdal.Open(tif_path, gdal.GA_ReadOnly)
            if dataset is None:
                return False
            
            # 获取数据集信息
            width = dataset.RasterXSize
            height = dataset.RasterYSize
            geotransform = dataset.GetGeoTransform()
            
            print(f"📊 数据集信息: {width}x{height}")
            
            # 创建瓦片目录
            tiles_dir = os.path.join(temp_dir, 'tiles')
            os.makedirs(tiles_dir, exist_ok=True)
            
            # 智能瓦片生成策略
            # 对于大文件，只生成低级别瓦片以提高速度
            file_size_mb = os.path.getsize(tif_path) / (1024 * 1024)
            
            if file_size_mb > 100:  # 大于100MB的文件
                max_tiles_zoom = min(max_zoom, 10)
                max_tiles_per_zoom = 16
                print(f"📊 大文件 ({file_size_mb:.1f}MB)，限制瓦片生成至级别 {max_tiles_zoom}")
            elif file_size_mb > 50:  # 50-100MB的文件
                max_tiles_zoom = min(max_zoom, 12)
                max_tiles_per_zoom = 32
                print(f"📊 中等文件 ({file_size_mb:.1f}MB)，限制瓦片生成至级别 {max_tiles_zoom}")
            else:  # 小文件
                max_tiles_zoom = min(max_zoom, 14)
                max_tiles_per_zoom = 64
                print(f"📊 小文件 ({file_size_mb:.1f}MB)，限制瓦片生成至级别 {max_tiles_zoom}")
            
            tile_count = 0
            total_limit = 100  # 总瓦片数量限制
            
            # 计算总瓦片数以便进度报告
            total_tiles_estimate = min(total_limit, sum(
                min(2 ** zoom, int(max_tiles_per_zoom ** 0.5)) ** 2 
                for zoom in range(min(max_tiles_zoom + 1, 8))
            ))
            
            for zoom in range(min(max_tiles_zoom + 1, 8)):
                zoom_dir = os.path.join(tiles_dir, str(zoom))
                os.makedirs(zoom_dir, exist_ok=True)
                
                # 计算该级别的瓦片数量
                tiles_per_side = 2 ** zoom
                tiles_this_zoom = min(tiles_per_side, int(max_tiles_per_zoom ** 0.5))
                
                for x in range(tiles_this_zoom):
                    x_dir = os.path.join(zoom_dir, str(x))
                    os.makedirs(x_dir, exist_ok=True)
                    
                    for y in range(tiles_this_zoom):
                        if tile_count >= total_limit:
                            break
                            
                        tile_path = os.path.join(x_dir, f"{y}.png")
                        
                        # 生成单个瓦片
                        if self._generate_single_tile_python(dataset, tile_path, zoom, x, y):
                            tile_count += 1
                            
                            # 更新进度
                            if progress_callback and tile_count % 5 == 0:
                                progress = min(0.7 * tile_count / total_tiles_estimate, 0.7)
                                progress_callback(progress, f"生成瓦片 {tile_count}/{total_tiles_estimate}")
                            
                            if tile_count % 10 == 0:
                                print(f"🔧 已生成 {tile_count} 个瓦片...")
                    
                    if tile_count >= total_limit:
                        break
                        
                if tile_count >= total_limit:
                    break
            
            dataset = None  # 关闭数据集
            
            print(f"✅ 生成了 {tile_count} 个瓦片")
            
            # 将瓦片打包为MBTiles
            return self._pack_tiles_to_mbtiles(tiles_dir, mbtiles_path, max_zoom)
            
        except Exception as e:
            print(f"❌ Python GDAL瓦片生成失败: {str(e)}")
            return False

    def _generate_single_tile_python(self, dataset, tile_path, z, x, y):
        """使用Python GDAL生成单个瓦片（保持原始坐标系）"""
        try:
            # 简化的瓦片生成，使用原始坐标系
            tile_size = 256
            scale = 2 ** z
            
            # 计算源图像中的像素范围
            src_x = x * tile_size
            src_y = y * tile_size
            src_width = tile_size
            src_height = tile_size
            
            # 检查边界
            dataset_width = dataset.RasterXSize
            dataset_height = dataset.RasterYSize
            
            if src_x >= dataset_width or src_y >= dataset_height:
                return False
            
            # 调整边界以适应数据集
            actual_width = min(src_width, dataset_width - src_x)
            actual_height = min(src_height, dataset_height - src_y)
            
            # 使用gdal.Translate生成瓦片
            translate_options = gdal.TranslateOptions(
                srcWin=[src_x, src_y, actual_width, actual_height],
                width=256,
                height=256,
                resampleAlg=gdal.GRA_Bilinear,
                format='PNG'
            )
            
            gdal.Translate(tile_path, dataset, options=translate_options)
            
            return os.path.exists(tile_path)
            
        except Exception as e:
            print(f"⚠️ 生成瓦片 {z}/{x}/{y} 失败: {str(e)}")
            return False

    def _try_gdal2tiles(self, tif_path, mbtiles_path, max_zoom, profile='raster'):
        """尝试使用gdal2tiles.py进行转换（智能坐标系处理）"""
        try:
            # 创建临时瓦片目录
            temp_tiles_dir = os.path.join(os.path.dirname(mbtiles_path), 'temp_tiles')
            os.makedirs(temp_tiles_dir, exist_ok=True)
            
            # 使用分析得到的profile
            cmd = [
                'gdal2tiles.py',
                f'--profile={profile}',  # 使用分析得到的profile
                '--webviewer=none',
                f'--zoom=0-{max_zoom}',
                '--format=png',
                tif_path,
                temp_tiles_dir
            ]
            
            print(f"🔧 执行命令: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)  # 30分钟超时
            
            if result.returncode != 0:
                print(f"⚠️ gdal2tiles.py执行失败: {result.stderr}")
                return False
            
            # 将瓦片目录转换为MBTiles
            success = self._pack_tiles_to_mbtiles(temp_tiles_dir, mbtiles_path, max_zoom)
            
            # 清理临时瓦片目录
            if os.path.exists(temp_tiles_dir):
                shutil.rmtree(temp_tiles_dir)
            
            return success
            
        except Exception as e:
            print(f"⚠️ gdal2tiles.py方法失败: {str(e)}")
            return False
    
    def _generate_tiles_manual(self, tif_path, tiles_dir, max_zoom, progress_callback=None):
        """手动生成瓦片（简化版本）"""
        try:
            # 这是一个简化的实现，实际生产环境可能需要更复杂的逻辑
            print("🔧 使用简化方法生成瓦片...")
            
            # 为每个缩放级别生成瓦片
            for zoom in range(min(max_zoom + 1, 10)):  # 限制到10级避免过多瓦片
                zoom_dir = os.path.join(tiles_dir, str(zoom))
                os.makedirs(zoom_dir, exist_ok=True)
                
                # 计算该级别的瓦片数量（简化计算）
                tile_count = 2 ** zoom
                
                for x in range(tile_count):
                    x_dir = os.path.join(zoom_dir, str(x))
                    os.makedirs(x_dir, exist_ok=True)
                    
                    for y in range(tile_count):
                        tile_path = os.path.join(x_dir, f"{y}.png")
                        
                        # 使用gdal_translate生成单个瓦片
                        if not self._generate_single_tile(tif_path, tile_path, zoom, x, y):
                            continue
            
            return True
            
        except Exception as e:
            print(f"❌ 手动瓦片生成失败: {str(e)}")
            return False
    
    def _generate_single_tile(self, tif_path, tile_path, z, x, y):
        """生成单个瓦片（保持原始坐标系）"""
        try:
            # 简化的瓦片生成方法，使用原始坐标系
            # 使用gdal_translate提取瓦片区域
            
            # 计算瓦片在原始坐标系中的位置
            # 这里使用简化的方法，将图像分割成瓦片
            tile_size = 256
            scale = 2 ** z
            
            # 计算源图像中的像素范围
            src_x = x * tile_size
            src_y = y * tile_size
            src_width = tile_size
            src_height = tile_size
            
            # 使用gdal_translate提取瓦片
            cmd = [
                'gdal_translate',
                '-srcwin', str(src_x), str(src_y), str(src_width), str(src_height),
                '-outsize', '256', '256',
                '-r', 'bilinear',
                '-of', 'PNG',
                tif_path,
                tile_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.returncode == 0
            
        except Exception as e:
            print(f"⚠️ 生成瓦片 {z}/{x}/{y} 失败: {str(e)}")
            return False
    
    def _pack_tiles_to_mbtiles(self, tiles_dir, mbtiles_path, max_zoom):
        """将瓦片目录打包为MBTiles文件"""
        try:
            print("📦 打包瓦片为MBTiles格式...")
            
            # 使用Python的sqlite3创建MBTiles
            import sqlite3
            
            conn = sqlite3.connect(mbtiles_path)
            cursor = conn.cursor()
            
            # 创建MBTiles表结构
            cursor.execute('''
                CREATE TABLE metadata (name text, value text);
            ''')
            
            cursor.execute('''
                CREATE TABLE tiles (zoom_level integer, tile_column integer, 
                                  tile_row integer, tile_data blob);
            ''')
            
            # 插入元数据
            metadata = [
                ('name', 'Generated from TIF'),
                ('type', 'overlay'),
                ('version', '1.0'),
                ('description', f'Tiles generated from TIF file using {profile} profile'),
                ('format', 'png'),
                ('profile', profile),  # 记录使用的profile
                ('minzoom', '0'),
                ('maxzoom', str(max_zoom))
            ]
            
            cursor.executemany('INSERT INTO metadata VALUES (?, ?)', metadata)
            
            # 插入瓦片数据
            tile_count = 0
            for zoom_dir in os.listdir(tiles_dir):
                if not zoom_dir.isdigit():
                    continue
                
                zoom = int(zoom_dir)
                zoom_path = os.path.join(tiles_dir, zoom_dir)
                
                for x_dir in os.listdir(zoom_path):
                    if not x_dir.isdigit():
                        continue
                    
                    x = int(x_dir)
                    x_path = os.path.join(zoom_path, x_dir)
                    
                    for tile_file in os.listdir(x_path):
                        if not tile_file.endswith('.png'):
                            continue
                        
                        y = int(tile_file.replace('.png', ''))
                        tile_path = os.path.join(x_path, tile_file)
                        
                        # TMS y坐标转换
                        tms_y = (2 ** zoom - 1) - y
                        
                        with open(tile_path, 'rb') as f:
                            tile_data = f.read()
                        
                        cursor.execute(
                            'INSERT INTO tiles VALUES (?, ?, ?, ?)',
                            (zoom, x, tms_y, tile_data)
                        )
                        tile_count += 1
            
            # 创建索引
            cursor.execute('''
                CREATE UNIQUE INDEX tile_index on tiles 
                (zoom_level, tile_column, tile_row);
            ''')
            
            conn.commit()
            conn.close()
            
            print(f"✅ MBTiles打包完成，包含 {tile_count} 个瓦片")
            return True
            
        except Exception as e:
            print(f"❌ MBTiles打包失败: {str(e)}")
            return False
    
    def _validate_mbtiles_file(self, mbtiles_path):
        """验证生成的MBTiles文件"""
        try:
            import sqlite3
            
            conn = sqlite3.connect(mbtiles_path)
            cursor = conn.cursor()
            
            # 检查表结构
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            if 'metadata' not in tables or 'tiles' not in tables:
                return {
                    'valid': False,
                    'error': 'MBTiles文件缺少必要的表'
                }
            
            # 获取瓦片统计
            cursor.execute("SELECT COUNT(*) FROM tiles")
            tile_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT MIN(zoom_level), MAX(zoom_level) FROM tiles")
            zoom_range = cursor.fetchone()
            
            # 获取元数据
            cursor.execute("SELECT name, value FROM metadata")
            metadata = dict(cursor.fetchall())
            
            conn.close()
            
            return {
                'valid': True,
                'info': {
                    'tile_count': tile_count,
                    'min_zoom': zoom_range[0],
                    'max_zoom': zoom_range[1],
                    'metadata': metadata,
                    'file_size': os.path.getsize(mbtiles_path)
                }
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'MBTiles验证失败: {str(e)}'
            }
    
    def _get_conversion_stats(self, mbtiles_path):
        """获取转换统计信息"""
        try:
            mbtiles_info = self._validate_mbtiles_file(mbtiles_path)
            
            if not mbtiles_info['valid']:
                return {
                    'success': False,
                    'error': mbtiles_info['error']
                }
            
            return {
                'success': True,
                'stats': {
                    'output_file': mbtiles_path,
                    'file_size_mb': round(mbtiles_info['info']['file_size'] / 1024 / 1024, 2),
                    'tile_count': mbtiles_info['info']['tile_count'],
                    'zoom_levels': f"{mbtiles_info['info']['min_zoom']}-{mbtiles_info['info']['max_zoom']}"
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'统计信息获取失败: {str(e)}'
            }
    
    def _publish_mbtiles_to_martin(self, file_id, mbtiles_path, original_filename, 
                                 user_id, tif_info, mbtiles_info, conversion_stats, coordinate_analysis=None):
        """将MBTiles文件发布为Martin服务"""
        try:
            from services.raster_martin_service import RasterMartinService
            
            raster_service = RasterMartinService()
            
            # 使用原始文件名作为基础，但指定为栅格类型
            mbtiles_filename = os.path.basename(mbtiles_path)
            
            result = raster_service.publish_mbtiles_martin(
                file_id=file_id,
                file_path=mbtiles_path,
                original_filename=original_filename,  # 不添加_mbtiles后缀
                user_id=user_id,
                mbtiles_type='raster.mbtiles'  # 修正vector_type值
            )
            
            if result['success']:
                print(f"✅ MBTiles已发布为Martin服务")
                
                # 添加转换相关的额外信息
                result['tif_conversion'] = {
                    'original_tif': original_filename,
                    'tif_info': tif_info,
                    'mbtiles_info': mbtiles_info,
                    'conversion_stats': conversion_stats,
                    'coordinate_analysis': coordinate_analysis  # 添加坐标系分析信息
                }
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Martin服务发布失败: {str(e)}'
            } 