// 文件相关类型定义
export const FileTypes = {
  SHP: 'shp',
  TIF: 'tif',
  TIFF: 'tiff',
  DWG: 'dwg',
  DXF: 'dxf',
  GEOJSON: 'geojson',
  MBTILES: 'mbtiles',
  ZIP: 'zip'
}

export const FileDimensions = {
  TWO_D: '2D',
  THREE_D: '3D'
}

export const FileStatus = {
  UPLOADED: 'uploaded',
  PROCESSING: 'processing',
  PUBLISHED: 'published',
  ERROR: 'error'
}

export const GeometryTypes = {
  POINT: 'Point',
  LINE: 'LineString',
  POLYGON: 'Polygon',
  MULTIPOINT: 'MultiPoint',
  MULTILINESTRING: 'MultiLineString',
  MULTIPOLYGON: 'MultiPolygon',
  RASTER: 'Raster'
}

// 学科分类
export const Disciplines = {
  GEOLOGY: '地质学',
  GEOGRAPHY: '地理学',
  SURVEYING: '测绘学',
  URBAN_PLANNING: '城市规划',
  ENVIRONMENTAL: '环境科学',
  AGRICULTURE: '农业',
  FORESTRY: '林业',
  WATER_RESOURCES: '水资源',
  TRANSPORTATION: '交通运输',
  OTHER: '其他'
}

// 坐标系统
export const CoordinateSystems = {
  WGS84: 'EPSG:4326',
  WEB_MERCATOR: 'EPSG:3857',
  CGCS2000: 'EPSG:4490',
  BEIJING54: 'EPSG:4214',
  XIAN80: 'EPSG:4610',
  DUJIANGYAN: 'EPSG:404000', // 都江堰地区专用坐标系
}

// GeoServer 存储类型
export const StoreTypes = {
  DATASTORE: 'datastore',
  COVERAGESTORE: 'coveragestore'
}

// GeoServer 数据类型
export const DataTypes = {
  SHAPEFILE: 'Shapefile',
  GEOTIFF: 'GeoTIFF',
  POSTGIS: 'PostGIS',
  DIRECTORY: 'Directory',
  WORLDIMAGE: 'WorldImage'
}

// 样式格式
export const StyleFormats = {
  SLD: 'sld',
  CSS: 'css',
  YSLD: 'ysld',
  MBSTYLE: 'mbstyle'
}

// 图层组模式
export const LayerGroupModes = {
  SINGLE: 'SINGLE',
  OPAQUE_CONTAINER: 'OPAQUE_CONTAINER',
  NAMED: 'NAMED',
  CONTAINER: 'CONTAINER',
  EO: 'EO'
}

// 服务类型
export const ServiceTypes = {
  WMS: 'WMS',
  WFS: 'WFS',
  WCS: 'WCS'
}

// 文件数据结构
export class FileModel {
  constructor(data = {}) {
    this.id = data.id || null
    this.file_name = data.file_name || ''
    this.original_name = data.original_name || ''
    this.file_path = data.file_path || ''
    this.file_size = data.file_size || 0
    this.is_public = data.is_public !== undefined ? data.is_public : true
    this.discipline = data.discipline || ''
    this.dimension = data.dimension || FileDimensions.TWO_D
    this.file_type = data.file_type || ''
    this.coordinate_system = data.coordinate_system || ''
    this.tags = data.tags || ''
    this.description = data.description || ''
    this.user_id = data.user_id || null
    this.upload_date = data.upload_date || null
    this.status = data.status || FileStatus.UPLOADED
    this.bbox = data.bbox || null
    this.geometry_type = data.geometry_type || ''
    this.feature_count = data.feature_count || 0
    this.metadata = data.metadata || null
  }
}

// 工作空间数据结构
export class WorkspaceModel {
  constructor(data = {}) {
    this.id = data.id || null
    this.name = data.name || ''
    this.namespace_uri = data.namespace_uri || ''
    this.namespace_prefix = data.namespace_prefix || ''
    this.description = data.description || ''
    this.is_default = data.is_default || false
    this.created_at = data.created_at || null
    this.updated_at = data.updated_at || null
  }
}

// 存储仓库数据结构
export class StoreModel {
  constructor(data = {}) {
    this.id = data.id || null
    this.name = data.name || ''
    this.workspace_id = data.workspace_id || null
    this.store_type = data.store_type || StoreTypes.DATASTORE
    this.data_type = data.data_type || ''
    this.connection_params = data.connection_params || {}
    this.description = data.description || ''
    this.enabled = data.enabled !== undefined ? data.enabled : true
    this.file_id = data.file_id || null
    this.created_at = data.created_at || null
    this.updated_at = data.updated_at || null
  }
}

// 要素类型数据结构
export class FeatureTypeModel {
  constructor(data = {}) {
    this.id = data.id || null
    this.name = data.name || ''
    this.native_name = data.native_name || ''
    this.store_id = data.store_id || null
    this.title = data.title || ''
    this.abstract = data.abstract || ''
    this.keywords = data.keywords || []
    this.srs = data.srs || CoordinateSystems.WGS84
    this.native_bbox = data.native_bbox || null
    this.lat_lon_bbox = data.lat_lon_bbox || null
    this.attributes = data.attributes || {}
    this.enabled = data.enabled !== undefined ? data.enabled : true
    this.created_at = data.created_at || null
    this.updated_at = data.updated_at || null
  }
}

// 覆盖范围数据结构
export class CoverageModel {
  constructor(data = {}) {
    this.id = data.id || null
    this.name = data.name || ''
    this.native_name = data.native_name || ''
    this.store_id = data.store_id || null
    this.title = data.title || ''
    this.abstract = data.abstract || ''
    this.keywords = data.keywords || []
    this.srs = data.srs || CoordinateSystems.WGS84
    this.native_srs = data.native_srs || ''
    this.native_bbox = data.native_bbox || null
    this.lat_lon_bbox = data.lat_lon_bbox || null
    this.grid_info = data.grid_info || {}
    this.bands_info = data.bands_info || {}
    this.enabled = data.enabled !== undefined ? data.enabled : true
    this.created_at = data.created_at || null
    this.updated_at = data.updated_at || null
  }
}

// 图层数据结构
export class LayerModel {
  constructor(data = {}) {
    this.id = data.id || null
    this.name = data.name || ''
    this.workspace_id = data.workspace_id || null
    this.featuretype_id = data.featuretype_id || null
    this.coverage_id = data.coverage_id || null
    this.title = data.title || ''
    this.abstract = data.abstract || ''
    this.default_style = data.default_style || ''
    this.additional_styles = data.additional_styles || []
    this.enabled = data.enabled !== undefined ? data.enabled : true
    this.queryable = data.queryable !== undefined ? data.queryable : true
    this.opaque = data.opaque !== undefined ? data.opaque : false
    this.attribution = data.attribution || ''
    this.wms_url = data.wms_url || ''
    this.wfs_url = data.wfs_url || ''
    this.wcs_url = data.wcs_url || ''
    this.file_id = data.file_id || null
    this.created_at = data.created_at || null
    this.updated_at = data.updated_at || null
  }
}

// 样式数据结构
export class StyleModel {
  constructor(data = {}) {
    this.id = data.id || null
    this.name = data.name || ''
    this.workspace_id = data.workspace_id || null
    this.filename = data.filename || ''
    this.format = data.format || StyleFormats.SLD
    this.language_version = data.language_version || ''
    this.content = data.content || ''
    this.description = data.description || ''
    this.created_at = data.created_at || null
    this.updated_at = data.updated_at || null
  }
}

// 图层组数据结构
export class LayerGroupModel {
  constructor(data = {}) {
    this.id = data.id || null
    this.name = data.name || ''
    this.workspace_id = data.workspace_id || null
    this.title = data.title || ''
    this.abstract = data.abstract || ''
    this.mode = data.mode || LayerGroupModes.SINGLE
    this.layers = data.layers || []
    this.bounds = data.bounds || null
    this.enabled = data.enabled !== undefined ? data.enabled : true
    this.created_at = data.created_at || null
    this.updated_at = data.updated_at || null
  }
}

// 场景数据结构
export class SceneModel {
  constructor(data = {}) {
    this.id = data.id || null
    this.name = data.name || ''
    this.description = data.description || ''
    this.is_public = data.is_public !== undefined ? data.is_public : true
    this.user_id = data.user_id || null
    this.created_at = data.created_at || null
    this.updated_at = data.updated_at || null
  }
}

// 场景图层数据结构
export class SceneLayerModel {
  constructor(data = {}) {
    this.id = data.id || null
    this.scene_id = data.scene_id || null
    this.layer_id = data.layer_id || null
    this.layer_order = data.layer_order || 0
    this.visible = data.visible !== undefined ? data.visible : true
    this.opacity = data.opacity !== undefined ? data.opacity : 1.0
    this.style_name = data.style_name || ''
    this.custom_style = data.custom_style || null
    this.queryable = data.queryable !== undefined ? data.queryable : true
    this.selectable = data.selectable !== undefined ? data.selectable : true
    this.created_at = data.created_at || null
  }
}

// 用户数据结构
export class UserModel {
  constructor(data = {}) {
    this.id = data.id || null
    this.username = data.username || ''
    this.created_at = data.created_at || null
  }
}

// API 响应数据结构
export class ApiResponse {
  constructor(data = {}) {
    this.success = data.success !== undefined ? data.success : true
    this.message = data.message || ''
    this.data = data.data || null
    this.error = data.error || null
    this.total = data.total || 0
    this.page = data.page || 1
    this.page_size = data.page_size || 20
    this.total_pages = data.total_pages || 0
  }
}

// 分页参数
export class PaginationParams {
  constructor(data = {}) {
    this.page = data.page || 1
    this.page_size = data.page_size || 20
    this.sort_by = data.sort_by || 'created_at'
    this.sort_order = data.sort_order || 'desc'
  }
}

// 过滤参数
export class FilterParams {
  constructor(data = {}) {
    this.user_id = data.user_id || null
    this.discipline = data.discipline || ''
    this.file_type = data.file_type || ''
    this.dimension = data.dimension || ''
    this.status = data.status || ''
    this.geometry_type = data.geometry_type || ''
    this.is_public = data.is_public || null
    this.tags = data.tags || ''
    this.file_name = data.file_name || ''
  }
}

// 导出所有类型
export default {
  FileTypes,
  FileDimensions,
  FileStatus,
  GeometryTypes,
  Disciplines,
  CoordinateSystems,
  StoreTypes,
  DataTypes,
  StyleFormats,
  LayerGroupModes,
  ServiceTypes,
  FileModel,
  WorkspaceModel,
  StoreModel,
  FeatureTypeModel,
  CoverageModel,
  LayerModel,
  StyleModel,
  LayerGroupModel,
  SceneModel,
  SceneLayerModel,
  UserModel,
  ApiResponse,
  PaginationParams,
  FilterParams
} 