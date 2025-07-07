/**
 * 瓦片加载函数库
 * 提供统一的瓦片加载函数，支持缓存和网络加载
 */

import { getGlobalCacheService } from './indexedDBOperations.js';
import { MVT } from 'ol/format';

/**
 * 创建WMTS瓦片加载函数
 * @param {Object} options - 配置选项
 * @param {string} options.layerId - 图层ID
 * @param {Object} options.tileCacheService - 瓦片缓存服务实例
 * @param {Array} options.retryCodes - 需要重试的HTTP状态码
 * @param {Object} options.retries - 重试计数器
 * @param {boolean} options.enableCacheStorage - 是否启用缓存存储，默认为true
 * @returns {Function} 瓦片加载函数
 */
export function createWmtsTileLoadFunction(options = {}) {
  const {
    layerId = 'default_layer',
    tileCacheService = getGlobalCacheService(),
    retryCodes = [404, 503, 500],
    retries = {},
    enableCacheStorage = true // 默认开启缓存存储
  } = options;

  return function wmtsTileLoadFunction(imageTile, src) {
    const image = imageTile.getImage();
    
    
    // 从URL中提取瓦片坐标信息用于缓存
    const urlPattern1 = /x=(\d+).*y=(\d+).*z=(\d+)/;
    const urlPattern2 = /\/([0-9]+)\/([0-9]+)\/([0-9]+)(\.[a-z]+)?$/;

    // 从URL中提取瓦片坐标
    const match1 = src.match(urlPattern1);
    const match2 = src.match(urlPattern2);
    let x, y, z;
    
    
    if (match1) {
      x = parseInt(match1[1]);
      y = parseInt(match1[2]);
      z = parseInt(match1[3]);
    }
    if (match2 && src.includes('arcgis')) {
      z = parseInt(match2[1]);
      y = parseInt(match2[2]);
      x = parseInt(match2[3]);
    }else if(match2){
      z = parseInt(match2[1]);
      x = parseInt(match2[2]);
      y = parseInt(match2[3]);
    }

     if(!x || !y || !z) {
      // 如果无法解析坐标，直接加载
      fetch(src).then(response => response.blob())
        .then(blob => {
          const imageUrl = URL.createObjectURL(blob);
          image.src = imageUrl;
        })
        .catch(() => imageTile.setState(3));
      return;
    }

    // 检查缓存中是否已经存在该瓦片
    if (tileCacheService) {
      tileCacheService.getTile(layerId, z, x, y).then((tileCache) => {
        if (tileCache != null && tileCache.data) {
          // 如果已经存在，直接使用缓存的瓦片替换图片瓦片
          let imageUrl;
          if (tileCache.data instanceof Blob) {
            imageUrl = URL.createObjectURL(tileCache.data);
          } else if (typeof tileCache.data === 'string') {
            // 如果是base64字符串
            imageUrl = 'data:image/png;base64,' + tileCache.data;
          } else {
            // 如果是ArrayBuffer
            const blob = new Blob([tileCache.data], { type: 'image/png' });
            imageUrl = URL.createObjectURL(blob);
          }
          image.src = imageUrl;
          //console.log(`命中底图瓦片缓存: ${z}/${x}/${y}`);
          return;
        } else {
          // 缓存中没有，尝试从网络加载
          tryLoadFromNetwork();
        }
      }).catch(error => {
        console.error('检查瓦片缓存失败:', error);
        // 缓存检查失败，尝试从网络加载
        tryLoadFromNetwork();
      });
    } else {
      // 缓存服务未初始化，直接从网络加载
      tryLoadFromNetwork();
    }

    // 网络加载函数
    function tryLoadFromNetwork() {
      fetch(src, {
        method: 'GET',
        keepalive: true,
        cache: "force-cache"
      }).then((response) => {
        if (retryCodes.includes(response.status)) {
          retries[src] = (retries[src] || 0) + 1;
          if (retries[src] < 3) {
            //console.log("请求瓦片失败，重新尝试次数：" + retries[src]);
            setTimeout(() => imageTile.load(), retries[src] * 250);
          } else {
            console.warn(`底图瓦片 ${z}/${x}/${y} 网络加载失败，已达到最大重试次数`);
            imageTile.setState(3); // error
          }
          return Promise.reject();
        }
        return response.blob();
      })
      .then((blob) => {
        const imageUrl = URL.createObjectURL(blob);
        image.src = imageUrl;
        
        // 缓存瓦片到IndexedDB（如果开启缓存存储）
        if (tileCacheService && enableCacheStorage) {
          tileCacheService.saveTile(layerId, z, x, y, blob, {
            contentType: 'image/png',
            url: src
          }).then(() => {
            console.log(`底图瓦片已缓存: ${z}/${x}/${y}`);
          }).catch(error => {
            console.error('缓存底图瓦片失败:', error);
          });
        }
      })
      .catch((error) => {
        console.warn(`底图瓦片 ${z}/${x}/${y} 网络加载失败:`, error.message);
        // 网络加载失败，尝试查找附近的缓存瓦片作为替代
        tryLoadNearbyCache();
      });
    }

    // 尝试加载附近的缓存瓦片作为替代
    function tryLoadNearbyCache() {
      if (!tileCacheService) {
        imageTile.setState(3); // error
        return;
      }

      // 搜索附近的缓存瓦片（同一层级的相邻瓦片）
      const searchOffsets = [
        [0, 0], [1, 0], [-1, 0], [0, 1], [0, -1],
        [1, 1], [-1, -1], [1, -1], [-1, 1]
      ];

      let foundCache = false;
      
      const searchPromises = searchOffsets.map(([dx, dy]) => {
        return tileCacheService.getTile(layerId, z, x + dx, y + dy);
      });

      Promise.all(searchPromises).then(results => {
        for (let i = 0; i < results.length; i++) {
          const tileCache = results[i];
          if (tileCache && tileCache.data && !foundCache) {
            foundCache = true;
            let imageUrl;
            if (tileCache.data instanceof Blob) {
              imageUrl = URL.createObjectURL(tileCache.data);
            } else if (typeof tileCache.data === 'string') {
              imageUrl = 'data:image/png;base64,' + tileCache.data;
            } else {
              const blob = new Blob([tileCache.data], { type: 'image/png' });
              imageUrl = URL.createObjectURL(blob);
            }
            image.src = imageUrl;
            //console.log(`使用附近缓存瓦片替代 ${z}/${x}/${y}，来源: ${z}/${x + searchOffsets[i][0]}/${y + searchOffsets[i][1]}`);
            return;
          }
        }
        
        if (!foundCache) {
          console.warn(`底图瓦片 ${z}/${x}/${y} 无法加载，且无可用的缓存替代`);
          imageTile.setState(3); // error
        }
      }).catch(error => {
        console.error('搜索附近缓存瓦片失败:', error);
        imageTile.setState(3); // error
      });
    }
  };
}

/**
 * 创建MVT瓦片加载函数
 * @param {Object} options - 配置选项
 * @param {string} options.layerId - 图层ID
 * @param {Object} options.tileCacheService - 瓦片缓存服务实例
 * @param {boolean} options.enableCacheStorage - 是否启用缓存存储，默认为true
 * @returns {Function} 瓦片加载函数
 */
export function createMvtTileLoadFunction(options = {}) {
  const {
    layerId = 'mvt_layer',
    tileCacheService = getGlobalCacheService(),
    enableCacheStorage = true // 默认开启缓存存储
  } = options;

  return function mvtTileLoadFunction(tile, url) {
    // 对于 VectorTile，我们需要设置 loader 而不是直接操作 image
    tile.setLoader(function(extent, resolution, projection) {
      // 从URL中提取瓦片坐标
      const match = url.match(/\/(\d+)\/(\d+)\/(\d+)$/);
      if (!match) {
        console.warn('无法解析瓦片坐标:', url);
        tile.setFeatures([]);
        return;
      }
      
      const [z, x, y] = [parseInt(match[1]), parseInt(match[2]), parseInt(match[3])];
      //console.log(`MVT瓦片请求: ${z}/${x}/${y} - ${url}`);
      
      // 直接使用传入的layerId，确保与缓存key一致
      const currentLayerId = layerId;
      
      // 检查缓存中是否已经存在该MVT瓦片
      if (tileCacheService) {
        tileCacheService.getTile(currentLayerId, z, x, y).then((tileCache) => {
          if (tileCache != null && tileCache.data) {
            // 如果已经存在，直接使用缓存的MVT数据
            loadFromCache(tileCache);
            return;
          } else {
            // 缓存中没有，尝试从网络加载
            tryLoadMVTFromNetwork();
          }
        }).catch(error => {
          console.error('检查MVT瓦片缓存失败:', error);
          // 缓存检查失败，尝试从网络加载
          tryLoadMVTFromNetwork();
        });
      } else {
        // 没有缓存服务，直接从网络加载
        tryLoadMVTFromNetwork();
      }

      // 从缓存加载MVT数据
      function loadFromCache(tileCache) {
        try {
          let arrayBuffer;
          if (tileCache.data instanceof ArrayBuffer) {
            arrayBuffer = tileCache.data;
          } else if (tileCache.data instanceof Blob) {
            // 如果是Blob，转换为ArrayBuffer
            tileCache.data.arrayBuffer().then(buffer => {
              const mvtFormat = new MVT();
              const features = mvtFormat.readFeatures(buffer, {
                extent: extent,
                featureProjection: projection
              });
              tile.setFeatures(features);
              //console.log(`命中MVT瓦片缓存: ${z}/${x}/${y}，包含 ${features.length} 个要素`);
            }).catch(error => {
              console.error('从缓存Blob解析MVT失败:', error);
              if (tileCacheService && tileCache && tileCache.layerId !== undefined && tileCache.zoomLevel !== undefined && tileCache.tileX !== undefined && tileCache.tileY !== undefined) {
                tileCacheService.deleteTile(tileCache.layerId, tileCache.zoomLevel, tileCache.tileX, tileCache.tileY)
                  .then(() => {
                    console.warn(`已自动删除损坏的MVT缓存: ${tileCache.layerId} ${tileCache.zoomLevel}/${tileCache.tileX}/${tileCache.tileY}`);
                  });
              }
              tile.setFeatures([]);
            });
            return;
          } else if (typeof tileCache.data === 'string') {
            // 如果是base64字符串，转换为ArrayBuffer
            const binaryString = atob(tileCache.data);
            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {
              bytes[i] = binaryString.charCodeAt(i);
            }
            arrayBuffer = bytes.buffer;
          } else {
            console.warn('未知的缓存数据类型:', typeof tileCache.data);
            arrayBuffer = tileCache.data;
          }
          
          // 解析缓存的MVT数据
          const mvtFormat = new MVT();
          const features = mvtFormat.readFeatures(arrayBuffer, {
            extent: extent,
            featureProjection: projection
          });
          
          tile.setFeatures(features);
          //console.log(`命中MVT瓦片缓存: ${z}/${x}/${y}，包含 ${features.length} 个要素`);
        } catch (error) {
          console.error('解析缓存MVT数据失败:', error);
          // 缓存数据有问题，尝试从网络加载
          tryLoadMVTFromNetwork();
        }
      }

      // 尝试从网络加载MVT数据
      function tryLoadMVTFromNetwork() {
        let reurl=url.replace('localhost:3000',process.env.VUE_APP_MARTIN_HOST+':'+process.env.VUE_APP_MARTIN_PORT)
        fetch(reurl)
          .then(response => {
            if (!response.ok) {
              throw new Error(`HTTP ${response.status}`);
            }
            return response.arrayBuffer();
          })
          .then(arrayBuffer => {
            // 解析MVT数据
            const mvtFormat = new MVT();
            const features = mvtFormat.readFeatures(arrayBuffer, {
              extent: extent,
              featureProjection: projection
            });
            
            //console.log(`MVT瓦片 ${z}/${x}/${y} 加载成功，包含 ${features.length} 个要素`);
            tile.setFeatures(features);
            
            // 缓存MVT瓦片到IndexedDB（如果开启缓存存储）
            if (tileCacheService && enableCacheStorage) {
              tileCacheService.saveTile(currentLayerId, z, x, y, arrayBuffer, {
                contentType: 'application/vnd.mapbox-vector-tile',
                url: url
              }).then(() => {
                console.log(`MVT瓦片已缓存: ${z}/${x}/${y}`);
              }).catch(error => {
                console.error('缓存MVT瓦片失败:', error);
              });
            }
          })
          .catch(error => {
            console.warn(`MVT瓦片 ${z}/${x}/${y} 网络加载失败:`, error.message);
            // 网络加载失败，尝试查找附近的缓存MVT瓦片作为替代
            tryLoadNearbyMVTCache();
          });
      }

      // 尝试加载附近的缓存MVT瓦片作为替代
      function tryLoadNearbyMVTCache() {
        if (!tileCacheService) {
          console.warn(`MVT瓦片 ${z}/${x}/${y} 无法加载，无缓存服务`);
          tile.setFeatures([]);
          return;
        }

        // 搜索附近的缓存瓦片（同一层级的相邻瓦片）
        const searchOffsets = [
          [0, 0], [1, 0], [-1, 0], [0, 1], [0, -1],
          [1, 1], [-1, -1], [1, -1], [-1, 1]
        ];

        let foundCache = false;
        
        const searchPromises = searchOffsets.map(([dx, dy]) => {
          return tileCacheService.getTile(currentLayerId, z, x + dx, y + dy);
        });

        Promise.all(searchPromises).then(results => {
          for (let i = 0; i < results.length; i++) {
            const tileCache = results[i];
            if (tileCache && tileCache.data && !foundCache) {
              foundCache = true;
              //console.log(`使用附近缓存MVT瓦片替代 ${z}/${x}/${y}，来源: ${z}/${x + searchOffsets[i][0]}/${y + searchOffsets[i][1]}`);
              loadFromCache(tileCache);
              return;
            }
          }
          
          if (!foundCache) {
            console.warn(`MVT瓦片 ${z}/${x}/${y} 无法加载，且无可用的缓存替代`);
            tile.setFeatures([]);
          }
        }).catch(error => {
          console.error('搜索附近缓存MVT瓦片失败:', error);
          tile.setFeatures([]);
        });
      }
    });
  };
}

/**
 * 获取默认的WMTS瓦片加载函数
 * @param {string} layerId - 图层ID
 * @param {boolean} enableCacheStorage - 是否启用缓存存储
 * @returns {Function} 瓦片加载函数
 */
export function getDefaultWmtsTileLoadFunction(layerId = 'default_layer', enableCacheStorage = true) {
  return createWmtsTileLoadFunction({ layerId, enableCacheStorage });
}

/**
 * 获取默认的MVT瓦片加载函数
 * @param {string} layerId - 图层ID
 * @param {boolean} enableCacheStorage - 是否启用缓存存储
 * @returns {Function} 瓦片加载函数
 */
export function getDefaultMvtTileLoadFunction(layerId = 'mvt_layer', enableCacheStorage = true) {
  return createMvtTileLoadFunction({ layerId, enableCacheStorage });
}

// 导出默认实例
export default {
  createWmtsTileLoadFunction,
  createMvtTileLoadFunction,
  getDefaultWmtsTileLoadFunction,
  getDefaultMvtTileLoadFunction
};
