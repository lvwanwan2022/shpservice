#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TIF Martin Service - Simplified Version
将TIF文件使用gdal2tiles.py转换为瓦片，然后合并为MBTiles格式
"""

import os
import json
import uuid
import tempfile
import shutil
import subprocess
import sqlite3
import threading
import time
from pathlib import Path
from models.db import execute_query, insert_with_snowflake_id
from config import DB_CONFIG, MARTIN_CONFIG, FILE_STORAGE
import logging

logger = logging.getLogger(__name__)

class TifMartinService:
    """TIF Martin服务类，简化版本"""
    
    def __init__(self):
        """初始化服务"""
        self.upload_folder = FILE_STORAGE['upload_folder']
        self.mbtiles_folder = os.path.join(self.upload_folder, 'mbtiles')
        self.temp_folder = FILE_STORAGE.get('temp_folder', 'temp')
        
        # 确保目录存在
        os.makedirs(self.mbtiles_folder, exist_ok=True)
        os.makedirs(self.temp_folder, exist_ok=True)
        
        # 进度跟踪
        self.progress_data = {}
        
        print("✅ TIF Martin服务初始化完成")
    
    def get_file_coordinate_system(self, file_id):
        """从数据库获取文件的坐标系信息"""
        try:
            sql = "SELECT coordinate_system FROM files WHERE id = %s"
            result = execute_query(sql, (file_id,))
            if result and result[0]['coordinate_system']:
                return result[0]['coordinate_system']
            return 'EPSG:4326'  # 默认坐标系
        except Exception as e:
            print(f"⚠️ 获取坐标系信息失败: {str(e)}")
            return 'EPSG:4326'
    
    def tif_to_mbtiles_and_publish(self, file_id, file_path, original_filename, user_id=None, max_zoom=18, min_zoom=2):
        """将TIF文件转换为MBTiles并发布为Martin服务"""
        temp_dir = None
        task_id = str(uuid.uuid4())
        
        try:
            print(f"🔄 开始处理TIF文件: {original_filename}")
            
            # 初始化进度
            self.progress_data[task_id] = {
                'status': 'starting',
                'progress': 0,
                'message': '开始处理...',
                'current_step': 'init'
            }
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                self.progress_data[task_id]['status'] = 'error'
                self.progress_data[task_id]['message'] = f'TIF文件不存在: {file_path}'
                return {'success': False, 'error': f'TIF文件不存在: {file_path}', 'task_id': task_id}
            
            # 获取坐标系
            coordinate_system = self.get_file_coordinate_system(file_id)
            print(f"📊 使用坐标系: {coordinate_system}")
            
            # 生成输出路径
            file_uuid = uuid.uuid4().hex
            mbtiles_filename = f"{file_uuid}.mbtiles"
            mbtiles_path = os.path.join(self.mbtiles_folder, mbtiles_filename)
            
            # 创建临时工作目录
            temp_dir = tempfile.mkdtemp(prefix='tif_conversion_')
            tiles_dir = os.path.join(temp_dir, 'tiles')
            
            print(f"📁 临时目录: {temp_dir}")
            print(f"📁 瓦片目录: {tiles_dir}")
            
            # 更新进度
            self.progress_data[task_id].update({
                'status': 'processing',
                'progress': 10,
                'message': '开始生成瓦片...',
                'current_step': 'tiles_generation'
            })
            
            # 第一步：使用gdal2tiles.py生成瓦片
            if not self._generate_tiles_with_gdal2tiles(file_path, tiles_dir, min_zoom, max_zoom, coordinate_system, task_id):
                return {
                    'success': False,
                    'error': '瓦片生成失败',
                    'task_id': task_id
                }
            
            # 更新进度
            self.progress_data[task_id].update({
                'progress': 80,
                'message': '瓦片生成完成，开始打包MBTiles...',
                'current_step': 'mbtiles_packing'
            })
            
            # 第二步：将瓦片打包为MBTiles
            if not self._pack_tiles_to_mbtiles(tiles_dir, mbtiles_path, min_zoom, max_zoom, task_id):
                return {
                    'success': False,
                    'error': 'MBTiles打包失败',
                    'task_id': task_id
                }
            
            # 更新进度
            self.progress_data[task_id].update({
                'progress': 90,
                'message': '发布Martin服务...',
                'current_step': 'martin_publish'
            })
            
            # 第三步：发布为Martin服务
            publish_result = self._publish_mbtiles_to_martin(
                file_id=file_id,
                mbtiles_path=mbtiles_path,
                original_filename=original_filename,
                user_id=user_id,
                coordinate_system=coordinate_system
            )
            
            if not publish_result['success']:
                # 如果发布失败，删除生成的MBTiles文件
                if os.path.exists(mbtiles_path):
                    os.remove(mbtiles_path)
                return publish_result
            
            # 完成
            self.progress_data[task_id].update({
                'status': 'completed',
                'progress': 100,
                'message': '转换完成！',
                'current_step': 'completed'
            })
            
            print(f"🎉 TIF文件成功转换并发布为Martin服务")
            
            return {
                'success': True,
                'message': 'TIF文件成功转换为MBTiles并发布为Martin服务',
                'task_id': task_id,
                'mbtiles_path': mbtiles_path,
                'mbtiles_filename': mbtiles_filename,
                'coordinate_system': coordinate_system,
                'martin_service': publish_result
            }
            
        except Exception as e:
            print(f"❌ TIF转MBTiles并发布失败: {str(e)}")
            
            # 更新进度为错误状态
            if task_id in self.progress_data:
                self.progress_data[task_id].update({
                    'status': 'error',
                    'message': f'处理失败: {str(e)}',
                    'current_step': 'error'
                })
            
            # 清理可能生成的文件
            if 'mbtiles_path' in locals() and os.path.exists(mbtiles_path):
                try:
                    os.remove(mbtiles_path)
                except:
                    pass
            
            return {
                'success': False,
                'error': str(e),
                'task_id': task_id
            }
        finally:
            # 清理临时目录
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                    print(f"🧹 临时目录已清理: {temp_dir}")
                except Exception as e:
                    print(f"⚠️ 清理临时目录失败: {e}")
    
    def _generate_tiles_with_gdal2tiles(self, tif_path, tiles_dir, min_zoom, max_zoom, coordinate_system, task_id):
        """使用gdal2tiles.py生成瓦片"""
        try:
            print(f"🔧 使用gdal2tiles.py生成瓦片...")
            
            # 构建命令
            cmd = [
                'python', 'gdal2tiles.py',
                '--config', 'GDAL_CACHEMAX', '500',
                f'--zoom={min_zoom}-{max_zoom}',
                '-s', coordinate_system,
                '--webviewer=none',
                '--quiet',
                tif_path,
                tiles_dir
            ]
            
            # 检查是否支持MPI
            try:
                subprocess.run(['mpirun', '--version'], capture_output=True, timeout=5)
                cmd.insert(2, '--mpi')  # 在gdal2tiles.py后添加--mpi参数
                print("✅ 启用MPI并行处理")
            except:
                print("⚠️ MPI不可用，使用单线程处理")
            
            print(f"🔧 执行命令: {' '.join(cmd)}")
            
            # 启动进程
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                universal_newlines=True
            )
            
            # 启动进度监控线程
            progress_thread = threading.Thread(
                target=self._monitor_tiles_progress,
                args=(tiles_dir, task_id, min_zoom, max_zoom)
            )
            progress_thread.daemon = True
            progress_thread.start()
            
            # 等待进程完成
            stdout, stderr = process.communicate(timeout=3600)  # 1小时超时
            
            if process.returncode != 0:
                print(f"❌ gdal2tiles.py执行失败: {stderr}")
                self.progress_data[task_id].update({
                    'status': 'error',
                    'message': f'瓦片生成失败: {stderr}'
                })
                return False
            
            print(f"✅ 瓦片生成完成")
            return True
            
        except subprocess.TimeoutExpired:
            print("❌ gdal2tiles.py执行超时")
            process.kill()
            self.progress_data[task_id].update({
                'status': 'error',
                'message': '瓦片生成超时'
            })
            return False
        except Exception as e:
            print(f"❌ gdal2tiles.py执行异常: {str(e)}")
            self.progress_data[task_id].update({
                'status': 'error',
                'message': f'瓦片生成异常: {str(e)}'
            })
            return False
    
    def _monitor_tiles_progress(self, tiles_dir, task_id, min_zoom, max_zoom):
        """监控瓦片生成进度"""
        try:
            # 估算总瓦片数
            total_tiles_estimate = sum(4 ** zoom for zoom in range(min_zoom, min(max_zoom + 1, 10)))
            
            while True:
                if task_id not in self.progress_data:
                    break
                
                if self.progress_data[task_id]['status'] in ['completed', 'error']:
                    break
                
                # 统计已生成的瓦片数
                current_tiles = 0
                if os.path.exists(tiles_dir):
                    for root, dirs, files in os.walk(tiles_dir):
                        current_tiles += len([f for f in files if f.endswith('.png')])
                
                # 计算进度 (10% - 75%)
                if total_tiles_estimate > 0:
                    progress = 10 + int((current_tiles / total_tiles_estimate) * 65)
                    progress = min(progress, 75)
                else:
                    progress = 10
                
                # 更新进度
                self.progress_data[task_id].update({
                    'progress': progress,
                    'message': f'正在生成瓦片... ({current_tiles} 个瓦片)',
                    'tiles_count': current_tiles
                })
                
                time.sleep(2)  # 每2秒更新一次
                
        except Exception as e:
            print(f"⚠️ 进度监控异常: {str(e)}")
    
    def _pack_tiles_to_mbtiles(self, tiles_dir, mbtiles_path, min_zoom, max_zoom, task_id):
        """将瓦片目录打包为MBTiles文件"""
        try:
            print("📦 打包瓦片为MBTiles格式...")
            
            # 创建MBTiles数据库
            conn = sqlite3.connect(mbtiles_path)
            cursor = conn.cursor()
            
            # 创建表结构
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
                ('description', 'Tiles generated from TIF file'),
                ('format', 'png'),
                ('minzoom', str(min_zoom)),
                ('maxzoom', str(max_zoom))
            ]
            
            cursor.executemany('INSERT INTO metadata VALUES (?, ?)', metadata)
            
            # 插入瓦片数据
            tile_count = 0
            total_files = sum(len(files) for _, _, files in os.walk(tiles_dir) if files)
            
            for root, dirs, files in os.walk(tiles_dir):
                for file in files:
                    if not file.endswith('.png'):
                        continue
                    
                    # 解析路径获取z/x/y
                    rel_path = os.path.relpath(root, tiles_dir)
                    path_parts = rel_path.split(os.sep)
                    
                    if len(path_parts) >= 2:
                        try:
                            zoom = int(path_parts[0])
                            x = int(path_parts[1])
                            y = int(file.replace('.png', ''))
                            
                            # TMS y坐标转换
                            tms_y = (2 ** zoom - 1) - y
                            
                            # 读取瓦片数据
                            tile_path = os.path.join(root, file)
                            with open(tile_path, 'rb') as f:
                                tile_data = f.read()
                            
                            cursor.execute(
                                'INSERT INTO tiles VALUES (?, ?, ?, ?)',
                                (zoom, x, tms_y, tile_data)
                            )
                            tile_count += 1
                            
                            # 更新进度
                            if tile_count % 100 == 0:
                                progress = 80 + int((tile_count / total_files) * 10)
                                self.progress_data[task_id].update({
                                    'progress': min(progress, 89),
                                    'message': f'打包瓦片... ({tile_count}/{total_files})'
                                })
                            
                        except (ValueError, IndexError):
                            continue
            
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
            self.progress_data[task_id].update({
                'status': 'error',
                'message': f'MBTiles打包失败: {str(e)}'
            })
            return False
    
    def _publish_mbtiles_to_martin(self, file_id, mbtiles_path, original_filename, user_id, coordinate_system):
        """将MBTiles文件发布为Martin服务"""
        try:
            from services.raster_martin_service import RasterMartinService
            
            raster_service = RasterMartinService()
            
            result = raster_service.publish_mbtiles_martin(
                file_id=file_id,
                file_path=mbtiles_path,
                original_filename=original_filename,
                user_id=user_id,
                mbtiles_type='raster.mbtiles'
            )
            
            if result['success']:
                print(f"✅ MBTiles已发布为Martin服务")
                
                # 添加坐标系信息
                result['coordinate_system'] = coordinate_system
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Martin服务发布失败: {str(e)}'
            }
    
    def get_progress(self, task_id):
        """获取任务进度"""
        return self.progress_data.get(task_id, {
            'status': 'not_found',
            'progress': 0,
            'message': '任务不存在',
            'current_step': 'unknown'
        })
    
    def cleanup_progress(self, task_id):
        """清理进度数据"""
        if task_id in self.progress_data:
            del self.progress_data[task_id]