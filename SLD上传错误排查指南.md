# SLD样式文件上传错误排查指南

## 问题描述
在"图层样式设置"对话框的SLD选项卡中上传SLD样式文件时，出现 400 Bad Request 错误。

## 错误信息
```
POST http://10.20.124.20:8080/api/sld-styles/upload 400 (BAD REQUEST)
API请求错误: Request failed with status code 400
```

## 可能的原因

### 1. 缺少必填参数
后端需要以下必填参数：
- `file`: SLD文件（必填）
- `name`: 样式名称（必填）
- `geometry_type`: 几何类型（必填，值必须是 'point', 'line', 或 'polygon'）
- `description`: 样式描述（可选）

### 2. 几何类型未选择
在上传对话框中，必须先选择几何类型（点图层/线图层/面图层）才能上传。

### 3. SLD文件格式问题
- 文件必须是 `.sld` 扩展名
- SLD文件内容必须是有效的XML格式
- SLD内容必须包含与所选几何类型匹配的符号化器

### 4. 文件编码问题
SLD文件必须是UTF-8编码

## 调试步骤

### 步骤1: 检查前端日志
已在前端代码中添加了详细的调试日志。请按以下步骤操作：

1. 打开浏览器开发者工具（F12）
2. 切换到 Console 标签
3. 尝试上传SLD文件
4. 查看控制台输出，应该会看到：
   ```
   准备上传SLD文件:
   - name: xxx
   - description: xxx
   - geometry_type: xxx
   - file: File对象
   
   FormData 内容:
   name: xxx
   description: xxx
   geometry_type: xxx
   file: File对象
   ```

5. 如果看到错误详情，记录下来

### 步骤2: 检查后端日志
已在后端代码中添加了详细的调试日志。请检查后端日志：

**Windows PowerShell:**
```powershell
# 查看后端运行的终端输出
# 或者如果有日志文件，查看日志文件
Get-Content -Path "logs\*.log" -Tail 100
```

后端日志会显示：
```
=== 开始处理SLD文件上传请求 ===
请求文件: ['file']
请求表单: {'name': 'xxx', 'description': 'xxx', 'geometry_type': 'xxx'}
文件名: xxx.sld
样式名称: xxx
样式描述: xxx
几何类型: xxx
```

### 步骤3: 常见问题检查清单

- [ ] 是否选择了几何类型（点图层/线图层/面图层）？
- [ ] 是否填写了样式名称？
- [ ] 是否选择了SLD文件？
- [ ] SLD文件扩展名是否为 `.sld`？
- [ ] SLD文件大小是否超过10MB？
- [ ] 后端服务是否正在运行？
- [ ] 网络连接是否正常？

## 解决方案

### 方案1: 确保所有必填字段已填写
1. 在上传对话框中，确保填写了"样式名称"
2. 选择"几何类型"（点图层/线图层/面图层）
3. 点击"选择文件"按钮，选择一个有效的.sld文件
4. 点击"上传"按钮

### 方案2: 验证SLD文件格式
确保SLD文件是有效的XML格式，并包含正确的符号化器：

**点图层示例:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.0.0" xmlns="http://www.opengis.net/sld">
  <NamedLayer>
    <Name>point_style</Name>
    <UserStyle>
      <FeatureTypeStyle>
        <Rule>
          <PointSymbolizer>
            <Graphic>
              <Mark>
                <WellKnownName>circle</WellKnownName>
                <Fill>
                  <CssParameter name="fill">#FF0000</CssParameter>
                </Fill>
              </Mark>
              <Size>6</Size>
            </Graphic>
          </PointSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>
```

**线图层示例:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.0.0" xmlns="http://www.opengis.net/sld">
  <NamedLayer>
    <Name>line_style</Name>
    <UserStyle>
      <FeatureTypeStyle>
        <Rule>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#0000FF</CssParameter>
              <CssParameter name="stroke-width">2</CssParameter>
            </Stroke>
          </LineSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>
```

**面图层示例:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.0.0" xmlns="http://www.opengis.net/sld">
  <NamedLayer>
    <Name>polygon_style</Name>
    <UserStyle>
      <FeatureTypeStyle>
        <Rule>
          <PolygonSymbolizer>
            <Fill>
              <CssParameter name="fill">#00FF00</CssParameter>
              <CssParameter name="fill-opacity">0.5</CssParameter>
            </Fill>
            <Stroke>
              <CssParameter name="stroke">#000000</CssParameter>
              <CssParameter name="stroke-width">1</CssParameter>
            </Stroke>
          </PolygonSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>
```

### 方案3: 检查后端服务
确保后端服务正在运行并且可以访问：

```powershell
# 测试后端API是否可访问
Invoke-WebRequest -Uri "http://10.20.124.20:8080/api/sld-styles" -Method GET
```

## 下一步操作

1. **重启前端开发服务器**（如果已修改代码）
   ```powershell
   cd simple_frontend
   npm run serve
   ```

2. **重启后端服务器**（如果已修改代码）
   ```powershell
   cd backend
   python app.py
   ```

3. **清除浏览器缓存**
   - 按 Ctrl+Shift+Delete
   - 选择"缓存的图像和文件"
   - 点击"清除数据"

4. **重新测试上传功能**
   - 打开浏览器开发者工具（F12）
   - 尝试上传SLD文件
   - 查看Console和Network标签中的详细信息

## 获取更多帮助

如果问题仍然存在，请提供以下信息：

1. 浏览器控制台的完整错误日志
2. 后端服务器的日志输出
3. 使用的SLD文件内容（前几行）
4. 上传时填写的表单数据（样式名称、几何类型等）

这些信息将帮助进一步诊断问题。
