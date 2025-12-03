# SLD样式应用问题修复说明

## 问题原因

虽然GeoServer支持SLD 1.1.0版本，但当前代码在调用GeoServer REST API时**没有使用 `?raw=true` 参数**，导致GeoServer在上传SLD时会进行解析和格式转换，从而丢失了样式信息。

### 具体问题

1. **接口调用方式不正确**：当前代码使用 `PUT /workspaces/{workspace}/styles/{style}` 或 `PUT /workspaces/{workspace}/styles/{style}.xml`，但没有添加 `?raw=true` 参数
2. **GeoServer的默认行为**：当不使用 `?raw=true` 时，GeoServer会：
   - 解析SLD内容
   - 尝试将SLD 1.1.0转换为1.0.0格式
   - 在转换过程中丢失样式参数（Fill、Stroke等）
   - 可能导致编码问题（中文乱码）

## 解决方案

### 修改内容

在 `backend/services/geoserver_service.py` 的 `_create_or_update_style` 方法中：

1. **添加 `?raw=true` 参数**：在URL中添加 `?raw=true` 参数，告诉GeoServer直接保存SLD内容，不进行解析和转换
2. **优先使用带raw参数的URL**：在尝试的URL列表中，优先使用带 `?raw=true` 的URL
3. **更新验证逻辑**：修改验证时获取样式的URL，确保正确获取保存后的内容

### 修改的代码位置

**文件**：`backend/services/geoserver_service.py`

**修改1**：更新现有样式时的URL（第5288-5291行）
```python
# 修改前
style_urls = [
    f"{self.rest_url}/workspaces/{encoded_workspace}/styles/{encoded_style_name}",
    f"{self.rest_url}/workspaces/{encoded_workspace}/styles/{encoded_style_name}.xml"
]

# 修改后
style_urls = [
    f"{self.rest_url}/workspaces/{encoded_workspace}/styles/{encoded_style_name}?raw=true",
    f"{self.rest_url}/workspaces/{encoded_workspace}/styles/{encoded_style_name}.xml?raw=true",
    f"{self.rest_url}/workspaces/{encoded_workspace}/styles/{encoded_style_name}",
    f"{self.rest_url}/workspaces/{encoded_workspace}/styles/{encoded_style_name}.xml"
]
```

**修改2**：创建新样式时的URL（第5375-5378行）
```python
# 修改前
style_content_urls = [
    f"{self.rest_url}/workspaces/{encoded_workspace}/styles/{encoded_style_name}",
    f"{self.rest_url}/workspaces/{encoded_workspace}/styles/{encoded_style_name}.xml"
]

# 修改后
style_content_urls = [
    f"{self.rest_url}/workspaces/{encoded_workspace}/styles/{encoded_style_name}?raw=true",
    f"{self.rest_url}/workspaces/{encoded_workspace}/styles/{encoded_style_name}.xml?raw=true",
    f"{self.rest_url}/workspaces/{encoded_workspace}/styles/{encoded_style_name}",
    f"{self.rest_url}/workspaces/{encoded_workspace}/styles/{encoded_style_name}.xml"
]
```

**修改3**：验证URL的处理（第5310-5314行和第5397-5401行）
```python
# 修改前
verify_response = requests.get(
    f"{style_url}.xml" if not style_url.endswith('.xml') else style_url,
    auth=self.auth,
    timeout=10
)

# 修改后
verify_url = style_url.split('?')[0]  # 移除查询参数
if not verify_url.endswith('.xml'):
    verify_url = f"{verify_url}.xml"
verify_response = requests.get(
    verify_url,
    auth=self.auth,
    timeout=10
)
```

## GeoServer REST API说明

### 使用 `?raw=true` 参数的优势

1. **保持原始格式**：GeoServer不会解析和转换SLD，直接保存原始内容
2. **支持SLD 1.1.0**：可以完整保留SLD 1.1.0的所有特性
3. **避免信息丢失**：不会丢失样式参数、命名空间等信息
4. **编码保持**：保持原始编码，避免中文乱码问题

### API端点说明

- **`PUT /workspaces/{workspace}/styles/{style}?raw=true`**：直接保存SLD内容，不解析
- **`PUT /workspaces/{workspace}/styles/{style}`**：GeoServer会解析和验证SLD，可能会转换格式
- **`GET /workspaces/{workspace}/styles/{style}.xml`**：获取保存的SLD内容

## 测试建议

1. **测试SLD 1.1.0格式**：上传包含 `se:` 命名空间的SLD 1.1.0文件，验证是否保持原始格式
2. **测试样式参数**：验证Fill、Stroke等样式参数是否完整保留
3. **测试中文名称**：验证中文名称是否正常显示，无乱码
4. **查看日志**：检查日志中是否有 "使用 ?raw=true 参数上传SLD" 的提示

## 预期效果

修复后，应用SLD样式时：
- ✅ SLD 1.1.0格式完整保留
- ✅ 所有样式参数（Fill、Stroke等）完整保留
- ✅ 中文名称正常显示，无乱码
- ✅ 命名空间（`se:`）保持不变
- ✅ 版本信息（`version="1.1.0"`）保持不变

## 注意事项

1. **向后兼容**：代码中仍然保留了不带 `?raw=true` 的URL作为备选，如果GeoServer版本不支持raw参数，会自动尝试其他方式
2. **验证逻辑**：验证时获取的URL需要移除查询参数，确保正确获取样式内容
3. **日志记录**：添加了日志说明使用了raw参数，便于调试和问题排查
