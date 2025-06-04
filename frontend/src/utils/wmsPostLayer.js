import L from 'leaflet'
import axios from 'axios'

/**
 * 支持POST请求的WMS图层类
 * 用于解决SLD_BODY等参数过长导致的414 URI Too Long错误
 */
export class WMSPostLayer extends L.Layer {
  constructor(url, options = {}) {
    super(options)
    this.url = url
    this.options = {
      tileSize: 256,
      format: 'image/png',
      transparent: true,
      version: '1.1.1',
      crs: L.CRS.EPSG4326,
      attribution: '',
      opacity: 1,
      zIndex: 1,
      ...options
    }
    
    this._tiles = new Map()
    this._loading = new Set()
    this._container = null
  }

  onAdd(map) {
    this._map = map
    this._container = L.DomUtil.create('div', 'leaflet-layer')
    this._container.style.position = 'absolute'
    this._container.style.pointerEvents = 'none'
    
    map.getPanes().overlayPane.appendChild(this._container)
    
    this._reset()
    this._update()
    
    map.on('viewreset', this._reset, this)
    map.on('zoom', this._onZoom, this)
    map.on('moveend', this._update, this)
    map.on('zoomend', this._update, this)
    
    return this
  }

  onRemove(map) {
    map.off('viewreset', this._reset, this)
    map.off('zoom', this._onZoom, this)
    map.off('moveend', this._update, this)
    map.off('zoomend', this._update, this)
    
    if (this._container && this._container.parentNode) {
      this._container.parentNode.removeChild(this._container)
    }
    
    this._tiles.clear()
    this._loading.clear()
  }

  _reset() {
    this._tiles.clear()
    this._loading.clear()
    if (this._container) {
      this._container.innerHTML = ''
    }
  }

  _onZoom() {
    this._reset()
  }

  _update() {
    if (!this._map) return
    
    const bounds = this._map.getBounds()
    const zoom = this._map.getZoom()
    const tileSize = this.options.tileSize
    const pixelBounds = this._map.getPixelBounds()
    const tileRange = this._getTileRange(pixelBounds, tileSize)
    
    // 清理不在视图范围内的瓦片
    this._removeOutOfBoundsTiles(tileRange)
    
    // 加载视图范围内的瓦片
    for (let j = tileRange.min.y; j <= tileRange.max.y; j++) {
      for (let i = tileRange.min.x; i <= tileRange.max.x; i++) {
        const coords = new L.Point(i, j)
        coords.z = zoom
        
        const key = this._tileCoordsToKey(coords)
        if (!this._tiles.has(key) && !this._loading.has(key)) {
          this._loadTile(coords)
        }
      }
    }
  }

  _getTileRange(pixelBounds, tileSize) {
    return {
      min: pixelBounds.min.divideBy(tileSize).floor(),
      max: pixelBounds.max.divideBy(tileSize).ceil().subtract([1, 1])
    }
  }

  _tileCoordsToKey(coords) {
    return `${coords.x}:${coords.y}:${coords.z}`
  }

  _removeOutOfBoundsTiles(tileRange) {
    const tilesToRemove = []
    
    this._tiles.forEach((tile, key) => {
      const coords = this._keyToTileCoords(key)
      if (coords.x < tileRange.min.x || coords.x > tileRange.max.x ||
          coords.y < tileRange.min.y || coords.y > tileRange.max.y) {
        tilesToRemove.push(key)
      }
    })
    
    tilesToRemove.forEach(key => {
      const tile = this._tiles.get(key)
      if (tile && tile.parentNode) {
        tile.parentNode.removeChild(tile)
      }
      this._tiles.delete(key)
    })
  }

  _keyToTileCoords(key) {
    const parts = key.split(':')
    return {
      x: parseInt(parts[0]),
      y: parseInt(parts[1]),
      z: parseInt(parts[2])
    }
  }

  async _loadTile(coords) {
    const key = this._tileCoordsToKey(coords)
    this._loading.add(key)
    
    try {
      const bbox = this._getTileBounds(coords)
      const imageUrl = await this._requestWMSImage(bbox, coords.z)
      
      const img = L.DomUtil.create('img', 'leaflet-tile')
      img.style.position = 'absolute'
      img.style.left = (coords.x * this.options.tileSize) + 'px'
      img.style.top = (coords.y * this.options.tileSize) + 'px'
      img.style.width = this.options.tileSize + 'px'
      img.style.height = this.options.tileSize + 'px'
      img.style.opacity = this.options.opacity
      img.style.zIndex = this.options.zIndex
      
      img.onload = () => {
        this._tiles.set(key, img)
        this._loading.delete(key)
        
        if (this._container) {
          this._container.appendChild(img)
        }
      }
      
      img.onerror = () => {
        console.error('WMS瓦片加载失败:', coords)
        this._loading.delete(key)
        this.fire('tileerror', { coords, error: new Error('瓦片加载失败') })
      }
      
      img.src = imageUrl
      
    } catch (error) {
      console.error('WMS POST请求失败:', error)
      this._loading.delete(key)
      this.fire('tileerror', { coords, error })
    }
  }

  _getTileBounds(coords) {
    const map = this._map
    const tileSize = this.options.tileSize
    const zoom = coords.z
    
    const nwPoint = new L.Point(coords.x * tileSize, coords.y * tileSize)
    const sePoint = new L.Point((coords.x + 1) * tileSize, (coords.y + 1) * tileSize)
    
    const nw = map.unproject(nwPoint, zoom)
    const se = map.unproject(sePoint, zoom)
    
    return {
      minx: nw.lng,
      miny: se.lat,
      maxx: se.lng,
      maxy: nw.lat
    }
  }

  async _requestWMSImage(bbox, zoom) {
    const params = {
      service: 'WMS',
      request: 'GetMap',
      version: this.options.version,
      layers: this.options.layers,
      styles: this.options.styles || '',
      crs: 'EPSG:4326',
      bbox: `${bbox.minx},${bbox.miny},${bbox.maxx},${bbox.maxy}`,
      width: this.options.tileSize,
      height: this.options.tileSize,
      format: this.options.format,
      transparent: this.options.transparent,
      ...this.options.extraParams
    }
    
    // 检查是否有SLD_BODY参数，如果有则使用POST请求
    if (this.options.extraParams && this.options.extraParams.SLD_BODY) {
      return this._requestWithPost(params)
    } else {
      return this._requestWithGet(params)
    }
  }

  async _requestWithPost(params) {
    try {
      // 使用FormData发送POST请求
      const formData = new FormData()
      Object.entries(params).forEach(([key, value]) => {
        formData.append(key, value)
      })
      
      const response = await axios.post(this.url, formData, {
        responseType: 'blob',
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      
      // 创建Blob URL
      const blob = response.data
      return URL.createObjectURL(blob)
      
    } catch (error) {
      console.error('WMS POST请求失败:', error)
      throw error
    }
  }

  _requestWithGet(params) {
    const searchParams = new URLSearchParams(params)
    return `${this.url}?${searchParams.toString()}`
  }

  setOpacity(opacity) {
    this.options.opacity = opacity
    this._tiles.forEach(tile => {
      tile.style.opacity = opacity
    })
    return this
  }

  setParams(params, noRedraw) {
    this.options.extraParams = { ...this.options.extraParams, ...params }
    if (!noRedraw) {
      this._reset()
      this._update()
    }
    return this
  }

  getParams() {
    return this.options.extraParams || {}
  }
}

// 便捷函数
export const wmsPostLayer = (url, options) => {
  return new WMSPostLayer(url, options)
}

export default WMSPostLayer 