import TileCacheService from './TileCacheService.js';

/**
 * OpenLayers 瓦片缓存适配器
 * 将瓦片缓存功能集成到 OpenLayers 中
 */
class OpenLayersCacheAdapter {
  constructor(options = {}) {
    this.cacheService = options.cacheService || new TileCacheService();
    this.enableCache = options.enableCache !== false; // 默认启用缓存
    this.cacheBeforeNetwork = options.cacheBeforeNetwork !== false; // 默认优先使用缓存
    this.debug = options.debug || false;
    
    // 重试配置
    this.maxRetries = options.maxRetries || 3;
    this.retryDelay = options.retryDelay || 250;
    this.retryCodes = options.retryCodes || [500, 502, 503, 504, 408, 429];
    
    // 重试计数器
    this.retries = new Map();
    
    // 正在进行的请求管理
    this.pendingRequests = new Map();
  }

  /**
   * 创建简化的瓦片加载函数（更接近用户示例的风格）
   * @param {string} layerId 图层ID
   * @param {string} baseUrl 基础URL模板
   * @param {object} options 选项
   * @returns {Function} 瓦片加载函数
   */
  createSimpleTileLoadFunction(layerId, baseUrl, options = {}) {
    return (tile, src) => {
      // 对于栅格瓦片，使用类似用户示例的逻辑
      if (tile.getImage) {
        const image = tile.getImage();
        
        // 提取坐标
        const coords = this.extractTileCoordinates(src, baseUrl);
        if (!coords) {
          // 无法提取坐标，使用标准加载
          image.src = src;
          return;
        }
        
        const { z, x, y } = coords;
        
                 // 检查缓存
         this.cacheService.getTile(layerId, z, x, y).then((tileCache) => {
           if (tileCache != null) {
             // 如果已经存在，直接使用缓存的瓦片替换图片瓦片
             const imageUrl = URL.createObjectURL(tileCache.data);
             image.onload = () => {
               URL.revokeObjectURL(imageUrl);
               
             };
             image.onerror = () => {
               URL.revokeObjectURL(imageUrl);
               console.error(`❌ 缓存瓦片加载失败: ${layerId}_${z}_${x}_${y}`);
               // 如果缓存的图片无法加载，降级到网络请求
               image.src = src;
             };
             image.src = imageUrl;
             
             return;
          } else {
            // 缓存未命中，进行网络请求
            const tileKey = `${layerId}_${z}_${x}_${y}`;
            
            fetch(src, {
              method: 'GET',
              keepalive: true,
              cache: "force-cache",
              mode: 'cors'
            }).then((response) => {
              if (!response.ok) {
                // 检查重试
                if (this.retryCodes.includes(response.status)) {
                  const retries = this.retries.get(tileKey) || 0;
                  if (retries < this.maxRetries) {
                    this.retries.set(tileKey, retries + 1);
                    if (this.debug) {
                      console.log("请求瓦片失败，重新尝试次数：" + (retries + 1));
                    }
                    setTimeout(() => {
                      // 重新触发加载
                      tile.load();
                    }, this.retryDelay * (retries + 1));
                    return; // 不要reject，直接返回
                  } else {
                    // 重试次数用完，清理并降级
                    this.retries.delete(tileKey);
                  }
                }
                // 降级到标准加载
                console.warn(`瓦片加载失败 ${response.status}，降级到标准加载: ${src}`);
                image.src = src;
                return;
              }
              return response.blob();
            })
            .then((blob) => {
              if (blob) {
                // 清除重试计数（成功了）
                this.retries.delete(tileKey);
                
                const imageUrl = URL.createObjectURL(blob);
                image.onload = () => {
                  URL.revokeObjectURL(imageUrl);
                  if (this.debug) {
                    console.log(`✅ 网络瓦片加载成功: ${layerId}_${z}_${x}_${y}`);
                  }
                };
                image.onerror = () => {
                  URL.revokeObjectURL(imageUrl);
                  console.error(`❌ 网络瓦片图像加载失败: ${layerId}_${z}_${x}_${y}`);
                };
                image.src = imageUrl;
                
                // 缓存瓦片
                this.cacheService.saveTile(layerId, z, x, y, blob, {
                  contentType: blob.type || 'image/png',
                  url: src
                }).catch(err => {
                  console.warn('缓存瓦片失败:', err);
                });
              }
            })
            .catch((error) => {
              console.warn('网络请求异常，降级到标准加载:', error.message);
              // 降级到标准加载而不是设置错误状态
              image.src = src;
            });
          }
        }).catch((error) => {
          console.error('检查缓存失败:', error);
          // 降级到标准加载
          if (this.debug) {
            console.log('缓存检查失败，降级到标准网络加载:', src);
          }
          image.src = src;
        });
             } else {
         // 对于矢量瓦片，使用复杂的处理逻辑
         const coords = this.extractTileCoordinates(src, baseUrl);
         if (coords) {
           this.handleTileLoad(tile, src, layerId, coords.z, coords.x, coords.y, options)
             .catch(error => {
               console.error('矢量瓦片加载失败:', error);
               setTimeout(() => {
                 this.loadTileFromNetwork(tile, src);
               }, 0);
             });
         } else {
           // 无法提取坐标，使用标准加载
           this.loadTileFromNetwork(tile, src);
         }
       }
    };
  }

  /**
   * 创建带缓存功能的瓦片加载函数
   * @param {string} layerId 图层ID
   * @param {string} baseUrl 基础URL模板
   * @param {object} options 选项
   * @returns {Function} 瓦片加载函数
   */
    createTileLoadFunction(layerId, baseUrl, options = {}) {
    return (tile, src) => {
      // 使用Promise的方式处理异步操作，但不让函数本身是async
      // 这样可以避免OpenLayers对异步函数的处理问题
      
      if (!this.enableCache) {
        // 如果缓存未启用，直接加载
        this.loadTileFromNetwork(tile, src);
        return;
      }

      const coords = this.extractTileCoordinates(src, baseUrl);
      if (!coords) {
        this.loadTileFromNetwork(tile, src);
        return;
      }

      const { z, x, y } = coords;

      // 使用Promise包装异步操作，但不阻塞主线程
      // 重要：不要在这里await，让OpenLayers正常处理瓦片状态
      this.handleTileLoad(tile, src, layerId, z, x, y, options)
        .catch(error => {
          console.error('瓦片加载失败:', error);
          // 最终错误处理：降级到普通加载
          if (this.debug) {
            console.log(`⚡ 降级到普通加载: ${src}`);
          }
          
          // 使用setTimeout确保不阻塞当前执行流
          setTimeout(() => {
            try {
              this.loadTileFromNetwork(tile, src);
            } catch (fallbackError) {
              console.error('降级加载也失败:', fallbackError);
              // 最终失败，设置瓦片错误状态
              if (tile.getState && tile.getState() !== 3) {
                tile.setState(3); // ERROR state
              }
            }
          }, 0);
        });
    };
  }

  /**
   * 处理瓦片加载的核心逻辑
   * @param {object} tile OpenLayers瓦片对象
   * @param {string} src 瓦片URL
   * @param {string} layerId 图层ID
   * @param {number} z 缩放级别
   * @param {number} x X坐标
   * @param {number} y Y坐标
   * @param {object} options 选项
   */
  async handleTileLoad(tile, src, layerId, z, x, y, options = {}) {
    const tileKey = `${layerId}_${z}_${x}_${y}`;
    
    try {
      if (this.cacheBeforeNetwork) {
        // 1. 首先检查缓存
        if (this.debug) {
          console.log(`🔍 检查缓存: ${layerId}_${z}_${x}_${y}`);
        }
        const cachedTile = await this.cacheService.getTile(layerId, z, x, y);
        if (cachedTile) {
          // 2. 缓存命中：直接使用缓存
          await this.loadTileFromCache(tile, cachedTile);
          if (this.debug) {
            console.log(`✅ 命中瓦片缓存: ${layerId}_${z}_${x}_${y}`);
          }
          return;
        } else {
          if (this.debug) {
            console.log(`❌ 缓存未命中: ${layerId}_${z}_${x}_${y}`);
          }
        }
      }

      // 3. 检查是否已有相同的请求在进行
      if (this.pendingRequests.has(tileKey)) {
        if (this.debug) {
          console.log(`⏳ 等待已有请求: ${layerId}_${z}_${x}_${y}`);
        }
        try {
          // 等待已有请求完成，然后再次检查缓存
          await this.pendingRequests.get(tileKey);
          const cachedTile = await this.cacheService.getTile(layerId, z, x, y);
          if (cachedTile) {
            await this.loadTileFromCache(tile, cachedTile);
            if (this.debug) {
              console.log(`✅ 从等待后的缓存加载: ${layerId}_${z}_${x}_${y}`);
            }
            return;
          }
        } catch (waitError) {
          // 如果等待的请求失败了，我们继续尝试自己的请求
          if (this.debug) {
            console.log(`⚠️ 等待的请求失败，开始自己的请求: ${layerId}_${z}_${x}_${y}`);
          }
        }
      }

      // 4. 缓存未命中：网络请求并缓存
      if (this.debug) {
        console.log(`🌐 网络加载: ${src}`);
      }
      
      // 创建请求Promise并存储
      const requestPromise = this.loadTileFromNetworkWithCache(tile, src, layerId, z, x, y, options)
        .finally(() => {
          // 请求完成后，清理pending状态
          this.pendingRequests.delete(tileKey);
        });
      
      this.pendingRequests.set(tileKey, requestPromise);
      await requestPromise;
      
    } catch (error) {
      // 确保清理pending状态
      this.pendingRequests.delete(tileKey);
      // 重新抛出错误，让调用者处理
      throw error;
    }
  }

  /**
   * 从网络加载瓦片并缓存
   * @param {object} tile OpenLayers瓦片对象
   * @param {string} src 瓦片URL
   * @param {string} layerId 图层ID
   * @param {number} z 缩放级别
   * @param {number} x X坐标
   * @param {number} y Y坐标
   * @param {object} options 选项
   */
  async loadTileFromNetworkWithCache(tile, src, layerId, z, x, y, options = {}) {
    // 检查是否为矢量瓦片
    if (tile.getFeatures) {
      return this.loadVectorTileFromNetworkWithCache(tile, src, layerId, z, x, y, options);
    } else if (tile.getImage) {
      return this.loadRasterTileFromNetworkWithCache(tile, src, layerId, z, x, y, options);
    } else {
      throw new Error('未知的瓦片类型');
    }
  }

  /**
   * 从网络加载矢量瓦片并缓存
   * @param {object} tile 矢量瓦片对象
   * @param {string} src 瓦片URL
   * @param {string} layerId 图层ID
   * @param {number} z 缩放级别
   * @param {number} x X坐标
   * @param {number} y Y坐标
   * @param {object} options 选项
   */
  async loadVectorTileFromNetworkWithCache(tile, src, layerId, z, x, y, options = {}) {
    // options参数预留给将来可能的扩展（如认证、代理等）
    // eslint-disable-next-line no-unused-vars
    const _ = options;
    const tileKey = `${layerId}_${z}_${x}_${y}`;
    
    try {
      const response = await fetch(src, {
        method: 'GET',
        mode: 'cors',
        keepalive: true,
        cache: 'force-cache'
      });

      if (!response.ok) {
        if (response.status === 404) {
          // 404错误：该瓦片位置没有数据，这是正常的
          if (this.debug) {
            console.log(`矢量瓦片无数据(404): ${layerId}_${z}_${x}_${y}`);
          }
          
          // 创建空的瓦片数据
          tile.setFeatures([]);
          
          // 可选：缓存空瓦片以避免重复请求
          const emptyData = new Uint8Array(0);
          const emptyBlob = new Blob([emptyData], { type: 'application/x-protobuf' });
          await this.cacheService.saveTile(layerId, z, x, y, emptyBlob, {
            contentType: 'application/x-protobuf',
            url: src,
            isEmpty: true
          });
          
          return;
        } else if (this.retryCodes.includes(response.status)) {
          // 检查是否需要重试
          const retryCount = this.retries.get(tileKey) || 0;
          if (retryCount < this.maxRetries) {
            this.retries.set(tileKey, retryCount + 1);
            if (this.debug) {
              console.log(`矢量瓦片请求失败，重试次数: ${retryCount + 1}, URL: ${src}`);
            }
            
            // 延迟重试
            await new Promise(resolve => setTimeout(resolve, this.retryDelay * (retryCount + 1)));
            return this.loadVectorTileFromNetworkWithCache(tile, src, layerId, z, x, y, options);
          } else {
            // 重试次数已达上限
            this.retries.delete(tileKey);
            throw new Error(`矢量瓦片加载失败，已重试${this.maxRetries}次: HTTP ${response.status}`);
          }
        } else {
          throw new Error(`HTTP ${response.status}: ${src}`);
        }
      }

      // 请求成功，清除重试计数
      this.retries.delete(tileKey);

      const arrayBuffer = await response.arrayBuffer();
      const uint8Array = new Uint8Array(arrayBuffer);

      // 缓存原始二进制数据
      const blob = new Blob([uint8Array], { type: 'application/x-protobuf' });
      await this.cacheService.saveTile(layerId, z, x, y, blob, {
        contentType: 'application/x-protobuf',
        url: src
      });

      if (this.debug) {
        console.log(`矢量瓦片已缓存: ${layerId}_${z}_${x}_${y}`);
      }

      // 设置加载器来处理网络数据
      tile.setLoader((extent, resolution, projection) => {
        try {
          // 获取tile的格式化器（应该是MVT格式）
          const format = tile.getFormat();
          if (format && format.readFeatures) {
            const features = format.readFeatures(arrayBuffer, {
              extent: extent,
              featureProjection: projection
            });
            tile.setFeatures(features);
          } else {
            console.warn('矢量瓦片格式化器不可用');
            tile.setFeatures([]);
          }
        } catch (error) {
          console.error('解析矢量瓦片数据失败:', error);
          tile.setFeatures([]);
        }
      });
    } catch (error) {
      console.error('矢量瓦片加载失败:', error);
      tile.setState(3); // ERROR state
      throw error;
    }
  }

  /**
   * 从网络加载栅格瓦片并缓存
   * @param {object} tile 栅格瓦片对象
   * @param {string} src 瓦片URL
   * @param {string} layerId 图层ID
   * @param {number} z 缩放级别
   * @param {number} x X坐标
   * @param {number} y Y坐标
   * @param {object} options 选项
   */
  async loadRasterTileFromNetworkWithCache(tile, src, layerId, z, x, y, options = {}) {
    const tileKey = `${layerId}_${z}_${x}_${y}`;
    
    try {
      // 使用fetch进行网络请求以便处理HTTP状态码
      const response = await fetch(src, {
        method: 'GET',
        keepalive: true,
        cache: 'force-cache',
        mode: 'cors'
      });

      if (!response.ok) {
        // 检查是否需要重试
        if (this.retryCodes.includes(response.status)) {
          const retryCount = this.retries.get(tileKey) || 0;
          if (retryCount < this.maxRetries) {
            this.retries.set(tileKey, retryCount + 1);
            if (this.debug) {
              console.log(`瓦片请求失败，重试次数: ${retryCount + 1}, URL: ${src}`);
            }
            
            // 延迟重试
            await new Promise(resolve => setTimeout(resolve, this.retryDelay * (retryCount + 1)));
            return this.loadRasterTileFromNetworkWithCache(tile, src, layerId, z, x, y, options);
          } else {
            // 重试次数已达上限
            this.retries.delete(tileKey);
            throw new Error(`瓦片加载失败，已重试${this.maxRetries}次: HTTP ${response.status}`);
          }
        } else {
          throw new Error(`HTTP ${response.status}: ${src}`);
        }
      }

      // 请求成功，清除重试计数
      this.retries.delete(tileKey);
      
      const blob = await response.blob();
      
      // 缓存瓦片数据
      await this.cacheService.saveTile(layerId, z, x, y, blob, {
        contentType: blob.type || 'image/png',
        url: src
      });

      if (this.debug) {
        console.log(`栅格瓦片已缓存: ${layerId}_${z}_${x}_${y}`);
      }

      // 设置瓦片图像
      const imageUrl = URL.createObjectURL(blob);
      const imageElement = tile.getImage();
      if (imageElement instanceof Image) {
        imageElement.onload = () => {
          URL.revokeObjectURL(imageUrl); // 清理URL对象
        };
        imageElement.onerror = () => {
          URL.revokeObjectURL(imageUrl); // 清理URL对象
        };
        imageElement.src = imageUrl;
      }
      
    } catch (error) {
      console.error(`栅格瓦片加载失败: ${src}`, error);
      tile.setState(3); // ERROR state
      throw error;
    }
  }

  /**
   * 从缓存加载瓦片
   * @param {object} tile OpenLayers瓦片对象
   * @param {object} cachedTile 缓存的瓦片数据
   */
  async loadTileFromCache(tile, cachedTile) {
    try {
      // 检查是否为矢量瓦片
      if (tile.getFeatures) {
        // 矢量瓦片：使用setLoader方法
        const arrayBuffer = await cachedTile.data.arrayBuffer();
        
        // 检查是否是空数据
        if (arrayBuffer.byteLength === 0) {
          // 空数据，直接设置空特征数组
          tile.setFeatures([]);
        } else {
          // 设置加载器来处理缓存的数据
          tile.setLoader((extent, resolution, projection) => {
            try {
              // 获取tile的格式化器（应该是MVT格式）
              const format = tile.getFormat();
              if (format && format.readFeatures) {
                const features = format.readFeatures(arrayBuffer, {
                  extent: extent,
                  featureProjection: projection
                });
                tile.setFeatures(features);
              } else {
                console.warn('矢量瓦片格式化器不可用');
                tile.setFeatures([]);
              }
            } catch (error) {
              console.error('解析缓存的矢量瓦片数据失败:', error);
              tile.setFeatures([]);
            }
          });
        }
        
        if (this.debug) {
          console.log('从缓存加载矢量瓦片成功');
        }
      } else if (tile.getImage) {
        // 栅格瓦片：创建图像URL
        const url = URL.createObjectURL(cachedTile.data);
        const imageElement = tile.getImage();
        
        if (imageElement instanceof Image) {
          imageElement.onload = () => {
            URL.revokeObjectURL(url); // 清理URL对象
          };
          imageElement.onerror = () => {
            URL.revokeObjectURL(url); // 清理URL对象
            console.error('从缓存加载栅格瓦片失败');
          };
          imageElement.src = url;
        }
        
        if (this.debug) {
          console.log('从缓存加载栅格瓦片成功');
        }
      } else {
        console.warn('未知的瓦片类型，无法从缓存加载');
      }
    } catch (error) {
      console.error('从缓存加载瓦片失败:', error);
      // 设置瓦片为错误状态
      tile.setState(3);
    }
  }

  /**
   * 普通网络加载瓦片（无缓存）
   * @param {object} tile OpenLayers瓦片对象
   * @param {string} src 瓦片URL
   */
  loadTileFromNetwork(tile, src) {
    // 检查是否为矢量瓦片
    if (tile.getFeatures) {
      // 矢量瓦片处理
      this.loadVectorTileFromNetwork(tile, src);
    } else if (tile.getImage) {
      // 栅格瓦片处理 - 使用OpenLayers默认加载机制
      const imageElement = tile.getImage();
      if (imageElement instanceof Image) {
        imageElement.onload = () => {
          if (this.debug) {
            console.log('网络瓦片加载成功:', src);
          }
        };
        imageElement.onerror = () => {
          if (this.debug) {
            console.error('网络瓦片加载失败:', src);
          }
          tile.setState(3); // ERROR state
        };
        imageElement.src = src;
      }
    } else {
      console.warn('未知的瓦片类型，无法加载:', tile);
    }
  }

  /**
   * 从网络加载矢量瓦片
   * @param {object} tile 矢量瓦片对象
   * @param {string} src 瓦片URL
   */
  loadVectorTileFromNetwork(tile, src) {
    // 使用fetch加载矢量瓦片数据
    fetch(src)
      .then(response => {
        if (!response.ok) {
          if (response.status === 404) {
            // 404错误：该瓦片位置没有数据，设置空数据
            tile.setFeatures([]);
            return null; // 返回null表示没有数据需要处理
          } else {
            throw new Error(`HTTP ${response.status}: ${src}`);
          }
        }
        return response.arrayBuffer();
      })
              .then(arrayBuffer => {
          // 只有在有数据时才设置
          if (arrayBuffer !== null) {
            tile.setLoader((extent, resolution, projection) => {
              try {
                // 获取tile的格式化器（应该是MVT格式）
                const format = tile.getFormat();
                if (format && format.readFeatures) {
                  const features = format.readFeatures(arrayBuffer, {
                    extent: extent,
                    featureProjection: projection
                  });
                  tile.setFeatures(features);
                } else {
                  console.warn('矢量瓦片格式化器不可用');
                  tile.setFeatures([]);
                }
              } catch (error) {
                console.error('解析矢量瓦片数据失败:', error);
                tile.setFeatures([]);
              }
            });
          }
        })
      .catch(error => {
        if (!error.message.includes('404')) {
          console.error('矢量瓦片加载失败:', error);
          tile.setState(3); // ERROR state
        }
      });
  }

  /**
   * 从URL中提取瓦片坐标
   * @param {string} url 瓦片URL
   * @param {string} baseUrl 基础URL模板
   * @returns {object|null} 坐标对象 {z, x, y}
   */
  extractTileCoordinates(url) {
    try {
      // 常见的瓦片URL格式匹配
      const patterns = [
        /\/(\d+)\/(\d+)\/(\d+)\./,  // /{z}/{x}/{y}.ext
        /\/(\d+)\/(\d+)\/(\d+)$/,   // /{z}/{x}/{y}
        /z=(\d+).*x=(\d+).*y=(\d+)/, // z=1&x=2&y=3
        /zoom=(\d+).*col=(\d+).*row=(\d+)/ // zoom=1&col=2&row=3
      ];

      for (const pattern of patterns) {
        const match = url.match(pattern);
        if (match) {
          const [, z, x, y] = match;
          return {
            z: parseInt(z),
            x: parseInt(x),
            y: parseInt(y)
          };
        }
      }

      return null;
    } catch (error) {
      console.error('提取瓦片坐标失败:', error);
      return null;
    }
  }

  /**
   * 创建带缓存的XYZ图层源
   * @param {string} layerId 图层ID
   * @param {object} sourceOptions OpenLayers XYZ源选项
   * @returns {object} XYZ源对象
   */
  createCachedXYZSource(layerId, sourceOptions) {
    // 注意：这个方法应该在组件已经导入OpenLayers的上下文中使用
    // 我们不在这里导入，而是依赖调用者已经导入了OpenLayers
    
    // 尝试从window对象获取OpenLayers（适配器模式）
    if (typeof window !== 'undefined' && window.ol && window.ol.source && window.ol.source.XYZ) {
      const originalUrl = sourceOptions.url;
      
      return new window.ol.source.XYZ({
        ...sourceOptions,
        tileLoadFunction: this.createSimpleTileLoadFunction(layerId, originalUrl, {
          crossOrigin: sourceOptions.crossOrigin
        })
      });
    }
    
    // 最后的备用方案：返回null，让调用者使用标准XYZ源
    console.warn('OpenLayers 未在window对象上找到，返回null让调用者处理');
    return null;
  }

  /**
   * 预加载指定区域的瓦片
   * @param {string} layerId 图层ID
   * @param {string} baseUrl 基础URL模板
   * @param {object} extent 区域范围 {minX, minY, maxX, maxY}
   * @param {number} zoomLevel 缩放级别
   * @param {Function} progressCallback 进度回调
   */
  async preloadTiles(layerId, baseUrl, extent, zoomLevel, progressCallback) {
    try {
      const { minX, minY, maxX, maxY } = extent;
      const tileSize = 256; // 默认瓦片大小
      
      // 计算瓦片范围
      const tileRange = this.calculateTileRange(minX, minY, maxX, maxY, zoomLevel, tileSize);
      const totalTiles = (tileRange.maxX - tileRange.minX + 1) * (tileRange.maxY - tileRange.minY + 1);
      let loadedTiles = 0;

      const promises = [];

      for (let x = tileRange.minX; x <= tileRange.maxX; x++) {
        for (let y = tileRange.minY; y <= tileRange.maxY; y++) {
          // 检查是否已缓存
          const hasCached = await this.cacheService.hasTile(layerId, zoomLevel, x, y);
          if (!hasCached) {
            const tileUrl = this.buildTileUrl(baseUrl, zoomLevel, x, y);
            
            const promise = this.preloadSingleTile(layerId, tileUrl, zoomLevel, x, y)
              .then(() => {
                loadedTiles++;
                if (progressCallback) {
                  progressCallback(loadedTiles, totalTiles);
                }
              })
              .catch(error => {
                console.error(`预加载瓦片失败 ${zoomLevel}/${x}/${y}:`, error);
              });
            
            promises.push(promise);
          } else {
            loadedTiles++;
            if (progressCallback) {
              progressCallback(loadedTiles, totalTiles);
            }
          }
        }
      }

      await Promise.all(promises);
      console.log(`预加载完成: ${layerId} - 缩放级别 ${zoomLevel}`);
    } catch (error) {
      console.error('预加载瓦片时出错:', error);
    }
  }

  /**
   * 预加载单个瓦片
   * @param {string} layerId 图层ID
   * @param {string} url 瓦片URL
   * @param {number} z 缩放级别
   * @param {number} x X坐标
   * @param {number} y Y坐标
   */
  async preloadSingleTile(layerId, url, z, x, y) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.crossOrigin = 'anonymous';
      
      img.onload = async () => {
        try {
          const canvas = document.createElement('canvas');
          const ctx = canvas.getContext('2d');
          canvas.width = img.width;
          canvas.height = img.height;
          ctx.drawImage(img, 0, 0);
          
          canvas.toBlob(async (blob) => {
            if (blob) {
              await this.cacheService.saveTile(layerId, z, x, y, blob, {
                contentType: 'image/png',
                url
              });
            }
            resolve();
          }, 'image/png');
        } catch (error) {
          reject(error);
        }
      };
      
      img.onerror = () => reject(new Error(`加载失败: ${url}`));
      img.src = url;
    });
  }

  /**
   * 构建瓦片URL
   * @param {string} baseUrl 基础URL模板
   * @param {number} z 缩放级别
   * @param {number} x X坐标
   * @param {number} y Y坐标
   * @returns {string} 瓦片URL
   */
  buildTileUrl(baseUrl, z, x, y) {
    return baseUrl
      .replace('{z}', z.toString())
      .replace('{x}', x.toString())
      .replace('{y}', y.toString());
  }

  /**
   * 计算瓦片范围
   * @param {number} minX 最小X坐标
   * @param {number} minY 最小Y坐标
   * @param {number} maxX 最大X坐标
   * @param {number} maxY 最大Y坐标
   * @param {number} zoom 缩放级别
   * @param {number} tileSize 瓦片大小
   * @returns {object} 瓦片范围
   */
  calculateTileRange(minX, minY, maxX, maxY, zoom) {
    const scale = Math.pow(2, zoom);
    
    return {
      minX: Math.floor((minX + 180) / 360 * scale),
      minY: Math.floor((1 - Math.log(Math.tan(maxY * Math.PI / 180) + 1 / Math.cos(maxY * Math.PI / 180)) / Math.PI) / 2 * scale),
      maxX: Math.floor((maxX + 180) / 360 * scale),
      maxY: Math.floor((1 - Math.log(Math.tan(minY * Math.PI / 180) + 1 / Math.cos(minY * Math.PI / 180)) / Math.PI) / 2 * scale)
    };
  }

  /**
   * 获取缓存服务实例
   * @returns {TileCacheService} 缓存服务实例
   */
  getCacheService() {
    return this.cacheService;
  }

  /**
   * 启用/禁用缓存
   * @param {boolean} enabled 是否启用
   */
  setEnableCache(enabled) {
    this.enableCache = enabled;
  }

  /**
   * 设置是否优先使用缓存
   * @param {boolean} cacheFirst 是否优先使用缓存
   */
  setCacheFirst(cacheFirst) {
    this.cacheBeforeNetwork = cacheFirst;
  }

  /**
   * 清理重试计数器
   */
  clearRetryCounters() {
    this.retries.clear();
  }

  /**
   * 清理所有状态
   */
  clearAllStates() {
    this.retries.clear();
    this.pendingRequests.clear();
  }

  /**
   * 获取重试统计信息
   * @returns {object} 重试统计
   */
  getRetryStats() {
    return {
      activeRetries: this.retries.size,
      pendingRequests: this.pendingRequests.size,
      retryEntries: Array.from(this.retries.entries()).map(([key, count]) => ({
        tileKey: key,
        retryCount: count
      }))
    };
  }

  /**
   * 获取详细的调试信息
   * @returns {object} 调试信息
   */
  getDebugInfo() {
    return {
      cacheEnabled: this.enableCache,
      cacheFirst: this.cacheBeforeNetwork,
      debugEnabled: this.debug,
      maxRetries: this.maxRetries,
      retryDelay: this.retryDelay,
      retryCodes: this.retryCodes,
      stats: this.getRetryStats()
    };
  }
}

export default OpenLayersCacheAdapter; 