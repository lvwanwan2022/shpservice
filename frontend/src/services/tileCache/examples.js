/**
 * 瓦片缓存系统使用示例
 * 展示如何在不同场景下使用瓦片缓存功能
 */

import { 
  quickSetup, 
  createOpenLayersAdapter, 
  createLeafletAdapter,
  OpenLayersCacheAdapter,
  //LeafletCacheAdapter,
  CacheStrategyManager,
  calculateTileList,
  calculateTileCount,
  olExtentToBounds,
  getCacheUsage,
  CacheDebugger
} from './index.js';

/**
 * 示例1: 系统初始化和基本设置
 */
export async function example1_BasicSetup() {
  console.log('=== 示例1: 基本设置 ===');
  
  // 快速初始化缓存系统
  const setup = quickSetup({
    maxCacheSize: 500 * 1024 * 1024, // 500MB
    maxCacheAge: 7 * 24 * 60 * 60 * 1000, // 7天
    useGlobal: true,
    debug: true
  });

  if (setup.supported) {
    console.log('缓存系统初始化成功');
    console.log('可用适配器:', Object.keys(setup.adapters));
    
    // 查看缓存使用情况
    const usage = await getCacheUsage();
    console.log('当前缓存使用情况:', usage);
  } else {
    console.error('缓存系统初始化失败:', setup.error);
  }
}

/**
 * 示例2: 计算bounds对应的瓦片列表
 */
export function example2_CalculateTiles() {
  console.log('=== 示例2: 计算瓦片列表 ===');
  
  // 定义一个区域范围（北京市中心）
  const bounds = {
    north: 39.9593,
    south: 39.8993,
    east: 116.4374,
    west: 116.3574
  };

  // 计算单个缩放级别的瓦片列表
  const tilesAtZoom10 = calculateTileList(bounds, 10);
  console.log(`缩放级别10的瓦片数量: ${tilesAtZoom10.length}`);
  console.log('前5个瓦片坐标:', tilesAtZoom10.slice(0, 5));

  // 计算多个缩放级别的瓦片列表
  const tilesMultiZoom = calculateTileList(bounds, { min: 8, max: 12 });
  console.log(`缩放级别8-12的总瓦片数量: ${tilesMultiZoom.length}`);

  // 只计算瓦片数量（不生成列表）
  const tileCount = calculateTileCount(bounds, { min: 8, max: 12 });
  console.log(`快速计算的瓦片数量: ${tileCount}`);
}

/**
 * 示例3: OpenLayers集成
 */
export function example3_OpenLayersIntegration() {
  console.log('=== 示例3: OpenLayers集成 ===');
  
  if (typeof window === 'undefined' || !window.ol) {
    console.warn('OpenLayers未加载，跳过示例');
    return;
  }

  // 创建缓存适配器
  const cacheAdapter = createOpenLayersAdapter({
    enableCache: true,
    cacheBeforeNetwork: true,
    debug: true
  });

  // 创建带缓存的OSM图层
  const osmSource = cacheAdapter.createCachedXYZSource('osm-base', {
    url: 'https://{a-c}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    crossOrigin: 'anonymous'
  });

  // 创建地图（需要OpenLayers库）
  if (typeof window === 'undefined' || !window.ol) {
    console.warn('OpenLayers未加载，跳过地图创建');
    return { cacheAdapter };
  }
  
  const map = new window.ol.Map({
    target: 'map',
    layers: [
      new window.ol.layer.Tile({
        source: osmSource
      })
    ],
    view: new window.ol.View({
      center: window.ol.proj.fromLonLat([116.3974, 39.9093]),
      zoom: 10
    })
  });

  // 预加载当前视图区域
  const extent = map.getView().calculateExtent(map.getSize());
  const bounds = olExtentToBounds(extent, 'EPSG:3857');
  
  cacheAdapter.preloadTiles(
    'osm-base',
    'https://{a-c}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    bounds,
    10,
    (loaded, total) => {
      console.log(`预加载进度: ${loaded}/${total}`);
    }
  );

  return { map, cacheAdapter };
}

/**
 * 示例4: Leaflet集成
 */
export function example4_LeafletIntegration() {
  console.log('=== 示例4: Leaflet集成 ===');
  
  if (typeof window === 'undefined' || !window.L) {
    console.warn('Leaflet未加载，跳过示例');
    return;
  }

  // 创建缓存适配器
  const cacheAdapter = createLeafletAdapter({
    enableCache: true,
    cacheBeforeNetwork: true,
    debug: true
  });

  // 创建地图
  const map = window.L.map('map').setView([39.9093, 116.3974], 10);

  // 创建带缓存的OSM图层
  const osmLayer = cacheAdapter.createCachedTileLayer(
    'osm-base',
    'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    {
      attribution: '© OpenStreetMap contributors',
      crossOrigin: 'anonymous'
    }
  );

  osmLayer.addTo(map);

  // 添加缓存控制面板
  const cacheControl = cacheAdapter.createCacheControl();
  cacheControl.addTo(map);

  // 预加载当前视图区域
  const bounds = map.getBounds();
  
  cacheAdapter.preloadTiles(
    'osm-base',
    'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    bounds,
    8,
    12,
    (loaded, total, zoom) => {
      console.log(`预加载进度: ${loaded}/${total} (缩放级别: ${zoom})`);
    }
  );

  return { map, cacheAdapter };
}

/**
 * 示例5: 缓存策略管理器使用
 */
export async function example5_CacheStrategyManager() {
  console.log('=== 示例5: 缓存策略管理器 ===');
  
  // 创建策略管理器
  const strategyManager = new CacheStrategyManager({
    loginStrategy: {
      priority: 3,
      zoomLevels: { min: 8, max: 12 },
      progressCallback: (progress) => {
        console.log(`登录策略进度: ${progress.completed}/${progress.total}`);
      }
    },
    sceneSwitchStrategy: {
      priority: 2,
      zoomLevels: { min: 10, max: 14 },
      progressCallback: (progress) => {
        console.log(`场景切换进度: ${progress.completed}/${progress.total}`);
      }
    },
    zoomStrategy: {
      priority: 1,
      zoomBuffer: 2,
      boundsExpansion: 0.5
    }
  });

  // 模拟场景数据
  const mockScenes = [
    {
      id: 'beijing',
      name: '北京市',
      layers: [
        {
          id: 'beijing-base',
          name: '北京底图',
          url: 'https://tile.example.com/beijing/{z}/{x}/{y}.png',
          bounds: {
            north: 40.2,
            south: 39.4,
            east: 117.4,
            west: 115.4
          }
        },
        {
          id: 'beijing-poi',
          name: '北京POI',
          url: 'https://poi.example.com/beijing/{z}/{x}/{y}.png',
          bounds: {
            north: 40.1,
            south: 39.5,
            east: 117.2,
            west: 115.6
          }
        }
      ]
    },
    {
      id: 'shanghai',
      name: '上海市',
      layers: [
        {
          id: 'shanghai-base',
          name: '上海底图',
          url: 'https://tile.example.com/shanghai/{z}/{x}/{y}.png',
          bounds: {
            north: 31.8,
            south: 30.7,
            east: 122.0,
            west: 120.8
          }
        }
      ]
    }
  ];

  // 执行登录策略
  console.log('执行登录预加载策略...');
  await strategyManager.executeLoginStrategy(mockScenes);

  // 执行场景切换策略
  console.log('执行场景切换策略...');
  await strategyManager.executeSceneSwitchStrategy(mockScenes[0]);

  // 执行缩放策略
  const visibleLayers = mockScenes[0].layers;
  const currentBounds = {
    north: 39.95,
    south: 39.85,
    east: 116.45,
    west: 116.35
  };
  
  console.log('执行缩放策略...');
  await strategyManager.executeZoomStrategy(visibleLayers, currentBounds, 12);

  // 查看任务状态
  console.log('任务状态:', strategyManager.getTaskStatus());
}

/**
 * 示例6: 缓存管理和调试
 */
export async function example6_CacheManagement() {
  console.log('=== 示例6: 缓存管理和调试 ===');
  
  // 使用调试工具
  await CacheDebugger.printStats();
  
  // 检查特定瓦片
  const hasTile = await CacheDebugger.checkTile('osm-base', 10, 100, 200);
  console.log('瓦片存在:', hasTile);
  
  // 列出所有图层
  const layers = await CacheDebugger.listLayers();
  console.log('缓存的图层:', layers);
  
  // 获取详细的缓存使用情况
  const usage = await getCacheUsage();
  console.log('缓存使用详情:', usage);
  
  // 如果缓存过大，可以清理过期缓存
  if (usage.totalSize > 100 * 1024 * 1024) { // 超过100MB
    console.log('缓存过大，开始清理...');
    const { cleanExpiredTiles } = await import('./utils.js');
    const cleanedCount = await cleanExpiredTiles(3 * 24 * 60 * 60 * 1000); // 3天
    console.log(`已清理 ${cleanedCount} 个过期瓦片`);
  }
}

/**
 * 示例7: 自定义缓存策略
 */
export async function example7_CustomStrategy() {
  console.log('=== 示例7: 自定义缓存策略 ===');
  
  const strategyManager = new CacheStrategyManager();
  
  // 自定义高优先级预加载策略
  strategyManager.setStrategy('login', {
    priority: 5,
    zoomLevels: { min: 6, max: 15 },
    maxConcurrent: 10,
    progressCallback: (progress) => {
      console.log(`高优先级预加载: ${Math.round(progress.completed / progress.total * 100)}%`);
    }
  });
  
  // 自定义轻量级缩放策略
  strategyManager.setStrategy('zoom', {
    priority: 1,
    zoomBuffer: 1, // 只预加载当前级别前后1级
    boundsExpansion: 0.2, // 只扩展20%的边界
    progressCallback: (progress) => {
      console.log(`轻量级缩放预加载: ${progress.completed}/${progress.total}`);
    }
  });
  
  console.log('自定义策略配置完成');
  
  // 测试自定义策略
  const testScene = {
    id: 'test',
    layers: [{
      id: 'test-layer',
      url: 'https://test.example.com/{z}/{x}/{y}.png',
      bounds: { north: 40, south: 39, east: 117, west: 116 }
    }]
  };
  
  await strategyManager.executeSceneSwitchStrategy(testScene);
}

/**
 * 示例8：完整的数据缓存服务使用
 */
export const example8_DataCacheService = {
  name: '完整的数据缓存服务',
  description: '展示如何使用DataCacheService调用后端API获取数据并缓存',
  
  async run() {
    console.log('\n=== 示例8：完整的数据缓存服务 ===');
    
    try {
      // 1. 导入所需模块
      const { DataCacheService } = await import('./utils.js');
      const { createTileCache } = await import('./index.js');
      
      // 模拟GIS API (在实际使用中会导入真实的API)
      const mockGisApi = {
        async getScenes() {
          console.log('🔍 调用API: getScenes()');
          return {
            data: [
              { id: 1, name: '城市规划场景', description: '包含建筑、道路等图层' },
              { id: 2, name: '环境监测场景', description: '包含污染源、监测点等图层' }
            ]
          };
        },
        
        async getScene(sceneId) {
          console.log(`🔍 调用API: getScene(${sceneId})`);
          const scenes = {
            1: {
              id: 1,
              name: '城市规划场景',
              layers: [
                { layer_id: 101, layer_name: '建筑物图层', file_type: 'SHP' },
                { layer_id: 102, layer_name: '道路网络', file_type: 'DXF' }
              ]
            },
            2: {
              id: 2,
              name: '环境监测场景',
              layers: [
                { layer_id: 201, layer_name: '污染源分布', file_type: 'GEOJSON' },
                { layer_id: 202, layer_name: '监测点位', file_type: 'SHP' }
              ]
            }
          };
          return { data: scenes[sceneId] || null };
        },
        
        async getSceneLayerBounds(layerId) {
          console.log(`🔍 调用API: getSceneLayerBounds(${layerId})`);
          // 模拟不同图层的bounds
          const bounds = {
            101: { bbox: [116.3, 39.9, 116.5, 40.1] }, // 北京建筑物
            102: { bbox: [116.2, 39.8, 116.6, 40.2] }, // 北京道路
            201: { bbox: [120.1, 30.2, 120.3, 30.4] }, // 上海污染源
            202: { bbox: [120.0, 30.1, 120.4, 30.5] }  // 上海监测点
          };
          
          // 模拟网络延迟
          await new Promise(resolve => setTimeout(resolve, 200));
          
          return { data: bounds[layerId] || null };
        }
      };
      
      // 2. 创建缓存服务
      console.log('📦 创建瓦片缓存服务...');
      const tileCacheService = createTileCache({
        maxCacheSize: 100 * 1024 * 1024, // 100MB
        maxCacheAge: 24 * 60 * 60 * 1000 // 1天
      });
      
      // 3. 创建数据缓存服务
      console.log('📊 创建数据缓存服务...');
      const dataCacheService = new DataCacheService(tileCacheService, mockGisApi);
      
      // 4. 设置进度回调
      dataCacheService.setProgressCallback((progress) => {
        console.log(`📈 进度更新: ${progress.percent}% - ${progress.message} (${progress.current}/${progress.total})`);
      });
      
      // 5. 执行登录缓存策略
      console.log('\n🚀 执行登录缓存策略...');
      await dataCacheService.executeLoginStrategy();
      
      // 6. 执行场景切换缓存策略
      console.log('\n🔄 执行场景切换缓存策略...');
      await dataCacheService.executeSceneSwitchStrategy(1);
      
      console.log('\n✅ 数据缓存服务示例完成！');
      
    } catch (error) {
      console.error('❌ 数据缓存服务示例失败:', error);
    }
  }
};

/**
 * 示例：类似于用户提供的WMTS瓦片加载函数
 * 展示如何使用OpenLayersCacheAdapter实现缓存优先的瓦片加载策略
 */

// 示例9：类似于用户示例的瓦片加载函数
function createCacheFirstTileLoadFunction() {
  console.log('=== 示例9：类似用户示例的瓦片加载函数 ===');
  
  // 创建缓存适配器
  const adapter = new OpenLayersCacheAdapter({
    debug: true,
    enableCache: true,
    cacheBeforeNetwork: true,
    maxRetries: 3,           // 最大重试次数
    retryDelay: 250,         // 重试延迟(ms)
    retryCodes: [500, 502, 503, 504, 408, 429] // 需要重试的HTTP状态码
  });

  const layerId = 'example_layer';
  const baseUrl = 'https://example.com/tiles/{z}/{x}/{y}.png';
  
  // 创建瓦片加载函数 - 与用户示例逻辑相似
  const wmtsTileLoadFunction = adapter.createTileLoadFunction(layerId, baseUrl, {
    crossOrigin: 'anonymous'
  });

  /* 
   * 上面创建的wmtsTileLoadFunction的逻辑等价于：
   * 
   * const wmtsTileLoadFunction = function(imageTile, src) {
   *   const image = imageTile.getImage();
   *   
   *   // 1. 检查缓存中是否已经存在该瓦片
   *   loadFromCache(src).then((tileCache) => {
   *     if (tileCache != null) {
   *       // 2. 如果已经存在，直接使用缓存的瓦片替换图片瓦片
   *       const imageUrl = URL.createObjectURL(tileCache);
   *       image.src = imageUrl;
   *       console.log("命中瓦片缓存");
   *       return;
   *     } else {
   *       // 3. 缓存未命中，进行网络请求
   *       fetch(src, {
   *         method: 'GET',
   *         keepalive: true,
   *         cache: "force-cache"
   *       }).then((response) => {
   *         // 4. 处理重试逻辑
   *         if (retryCodes.includes(response.status)) {
   *           retries[src] = (retries[src] || 0) + 1;
   *           if (retries[src] < 3) {
   *             console.log("请求瓦片失败，重新尝试次数：" + retries[src]);
   *             setTimeout(() => imageTile.load(), retries[src] * 250);
   *           }
   *           return Promise.reject();
   *         }
   *         return response.blob();
   *       })
   *       .then((blob) => {
   *         // 5. 网络成功：设置图像并缓存
   *         const imageUrl = URL.createObjectURL(blob);
   *         image.src = imageUrl;
   *         cacheTile(src, blob);
   *       })
   *       .catch(() => imageTile.setState(3)); // error
   *     }
   *   });
   * };
   */

  console.log('瓦片加载函数已创建，包含以下特性：');
  console.log('- 缓存优先策略：先检查IndexedDB缓存');
  console.log('- 网络降级：缓存未命中时从网络加载');
  console.log('- 自动重试：网络失败时最多重试3次');
  console.log('- 自动缓存：网络成功后保存到IndexedDB');
  console.log('- 错误处理：最终失败时设置瓦片错误状态');

  return wmtsTileLoadFunction;
}

/**
 * 运行所有示例
 */
export async function runAllExamples() {
  console.log('开始运行所有瓦片缓存示例...');
  
  try {
    await example1_BasicSetup();
    example2_CalculateTiles();
    // example3_OpenLayersIntegration(); // 需要DOM元素
    // example4_LeafletIntegration(); // 需要DOM元素
    await example5_CacheStrategyManager();
    await example6_CacheManagement();
    await example7_CustomStrategy();
    await example8_DataCacheService.run();
    
    console.log('所有示例运行完成！');
  } catch (error) {
    console.error('示例运行失败:', error);
  }
}

// 默认导出
export default {
  example1_BasicSetup,
  example2_CalculateTiles,
  example3_OpenLayersIntegration,
  example4_LeafletIntegration,
  example5_CacheStrategyManager,
  example6_CacheManagement,
  example7_CustomStrategy,
  example8_DataCacheService,
  createCacheFirstTileLoadFunction,
  runAllExamples
}; 