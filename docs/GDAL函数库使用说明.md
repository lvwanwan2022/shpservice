# GDAL函数库使用说明

## 📋 概述

根据您提供的《GIS空间分析常规功能需求.pdf》文档，我已经创建了一个完整的GDAL函数库JSON文档，包含了PDF中提到的所有GIS分析方法，并按功能分类组织。

## 🎯 主要功能覆盖

### 1. 坐标转换功能（完全对应PDF需求）
- ✅ **地理坐标系转换**：标准地理坐标系转换
- ✅ **投影坐标系转换**：标准投影坐标系、工程坐标系
- ✅ **坐标查询**：当前数据查询、当前图层查询

### 2. 矢量分析功能（完全对应PDF需求）

#### 常规分析
- ✅ **构建缓冲区**：点、线、面缓冲区分析
- ✅ **裁剪分析**：线→面、线→线、面→面
- ✅ **相交分析**：线→面、线→线、面→面（线线相交得到点）
- ✅ **差集分析**：面→面、线→线、点→点
- ✅ **融合分析**：点、线、面，按目标字段合并同类项
- ✅ **联合分析**：面→面、线→线、点→点，多个数据构建更大区域
- ✅ **合并图层**：点、线、面，多表合并

#### 非常规分析
- ✅ **按属性字段连接图层**：任意类型矢量要素间的同字段连接
- ✅ **按属性字段提取要素**：属性筛选功能
- ✅ **按属性字段选择要素**：在视口中按属性过滤显示

### 3. 栅格分析功能（完全对应PDF需求）

#### 常规分析
- ✅ **DEM高程分析**：坡度分析、平整度分析
- ✅ **提取等高线**：从DEM生成等高线
- ✅ **DOM影像拼接**：多影像拼接处理
- ✅ **多期影像叠加分析**：变化检测和动态对比

#### 遥感分析
- ✅ **NDVI植被指数计算**：植被分析
- ✅ **影像变化检测**：多期对比分析

### 4. 表格分析功能（完全对应PDF需求）
- ✅ **带地理坐标的CSV**：添加到页面并可视化

## 🏗️ JSON结构说明

### 主要结构
```json
{
  "gdal_functions": {
    "coordinate_operations": {},    // 坐标操作
    "vector_analysis": {},         // 矢量分析
    "raster_analysis": {},         // 栅格分析
    "table_analysis": {},          // 表格分析
    "raster_operations": {},       // 栅格操作
    "utility_operations": {},      // 实用工具
    "specialized_operations": {},   // 专业分析
    "common_patterns": {}          // 常用模式
  },
  "metadata": {}                   // 元数据信息
}
```

### 每个函数包含的信息
```json
{
  "function_name": "函数名",
  "description": "功能描述",
  "category": "功能分类",
  "input_types": ["输入数据类型"],
  "parameters": {
    "参数名": {
      "type": "参数类型",
      "description": "参数描述",
      "required": true/false,
      "example": "示例值",
      "options": ["可选值列表"]
    }
  },
  "python_template": "Python代码模板",
  "command_template": "命令行模板",
  "examples": [
    {
      "description": "示例描述",
      "code": "示例代码"
    }
  ]
}
```

## 💻 前端使用方法

### 1. 读取JSON数据
```javascript
// 在Vue组件中加载GDAL函数库
import gdalFunctions from './GDAL函数库.json'

export default {
  data() {
    return {
      gdalLib: gdalFunctions.gdal_functions,
      currentCategory: null,
      selectedFunction: null,
      parameters: {}
    }
  }
}
```

### 2. 构建功能分类列表
```javascript
// 获取所有功能分类
const categories = Object.keys(this.gdalLib)

// 构建分类菜单
const categoryMenu = categories.map(cat => ({
  name: cat,
  label: this.getCategoryLabel(cat),
  functions: Object.keys(this.gdalLib[cat])
}))
```

### 3. 生成参数配置界面
```javascript
// 根据选中的函数生成参数表单
generateParameterForm(functionDef) {
  const parameters = functionDef.parameters
  const formItems = []
  
  Object.keys(parameters).forEach(paramName => {
    const param = parameters[paramName]
    formItems.push({
      name: paramName,
      label: param.description,
      type: param.type,
      required: param.required,
      options: param.options,
      example: param.example,
      default: param.default
    })
  })
  
  return formItems
}
```

### 4. 生成Python代码
```javascript
// 根据用户输入的参数生成可执行的Python代码
generatePythonCode(functionDef, userParams) {
  let template = functionDef.python_template
  
  // 替换模板中的参数占位符
  Object.keys(userParams).forEach(paramName => {
    const value = userParams[paramName]
    const placeholder = `{${paramName}}`
    template = template.replace(new RegExp(placeholder, 'g'), value)
  })
  
  return template
}
```

### 5. 构建完整的界面组件

```vue
<template>
  <div class="gdal-calculator">
    <!-- 功能分类选择 -->
    <el-menu @select="onCategorySelect">
      <el-submenu v-for="category in categories" :key="category.name">
        <span slot="title">{{ category.label }}</span>
        <el-menu-item 
          v-for="func in category.functions" 
          :key="func"
          @click="selectFunction(category.name, func)">
          {{ gdalLib[category.name][func].description }}
        </el-menu-item>
      </el-submenu>
    </el-menu>
    
    <!-- 参数配置面板 -->
    <div v-if="selectedFunction" class="parameter-panel">
      <h3>{{ selectedFunction.description }}</h3>
      
      <el-form :model="parameters" label-width="120px">
        <el-form-item 
          v-for="param in parameterList" 
          :key="param.name"
          :label="param.label"
          :required="param.required">
          
          <!-- 文件选择器 -->
          <el-select v-if="param.type === 'string' && param.name.includes('input')"
                     v-model="parameters[param.name]"
                     placeholder="选择文件">
            <el-option v-for="file in availableFiles" 
                       :key="file.name" 
                       :label="file.name" 
                       :value="file.path"/>
          </el-select>
          
          <!-- 数值输入 -->
          <el-input-number v-else-if="param.type === 'number'"
                           v-model="parameters[param.name]"
                           :placeholder="param.example"/>
          
          <!-- 选项选择 -->
          <el-select v-else-if="param.options"
                     v-model="parameters[param.name]"
                     :placeholder="param.default">
            <el-option v-for="option in param.options" 
                       :key="option" 
                       :label="option" 
                       :value="option"/>
          </el-select>
          
          <!-- 普通文本输入 -->
          <el-input v-else 
                    v-model="parameters[param.name]"
                    :placeholder="param.example"/>
        </el-form-item>
      </el-form>
      
      <!-- 代码预览 -->
      <div class="code-preview">
        <h4>生成的Python代码：</h4>
        <pre><code>{{ generatedCode }}</code></pre>
      </div>
      
      <!-- 执行按钮 -->
      <el-button type="primary" @click="executeCode">执行分析</el-button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'GdalCalculator',
  data() {
    return {
      gdalLib: require('./GDAL函数库.json').gdal_functions,
      selectedFunction: null,
      parameters: {},
      availableFiles: [] // 从文件管理系统获取
    }
  },
  computed: {
    categories() {
      return Object.keys(this.gdalLib).map(cat => ({
        name: cat,
        label: this.getCategoryLabel(cat),
        functions: Object.keys(this.gdalLib[cat])
      }))
    },
    parameterList() {
      if (!this.selectedFunction) return []
      return Object.keys(this.selectedFunction.parameters).map(paramName => ({
        name: paramName,
        ...this.selectedFunction.parameters[paramName]
      }))
    },
    generatedCode() {
      if (!this.selectedFunction) return ''
      return this.generatePythonCode(this.selectedFunction, this.parameters)
    }
  },
  methods: {
    selectFunction(category, functionName) {
      this.selectedFunction = this.gdalLib[category][functionName]
      this.parameters = {}
      
      // 设置默认值
      Object.keys(this.selectedFunction.parameters).forEach(paramName => {
        const param = this.selectedFunction.parameters[paramName]
        if (param.default !== undefined) {
          this.parameters[paramName] = param.default
        }
      })
    },
    
    generatePythonCode(functionDef, userParams) {
      let template = functionDef.python_template
      Object.keys(userParams).forEach(paramName => {
        const value = userParams[paramName]
        template = template.replace(new RegExp(`{${paramName}}`, 'g'), value)
      })
      return template
    },
    
    async executeCode() {
      try {
        const response = await this.$http.post('/api/gdal/execute', {
          code: this.generatedCode,
          function_name: this.selectedFunction.function_name,
          parameters: this.parameters
        })
        
        if (response.data.success) {
          this.$message.success('执行成功')
          // 处理结果，更新地图显示等
          this.handleExecutionResult(response.data.result)
        } else {
          this.$message.error('执行失败：' + response.data.error)
        }
      } catch (error) {
        this.$message.error('执行出错：' + error.message)
      }
    },
    
    getCategoryLabel(category) {
      const labels = {
        coordinate_operations: '坐标操作',
        vector_analysis: '矢量分析',
        raster_analysis: '栅格分析',
        table_analysis: '表格分析',
        raster_operations: '栅格操作',
        utility_operations: '实用工具',
        specialized_operations: '专业分析'
      }
      return labels[category] || category
    }
  }
}
</script>
```

## 🔧 后端集成方案

### 1. 创建GDAL执行路由
```python
# backend/routes/gdal_routes.py
from flask import Blueprint, request, jsonify
from services.gdal_execution_service import GdalExecutionService

gdal_bp = Blueprint('gdal', __name__)

@gdal_bp.route('/execute', methods=['POST'])
def execute_gdal():
    data = request.json
    code = data.get('code')
    function_name = data.get('function_name')
    parameters = data.get('parameters', {})
    
    try:
        service = GdalExecutionService()
        result = service.execute_safe(code, function_name, parameters)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
```

### 2. 安全执行服务
```python
# backend/services/gdal_execution_service.py
import subprocess
import tempfile
import os
from pathlib import Path

class GdalExecutionService:
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / 'gdal_execution'
        self.temp_dir.mkdir(exist_ok=True)
    
    def execute_safe(self, code, function_name, parameters):
        # 验证代码安全性
        if not self.validate_code(code):
            raise ValueError("代码包含不安全的操作")
        
        # 创建临时执行文件
        script_file = self.temp_dir / f'{function_name}_{os.getpid()}.py'
        
        try:
            with open(script_file, 'w', encoding='utf-8') as f:
                f.write(code)
            
            # 在容器中执行
            result = self.execute_in_container(script_file)
            return result
            
        finally:
            # 清理临时文件
            if script_file.exists():
                script_file.unlink()
    
    def validate_code(self, code):
        # 检查代码中是否包含危险操作
        dangerous_keywords = ['import os', 'subprocess', 'eval', 'exec', '__import__']
        return not any(keyword in code for keyword in dangerous_keywords)
    
    def execute_in_container(self, script_file):
        # 使用Docker容器执行GDAL代码
        cmd = [
            'docker', 'run', '--rm',
            '-v', f'{self.temp_dir}:/workspace',
            '-v', f'{self.get_data_dir()}:/data',
            'osgeo/gdal:alpine-small-latest',
            'python', f'/workspace/{script_file.name}'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"执行失败: {result.stderr}")
        
        return result.stdout
```

## 📊 使用统计和分析

该JSON库提供的功能完全覆盖了PDF文档中提到的需求：

### ✅ 完全实现的功能
1. **坐标转换** - 2个函数
2. **矢量分析** - 8个主要分析功能
3. **栅格分析** - 4个主要分析功能  
4. **表格分析** - 1个转换功能
5. **扩展功能** - 30+ 个其他GDAL/OGR函数

### 📈 总计
- **45个GDAL函数**
- **8个功能分类**
- **完整的参数定义**
- **Python和命令行模板**
- **实际代码示例**

这个JSON文档可以直接用于您的前端界面，让用户通过图形化配置生成GDAL代码并执行GIS分析任务！ 