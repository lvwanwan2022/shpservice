<template>
  <div class="error-diagnostic-tool">
    <el-card header="GeoServer错误诊断工具">
      <div class="test-info">
        <p><strong>说明:</strong> 这个工具专门用于诊断GeoServer返回的错误信息</p>
      </div>
      
      <div class="layer-input">
        <el-input 
          v-model="testLayerName" 
          placeholder="输入图层名称进行错误诊断"
          @keyup.enter="diagnoseLayer"
        >
          <template #prepend>图层名称</template>
          <template #append>
            <el-button @click="diagnoseLayer">诊断错误</el-button>
          </template>
        </el-input>
      </div>
      
      <div class="quick-tests">
        <el-button @click="testExistingLayers" type="success">
          测试已知存在的图层
        </el-button>
        
        <el-button @click="testNonExistentLayer" type="warning">
          测试不存在的图层
        </el-button>
        
        <el-button @click="clearResults" type="info">
          清除结果
        </el-button>
      </div>
      
      <div class="test-results" v-if="results.length > 0">
        <h4>诊断结果:</h4>
        <div v-for="(result, index) in results" :key="index" :class="['result-item', result.type]">
          <div class="result-header">
            <span class="result-time">{{ result.time }}</span>
            <span class="result-message">{{ result.message }}</span>
          </div>
          <div v-if="result.details" class="result-details">
            <pre>{{ result.details }}</pre>
          </div>
          <div v-if="result.url" class="result-url">
            <strong>测试URL:</strong> 
            <a :href="result.url" target="_blank">{{ result.url }}</a>
          </div>
          <div v-if="result.xmlError" class="xml-error">
            <h5>GeoServer错误信息:</h5>
            <pre class="xml-content">{{ result.xmlError }}</pre>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

export default {
  name: 'ErrorDiagnosticTool',
  setup() {
    const results = ref([])
    const testLayerName = ref('shpservice:700f4b56b4954f2d87f11f1ab634a03c')
    
    const addResult = (message, type = 'info', details = null, url = null, xmlError = null) => {
      results.value.push({
        time: new Date().toLocaleTimeString(),
        message,
        type,
        details,
        url,
        xmlError,
        timestamp: Date.now()
      })
    }
    
    // 诊断图层
    const diagnoseLayer = async () => {
      if (!testLayerName.value.trim()) {
        ElMessage.warning('请输入图层名称')
        return
      }
      
      await testLayerWithDiagnosis(testLayerName.value.trim())
    }
    
    // 测试已知存在的图层
    const testExistingLayers = async () => {
      const existingLayers = [
        'shpservice:700f4b56b4954f2d87f11f1ab634a03c',
        'shpservice:lvtestwfs'
      ]
      
      addResult('开始测试已知存在的图层...', 'info')
      
      for (const layerName of existingLayers) {
        await testLayerWithDiagnosis(layerName)
        // 添加延迟避免请求过快
        await new Promise(resolve => setTimeout(resolve, 1000))
      }
      
      addResult('已知图层测试完成', 'info')
    }
    
    // 测试不存在的图层
    const testNonExistentLayer = async () => {
      addResult('测试不存在的图层以查看错误格式...', 'info')
      await testLayerWithDiagnosis('shpservice:non_existent_layer')
    }
    
    // 带诊断的图层测试
    const testLayerWithDiagnosis = async (layerName) => {
      addResult(`开始诊断图层: ${layerName}`, 'info')
      
      try {
        // 使用text响应类型以便读取XML错误
        const getMapUrl = `/geoserver/wms?service=WMS&version=1.1.1&request=GetMap&layers=${layerName}&styles=&bbox=-180,-90,180,90&width=256&height=256&srs=EPSG:4326&format=image/png&transparent=true`
        
        addResult(`测试URL: ${getMapUrl}`, 'info', null, `${window.location.origin}${getMapUrl}`)
        
        const response = await axios.get(getMapUrl, { 
          timeout: 15000,
          responseType: 'text' // 使用text类型以便读取XML
        })
        
        if (response.status === 200) {
          const contentType = response.headers['content-type']
          
          if (contentType && contentType.includes('image')) {
            addResult(`✅ 图层 ${layerName} 渲染成功`, 'success', 
              `内容类型: ${contentType}\n响应大小: ${response.data.length} 字符`)
          } else if (contentType && contentType.includes('xml')) {
            // 解析XML错误信息
            const xmlContent = response.data
            addResult(`❌ 图层 ${layerName} 返回错误`, 'error', 
              `内容类型: ${contentType}`, null, xmlContent)
            
            // 尝试提取具体错误信息
            const errorMatch = xmlContent.match(/<ServiceException[^>]*>(.*?)<\/ServiceException>/s)
            if (errorMatch) {
              const errorMessage = errorMatch[1].trim()
              addResult(`🔍 错误详情`, 'error', errorMessage)
            }
          } else {
            addResult(`⚠️ 未知响应格式`, 'warning', 
              `内容类型: ${contentType}\n响应内容: ${response.data.substring(0, 200)}...`)
          }
        } else {
          addResult(`❌ 请求失败`, 'error', `状态码: ${response.status}`)
        }
        
      } catch (error) {
        addResult(`❌ 诊断失败`, 'error', 
          `错误: ${error.message}\n状态码: ${error.response?.status || 'N/A'}`)
        
        // 如果有响应数据，也尝试显示
        if (error.response && error.response.data) {
          addResult(`🔍 错误响应内容`, 'error', null, null, error.response.data)
        }
      }
    }
    
    // 清除结果
    const clearResults = () => {
      results.value = []
    }
    
    return {
      results,
      testLayerName,
      diagnoseLayer,
      testExistingLayers,
      testNonExistentLayer,
      clearResults
    }
  }
}
</script>

<style scoped>
.error-diagnostic-tool {
  margin: 10px 0;
}

.test-info {
  margin-bottom: 15px;
  padding: 10px;
  background-color: #f0f9ff;
  border-radius: 4px;
}

.layer-input {
  margin-bottom: 15px;
}

.quick-tests {
  margin-bottom: 15px;
}

.quick-tests .el-button {
  margin-right: 10px;
  margin-bottom: 5px;
}

.test-results {
  max-height: 600px;
  overflow-y: auto;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 15px;
  background-color: #f5f7fa;
}

.result-item {
  margin-bottom: 15px;
  padding: 10px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 12px;
}

.result-item.info {
  background-color: #f0f9ff;
  border-left: 4px solid #409eff;
}

.result-item.success {
  background-color: #f0f9ff;
  border-left: 4px solid #67c23a;
}

.result-item.warning {
  background-color: #fdf6ec;
  border-left: 4px solid #e6a23c;
}

.result-item.error {
  background-color: #fef0f0;
  border-left: 4px solid #f56c6c;
}

.result-header {
  display: flex;
  align-items: center;
  margin-bottom: 5px;
}

.result-time {
  color: #909399;
  margin-right: 10px;
  font-weight: normal;
}

.result-message {
  font-weight: bold;
  flex-grow: 1;
}

.result-details {
  margin: 8px 0;
  padding: 8px;
  background-color: rgba(0, 0, 0, 0.05);
  border-radius: 3px;
  white-space: pre-wrap;
  word-break: break-all;
}

.result-url {
  margin-top: 8px;
  font-size: 11px;
}

.result-url a {
  color: #409eff;
  text-decoration: none;
  word-break: break-all;
}

.result-url a:hover {
  text-decoration: underline;
}

.xml-error {
  margin-top: 10px;
  padding: 10px;
  background-color: #fff2f0;
  border: 1px solid #ffccc7;
  border-radius: 4px;
}

.xml-error h5 {
  margin: 0 0 10px 0;
  color: #cf1322;
}

.xml-content {
  background-color: #fff;
  padding: 10px;
  border-radius: 3px;
  font-size: 11px;
  max-height: 200px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-all;
}
</style> 