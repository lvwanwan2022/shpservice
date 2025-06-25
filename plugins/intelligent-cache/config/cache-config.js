/**
 * 智能缓存插件配置
 */

export default {
  // 缓存基础配置
  cache: {
    // 最大缓存大小 (字节)
    maxSize: 500 * 1024 * 1024, // 500MB
    
    // 最大瓦片数量
    maxTileCount: 10000,
    
    // 数据库名称
    dbName: 'GIS_Smart_Cache',
    
    // 数据库版本
    dbVersion: 1,
    
    // 清理策略
    cleanup: {
      // 触发清理的阈值（缓存使用率）
      threshold: 0.8,
      
      // 每次清理的比例
      ratio: 0.3,
      
      // 清理间隔（毫秒）
      interval: 5 * 60 * 1000 // 5分钟
    }
  },

  // 行为追踪配置
  behavior: {
    // 是否启用行为追踪
    enabled: true,
    
    // 行为记录保留时间（毫秒）
    retentionTime: 7 * 24 * 60 * 60 * 1000, // 7天
    
    // 批量上传大小
    batchSize: 50,
    
    // 上传间隔（毫秒）
    uploadInterval: 30 * 1000, // 30秒
    
    // 追踪的行为类型
    trackingEvents: [
      'tile_request',
      'map_move',
      'map_zoom',
      'layer_toggle',
      'feature_click'
    ]
  },

  // AI预测配置
  prediction: {
    // 是否启用AI预测
    enabled: true,
    
    // 预测模型路径
    modelPath: '/plugins/intelligent-cache/models/behavior_predictor.json',
    
    // 预测阈值（概率）
    threshold: 0.6,
    
    // 最大预加载数量
    maxPreloads: 5,
    
    // 预测历史长度
    historyLength: 20,
    
    // 特征提取配置
    features: {
      spatial: true,      // 空间特征
      temporal: true,     // 时间特征
      behavioral: true,   // 行为特征
      contextual: true    // 上下文特征
    },
    
    // 规则引擎配置
    rules: {
      // 邻近瓦片权重
      neighborWeight: 0.4,
      
      // 缩放趋势权重
      zoomWeight: 0.3,
      
      // 移动模式权重
      movementWeight: 0.3
    }
  },

  // 空间索引配置
  spatial: {
    // 索引类型 (rtree, quadtree, grid)
    indexType: 'rtree',
    
    // 最大节点数
    maxEntries: 16,
    
    // 最小节点数
    minEntries: 4,
    
    // 空间分区大小
    gridSize: 100
  },

  // 瓦片服务配置
  tileService: {
    // 基础URL
    baseUrl: '/api/tiles',
    
    // 支持的图层类型
    supportedLayers: ['mvt', 'wms', 'wmts'],
    
    // 请求超时时间（毫秒）
    timeout: 10000,
    
    // 重试次数
    retryCount: 3,
    
    // 重试间隔（毫秒）
    retryDelay: 1000
  },

  // 性能监控配置
  performance: {
    // 是否启用性能监控
    enabled: true,
    
    // 监控指标
    metrics: [
      'cache_hit_rate',
      'average_response_time',
      'prediction_accuracy',
      'preload_efficiency',
      'memory_usage'
    ],
    
    // 统计间隔（毫秒）
    interval: 60 * 1000, // 1分钟
    
    // 数据保留时间（毫秒）
    retentionTime: 24 * 60 * 60 * 1000 // 24小时
  },

  // 重要性评分权重配置
  importance: {
    weights: {
      zoomLevel: 0.15,      // 缩放级别重要性
      spatialHotness: 0.25, // 空间热度
      layerPriority: 0.15,  // 图层优先级
      temporalPattern: 0.15, // 时间模式
      userPreference: 0.15,  // 用户偏好
      predictionScore: 0.15  // 预测得分
    },
    
    // 图层优先级配置
    layerPriorities: {
      base: 0.9,        // 底图
      roads: 0.8,       // 道路
      buildings: 0.7,   // 建筑
      water: 0.6,       // 水系
      vegetation: 0.5,  // 植被
      labels: 0.4,      // 标注
      overlay: 0.3      // 叠加层
    },
    
    // 缩放级别重要性曲线
    zoomCurve: {
      optimal: 12,      // 最优缩放级别
      falloff: 0.1      // 衰减率
    }
  },

  // 网络配置
  network: {
    // 网络状态检测
    statusCheck: {
      enabled: true,
      interval: 30 * 1000, // 30秒
      testUrl: '/api/ping'
    },
    
    // 自适应策略
    adaptive: {
      // 低网速阈值（KB/s）
      slowThreshold: 100,
      
      // 高网速阈值（KB/s）
      fastThreshold: 1000,
      
      // 网速对应的预加载策略
      strategies: {
        slow: {
          maxPreloads: 2,
          threshold: 0.8
        },
        medium: {
          maxPreloads: 5,
          threshold: 0.6
        },
        fast: {
          maxPreloads: 10,
          threshold: 0.4
        }
      }
    }
  },

  // 调试配置
  debug: {
    // 是否启用调试模式
    enabled: false,
    
    // 日志级别 (error, warn, info, debug)
    logLevel: 'info',
    
    // 是否显示性能统计
    showStats: true,
    
    // 是否显示预测结果
    showPredictions: false,
    
    // 是否保存调试数据
    saveDebugData: false
  }
} 