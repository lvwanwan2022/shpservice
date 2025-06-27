# 图层顺序管理功能说明

## 🎯 功能概述

OpenLayers地图浏览页面现已支持完整的图层顺序管理功能，确保图层按照正确的显示顺序进行排列和渲染。

## 📋 功能特性

### 1. 图层卡片显示顺序
- **前端显示**：左侧图层卡片按 `layer_order` 字段**从大到小**排列
- **顺序规则**：`layer_order` 值大的图层显示在上方
- **实时更新**：图层顺序变更后自动刷新显示

### 2. 地图图层渲染顺序
- **渲染顺序**：`layer_order` 值大的图层在地图最上层显示
- **zIndex设置**：图层的 `zIndex` 直接使用 `layer_order` 值
- **支持类型**：Martin图层和GeoServer图层均支持

### 3. 新增图层顺序分配
- **自动分配**：添加新图层时，`layer_order` 自动设置为当前场景最大值+1
- **确保置顶**：新添加的图层总是显示在最上层
- **避免冲突**：自动避免顺序值重复

## 🔧 技术实现

### 后端逻辑
```sql
-- 获取当前场景最大图层顺序
SELECT COALESCE(MAX(layer_order), 0) as max_order
FROM scene_layers
WHERE scene_id = %(scene_id)s

-- 新图层设置为最大值+1
layer_order = max_order + 1
```

### 前端显示排序
```javascript
// 图层卡片按order降序排列（大的在上面）
const sortedLayersList = computed(() => {
  return [...layersList.value].sort((a, b) => {
    const orderA = a.layer_order || 0
    const orderB = b.layer_order || 0
    return orderB - orderA // 降序排列
  })
})
```

### 地图图层排序
```javascript
// 地图添加时按order升序（小的先添加，大的在上层）
const sortedLayers = [...layersList.value].sort((a, b) => {
  const orderA = a.layer_order || 0
  const orderB = b.layer_order || 0
  return orderA - orderB // 升序排列
})

// 设置图层zIndex
zIndex: layer.layer_order || 1
```

## 📊 使用示例

### 场景示例
假设某个场景有以下图层：

| 图层名称 | layer_order | 显示位置 |
|---------|-------------|----------|
| 建筑物   | 5          | 最上层   |
| 道路     | 3          | 中间层   |
| 地形     | 1          | 最下层   |

**前端卡片显示顺序**：建筑物 → 道路 → 地形
**地图渲染顺序**：地形(底层) → 道路(中层) → 建筑物(顶层)

### 添加新图层
当添加新图层"标注"时：
1. 系统查询当前最大 `layer_order` = 5
2. 新图层 `layer_order` = 6
3. 结果：标注图层显示在最上方

## 🎮 用户操作

### 查看图层顺序
- 打开任意场景，左侧面板显示图层卡片
- 卡片从上到下按优先级排列
- 数值大的图层在上方

### 调整图层顺序
- 使用现有的上移/下移按钮
- 系统自动更新 `layer_order` 值
- 地图实时刷新显示顺序

### 添加新图层
- 通过"添加图层"对话框选择文件
- 新图层自动分配最高优先级
- 新图层显示在最上方

## 🔍 调试信息

### 查看图层order值
```javascript
// 在浏览器控制台执行
console.log('图层顺序信息:', layersList.value.map(layer => ({
  name: layer.layer_name,
  order: layer.layer_order,
  zIndex: layer.zIndex
})))
```

### 验证渲染顺序
```javascript
// 检查地图图层的zIndex
map.value.getLayers().forEach(layer => {
  console.log('图层zIndex:', layer.getZIndex(), '图层名:', layer.get('layerName'))
})
```

## 🚀 后续优化

1. **拖拽排序**：支持鼠标拖拽调整图层顺序
2. **批量操作**：支持批量调整多个图层顺序
3. **顺序模板**：保存常用的图层顺序配置
4. **可视化指示**：显示图层顺序数值

## 🐛 故障排除

### 图层顺序不正确
1. 检查数据库中的 `layer_order` 字段值
2. 确认前端排序逻辑正确执行
3. 验证地图图层的 `zIndex` 设置

### 新图层未置顶
1. 检查后端自动分配逻辑
2. 确认API返回的图层包含 `layer_order` 字段
3. 验证前端添加图层后的刷新逻辑

---

*本功能已在MapViewOL.vue和MapViewOLCache.vue中实现，确保了一致的用户体验。* 