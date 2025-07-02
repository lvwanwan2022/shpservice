/**
 * 瓦片计算工具模块
 * 包含所有与瓦片坐标、边界、范围计算相关的函数
 */

/**
 * 经纬度转瓦片坐标
 */
export function latLonToTile(lat, lon, zoom) {
  const x = Math.floor((lon + 180) / 360 * Math.pow(2, zoom));
  const y = Math.floor((1 - Math.log(Math.tan(lat * Math.PI / 180) + 1 / Math.cos(lat * Math.PI / 180)) / Math.PI) / 2 * Math.pow(2, zoom));
  return { x, y };
}

/**
 * 瓦片坐标转经纬度
 */
export function tileToLatLon(x, y, zoom) {
  const n = Math.pow(2, zoom);
  const lon = x / n * 360 - 180;
  const lat = Math.atan(Math.sinh(Math.PI * (1 - 2 * y / n))) * 180 / Math.PI;
  return { lat, lon };
}

/**
 * 计算瓦片的地理边界
 */
export function getTileBounds(z, x, y) {
  const n = Math.pow(2, z);
  const lonDeg = (x / n) * 360.0 - 180.0;
  const latRad = Math.atan(Math.sinh(Math.PI * (1 - 2 * y / n)));
  const latDeg = (latRad * 180.0) / Math.PI;
  
  const lonDeg2 = ((x + 1) / n) * 360.0 - 180.0;
  const latRad2 = Math.atan(Math.sinh(Math.PI * (1 - 2 * (y + 1) / n)));
  const latDeg2 = (latRad2 * 180.0) / Math.PI;
  
  return [
    [lonDeg, latDeg],
    [lonDeg2, latDeg],
    [lonDeg2, latDeg2],
    [lonDeg, latDeg2],
    [lonDeg, latDeg]
  ];
}

/**
 * 计算包含指定区域的瓦片范围
 */
export function calculateTileRange(bounds, zoom) {
  const north = bounds.north || bounds.top;
  const south = bounds.south || bounds.bottom;
  const east = bounds.east || bounds.right;
  const west = bounds.west || bounds.left;
  
  const nw = latLonToTile(north, west, zoom);
  const se = latLonToTile(south, east, zoom);
  
  return {
    minX: Math.min(nw.x, se.x),
    minY: Math.min(nw.y, se.y),
    maxX: Math.max(nw.x, se.x),
    maxY: Math.max(nw.y, se.y)
  };
}

/**
 * 根据bounds和缩放级别范围计算所有需要加载的瓦片坐标列表
 */
export function calculateTileList(bounds, zoomLevels) {
  const tileList = [];
  
  let minZoom, maxZoom;
  if (typeof zoomLevels === 'number') {
    minZoom = maxZoom = zoomLevels;
  } else if (Array.isArray(zoomLevels)) {
    minZoom = Math.min(...zoomLevels);
    maxZoom = Math.max(...zoomLevels);
  } else {
    minZoom = zoomLevels.min || zoomLevels.minZoom || 0;
    maxZoom = zoomLevels.max || zoomLevels.maxZoom || 18;
  }
  
  for (let z = minZoom; z <= maxZoom; z++) {
    const tileRange = calculateTileRange(bounds, z);
    
    for (let x = tileRange.minX; x <= tileRange.maxX; x++) {
      for (let y = tileRange.minY; y <= tileRange.maxY; y++) {
        tileList.push({ z, x, y });
      }
    }
  }
  
  return tileList;
}

/**
 * 计算瓦片范围内的瓦片总数
 */
export function calculateTileCount(bounds, zoomLevels) {
  let totalCount = 0;
  
  let minZoom, maxZoom;
  if (typeof zoomLevels === 'number') {
    minZoom = maxZoom = zoomLevels;
  } else if (Array.isArray(zoomLevels)) {
    minZoom = Math.min(...zoomLevels);
    maxZoom = Math.max(...zoomLevels);
  } else {
    minZoom = zoomLevels.min || zoomLevels.minZoom || 0;
    maxZoom = zoomLevels.max || zoomLevels.maxZoom || 18;
  }
  
  for (let z = minZoom; z <= maxZoom; z++) {
    const tileRange = calculateTileRange(bounds, z);
    const count = (tileRange.maxX - tileRange.minX + 1) * (tileRange.maxY - tileRange.minY + 1);
    totalCount += count;
  }
  
  return totalCount;
}

/**
 * 构建瓦片URL
 */
export function buildTileUrl(urlTemplate, z, x, y) {
  return urlTemplate
    .replace(/\{z\}/g, z.toString())
    .replace(/\{x\}/g, x.toString())
    .replace(/\{y\}/g, y.toString())
    .replace(/\{-y\}/g, (Math.pow(2, z) - 1 - y).toString());
}

/**
 * 从URL中提取瓦片坐标
 */
export function extractTileCoordinates(url) {
  const patterns = [
    /[/&](\d+)\/(\d+)\/(\d+)(?:\.|$)/,
    /z=(\d+).*?x=(\d+).*?y=(\d+)/,
    /y=(\d+).*?x=(\d+).*?z=(\d+)/
  ];
  
  for (const pattern of patterns) {
    const match = url.match(pattern);
    if (match) {
      if (pattern.source.includes('z=')) {
        if (pattern.source.startsWith('z=')) {
          return { z: parseInt(match[1]), x: parseInt(match[2]), y: parseInt(match[3]) };
        } else {
          return { z: parseInt(match[3]), x: parseInt(match[2]), y: parseInt(match[1]) };
        }
      } else {
        return { z: parseInt(match[1]), x: parseInt(match[2]), y: parseInt(match[3]) };
      }
    }
  }
  
  return null;
}

/**
 * 格式化文件大小
 */
export function formatFileSize(bytes) {
  if (bytes === 0) return '0 B';
  
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * 格式化时间差
 */
export function formatTimeAgo(timestamp) {
  const now = Date.now();
  const diff = now - timestamp;
  
  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  
  if (days > 0) return `${days}天前`;
  if (hours > 0) return `${hours}小时前`;
  if (minutes > 0) return `${minutes}分钟前`;
  return `${seconds}秒前`;
} 