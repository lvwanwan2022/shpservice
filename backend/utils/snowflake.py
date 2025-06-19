#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
雪花算法ID生成器
"""

import time
import threading

class SnowflakeGenerator:
    """
    雪花算法ID生成器
    
    生成64位的ID，结构如下：
    - 1位符号位，始终为0
    - 41位时间戳（毫秒级）
    - 5位数据中心ID
    - 5位工作机器ID
    - 12位序列号
    
    可以生成在分布式系统中唯一的ID
    """
    
    def __init__(self, datacenter_id=1, worker_id=1, sequence=0):
        """
        初始化雪花ID生成器
        
        Args:
            datacenter_id: 数据中心ID (0-31)
            worker_id: 工作机器ID (0-31)
            sequence: 起始序列号 (0-4095)
        """
        # 参数限制
        max_datacenter_id = -1 ^ (-1 << 5)  # 5位，最大值31
        max_worker_id = -1 ^ (-1 << 5)      # 5位，最大值31
        max_sequence = -1 ^ (-1 << 12)      # 12位，最大值4095
        
        # 参数校验
        if datacenter_id > max_datacenter_id or datacenter_id < 0:
            raise ValueError(f"数据中心ID必须在0-{max_datacenter_id}之间")
        if worker_id > max_worker_id or worker_id < 0:
            raise ValueError(f"工作机器ID必须在0-{max_worker_id}之间")
        if sequence > max_sequence or sequence < 0:
            raise ValueError(f"序列号必须在0-{max_sequence}之间")
            
        # 各部分偏移量
        self.worker_id_bits = 5
        self.datacenter_id_bits = 5
        self.sequence_bits = 12
        
        # 各部分最大值
        self.max_worker_id = -1 ^ (-1 << self.worker_id_bits)
        self.max_datacenter_id = -1 ^ (-1 << self.datacenter_id_bits)
        self.max_sequence = -1 ^ (-1 << self.sequence_bits)
        
        # 各部分左移位数
        self.worker_id_shift = self.sequence_bits
        self.datacenter_id_shift = self.sequence_bits + self.worker_id_bits
        self.timestamp_shift = self.sequence_bits + self.worker_id_bits + self.datacenter_id_bits
        
        # 实例变量
        self.datacenter_id = datacenter_id
        self.worker_id = worker_id
        self.sequence = sequence
        self.last_timestamp = -1
        
        # 起始时间戳（2023-01-01 00:00:00 UTC）
        self.twepoch = 1672531200000
        
        # 线程锁，保证并发安全
        self.lock = threading.Lock()
    
    def _next_millis(self, last_timestamp):
        """
        获取下一毫秒时间戳
        """
        timestamp = self._get_time()
        while timestamp <= last_timestamp:
            timestamp = self._get_time()
        return timestamp
    
    def _get_time(self):
        """
        获取当前时间戳（毫秒）
        """
        return int(time.time() * 1000)
    
    def get_id(self):
        """
        生成下一个ID
        
        Returns:
            生成的雪花算法ID
        """
        with self.lock:
            timestamp = self._get_time()
            
            # 时钟回拨问题处理
            if timestamp < self.last_timestamp:
                # 如果出现时钟回拨，等待直到时间追上来
                timestamp = self._next_millis(self.last_timestamp)
            
            # 同一毫秒内序列号递增
            if timestamp == self.last_timestamp:
                self.sequence = (self.sequence + 1) & self.max_sequence
                # 同一毫秒内序列号用完，等待下一毫秒
                if self.sequence == 0:
                    timestamp = self._next_millis(self.last_timestamp)
            else:
                # 不同毫秒，序列号重置
                self.sequence = 0
                
            # 记录最后一次时间戳
            self.last_timestamp = timestamp
            
            # 组合各部分生成ID
            return ((timestamp - self.twepoch) << self.timestamp_shift) | \
                   (self.datacenter_id << self.datacenter_id_shift) | \
                   (self.worker_id << self.worker_id_shift) | \
                   self.sequence

# 创建默认的雪花ID生成器实例
snowflake = SnowflakeGenerator()

def get_snowflake_id():
    """
    获取雪花算法生成的ID
    
    Returns:
        雪花算法ID
    """
    return snowflake.get_id() 