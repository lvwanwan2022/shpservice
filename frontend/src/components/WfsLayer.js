import L from 'leaflet';
import axios from 'axios';

/**
 * WFS图层类
 */
export default class WfsLayer {
  /**
   * 创建WFS图层
   * @param {Object} options - 配置选项
   */
  constructor(options = {}) {
    this.options = Object.assign({
      url: '',
      typeName: '', // 图层名称，格式为"workspace:layername"
      style: {
        color: '#3388ff',
        weight: 3,
        opacity: 0.8,
        fillColor: '#3388ff',
        fillOpacity: 0.3
      },
      onEachFeature: null,
      maxFeatures: 5000, // 最大要素数量
      outputFormat: 'application/json',
      srsName: 'EPSG:4326',
      version: '2.0.0',
      service: 'WFS',
      request: 'GetFeature'
    }, options);
    
    this.layer = null;
    this.loading = false;
    this.loaded = false;
    this.error = null;
    this.data = null;
  }
  
  /**
   * 加载WFS图层
   * @returns {Promise} 加载完成的Promise
   */
  load() {
    if (this.loading) {
      return Promise.reject(new Error('图层正在加载中'));
    }
    
    if (this.loaded && this.layer) {
      return Promise.resolve(this.layer);
    }
    
    this.loading = true;
    this.error = null;
    
    // 构建WFS请求参数
    const params = {
      service: this.options.service,
      version: this.options.version,
      request: this.options.request,
      typeName: this.options.typeName,
      outputFormat: this.options.outputFormat,
      srsName: this.options.srsName,
      maxFeatures: this.options.maxFeatures
    };
    
    //console.log('请求WFS数据:', this.options.url, params);
    
    // 发起请求
    return axios.get(this.options.url, { 
      params,
      // 添加更多请求配置
      timeout: 30000,
      withCredentials: false, // 不发送凭证
      headers: {
        'Accept': 'application/json'
      },
      // 使用代理模式避免跨域
      proxy: false
    })
      .then(response => {
        //console.log('WFS数据请求成功:', response.status);
        this.data = response.data;
        
        // 创建GeoJSON图层
        this.layer = L.geoJSON(this.data, {
          style: this.options.style,
          onEachFeature: this.options.onEachFeature || this._defaultOnEachFeature.bind(this)
        });
        
        this.loaded = true;
        this.loading = false;
        return this.layer;
      })
      .catch(error => {
        console.error('WFS数据请求详细错误:', error);
        // 提供更详细的错误信息
        this.error = {
          message: error.message,
          url: this.options.url,
          params: params,
          status: error.response ? error.response.status : '无响应',
          details: error.response ? error.response.data : '无详细信息'
        };
        this.loading = false;
        
        // 尝试使用JSONP方式请求WFS
        return this._loadWithJsonp();
      });
  }
  
  /**
   * 使用JSONP方式加载WFS数据（备用方法）
   * @returns {Promise} 加载完成的Promise
   * @private
   */
  _loadWithJsonp() {
    return new Promise((resolve) => {
      //console.log('尝试使用JSONP方式加载WFS数据');
      
      // 使用WMS-JSON方式作为备选方案（如果GeoServer支持）
      const wmsUrl = this.options.url.replace('wfs', 'wms');
      const layer = L.tileLayer.wms(wmsUrl, {
        layers: this.options.typeName,
        format: 'image/png',
        transparent: true
      });
      
      this.layer = layer;
      this.loaded = true;
      
      resolve(layer);
    });
  }
  
  /**
   * 默认的要素处理函数
   * @param {Object} feature - GeoJSON要素
   * @param {L.Layer} layer - Leaflet图层
   * @private
   */
  _defaultOnEachFeature(feature, layer) {
    if (feature.properties) {
      let popupContent = '<div style="max-height:200px;overflow:auto;"><table style="width:100%;border-collapse:collapse;">';
      for (const property in feature.properties) {
        if (feature.properties[property] !== null && feature.properties[property] !== undefined) {
          popupContent += `<tr>
            <td style="padding:4px;border:1px solid #ddd;font-weight:bold;">${property}</td>
            <td style="padding:4px;border:1px solid #ddd;">${feature.properties[property]}</td>
          </tr>`;
        }
      }
      popupContent += '</table></div>';
      layer.bindPopup(popupContent);
    }
  }
  
  /**
   * 添加到地图
   * @param {L.Map} map - Leaflet地图实例
   * @returns {Promise} 加载并添加完成的Promise
   */
  addTo(map) {
    return this.load()
      .then(layer => {
        layer.addTo(map);
        
        // 自动缩放到图层范围 - 禁用以避免动画问题
        // if (this.options.fitBounds !== false && layer.getBounds && layer.getBounds().isValid()) {
        //   map.fitBounds(layer.getBounds(), {
        //     padding: [20, 20]
        //   });
        // }
        
        return layer;
      });
  }
  
  /**
   * 从地图移除
   * @param {L.Map} map - Leaflet地图实例
   */
  removeFrom(map) {
    if (this.layer) {
      map.removeLayer(this.layer);
    }
  }
  
  /**
   * 获取图层实例
   * @returns {L.GeoJSON} GeoJSON图层
   */
  getLayer() {
    return this.layer;
  }
  
  /**
   * 获取图层状态
   * @returns {Object} 图层状态
   */
  getState() {
    return {
      loading: this.loading,
      loaded: this.loaded,
      error: this.error
    };
  }
  
  /**
   * 设置图层样式
   * @param {Object|Function} style - 图层样式
   */
  setStyle(style) {
    if (this.layer) {
      this.layer.setStyle(style);
    }
    this.options.style = style;
  }
  
  /**
   * 检查图层是否支持 fitBounds 操作
   * @returns {boolean} 是否支持
   */
  hasBounds() {
    return this.layer && this.layer.getBounds && typeof this.layer.getBounds === 'function';
  }
} 