/**
 * 智能缓存插件安装脚本
 */

const fs = require('fs')
const path = require('path')

class PluginInstaller {
  constructor() {
    this.pluginName = 'intelligent-cache'
    this.projectRoot = this.findProjectRoot()
    this.pluginRoot = path.join(this.projectRoot, 'plugins', this.pluginName)
  }

  findProjectRoot() {
    let currentDir = __dirname
    while (currentDir !== path.dirname(currentDir)) {
      if (fs.existsSync(path.join(currentDir, 'package.json'))) {
        const packageJson = JSON.parse(
          fs.readFileSync(path.join(currentDir, 'package.json'), 'utf8')
        )
        // 检查是否是主项目（而不是插件）
        if (!packageJson.plugin) {
          return currentDir
        }
      }
      currentDir = path.dirname(currentDir)
    }
    throw new Error('无法找到项目根目录')
  }

  async install() {
    console.log('🚀 开始安装智能缓存插件...')
    
    try {
      // 1. 检查兼容性
      await this.checkCompatibility()
      
      // 2. 安装前端依赖
      await this.installFrontendDependencies()
      
      // 3. 安装后端依赖
      await this.installBackendDependencies()
      
      // 4. 修改前端配置
      await this.modifyFrontendConfig()
      
      // 5. 修改后端配置
      await this.modifyBackendConfig()
      
      // 6. 创建数据库表
      await this.createDatabaseTables()
      
      // 7. 复制模型文件
      await this.copyModelFiles()
      
      console.log('✅ 智能缓存插件安装成功！')
      console.log('')
      console.log('📋 后续步骤：')
      console.log('1. 重启前端开发服务器')
      console.log('2. 重启后端服务器')
      console.log('3. 访问 /cache-stats 查看缓存统计')
      
    } catch (error) {
      console.error('❌ 插件安装失败:', error.message)
      await this.rollback()
      process.exit(1)
    }
  }

  async checkCompatibility() {
    console.log('🔍 检查项目兼容性...')
    
    // 检查前端框架
    const frontendPackage = path.join(this.projectRoot, 'frontend', 'package.json')
    if (fs.existsSync(frontendPackage)) {
      const pkg = JSON.parse(fs.readFileSync(frontendPackage, 'utf8'))
      
      // 检查Vue版本
      if (!pkg.dependencies?.vue || !pkg.dependencies.vue.includes('3.')) {
        throw new Error('需要Vue 3.x版本')
      }
      
      console.log('✅ 前端框架兼容')
    }
    
    // 检查后端框架
    const backendRequirements = path.join(this.projectRoot, 'backend', 'requirements.txt')
    if (fs.existsSync(backendRequirements)) {
      const requirements = fs.readFileSync(backendRequirements, 'utf8')
      
      if (!requirements.includes('flask') && !requirements.includes('Flask')) {
        console.warn('⚠️  未检测到Flask，请确保后端使用Flask框架')
      } else {
        console.log('✅ 后端框架兼容')
      }
    }
  }

  async installFrontendDependencies() {
    console.log('📦 安装前端依赖...')
    
    const frontendPackage = path.join(this.projectRoot, 'frontend', 'package.json')
    if (!fs.existsSync(frontendPackage)) {
      throw new Error('前端package.json不存在')
    }
    
    const pkg = JSON.parse(fs.readFileSync(frontendPackage, 'utf8'))
    
    // 添加插件依赖
    const newDependencies = {
      'rbush': '^3.0.1',
      'idb': '^7.1.1',
      '@tensorflow/tfjs': '^4.0.0'
    }
    
    pkg.dependencies = { ...pkg.dependencies, ...newDependencies }
    
    // 备份原文件
    fs.copyFileSync(frontendPackage, frontendPackage + '.backup')
    
    // 写入新配置
    fs.writeFileSync(frontendPackage, JSON.stringify(pkg, null, 2))
    
    console.log('✅ 前端依赖配置完成')
  }

  async installBackendDependencies() {
    console.log('📦 安装后端依赖...')
    
    const requirementsFile = path.join(this.projectRoot, 'backend', 'requirements.txt')
    
    const newRequirements = [
      'torch>=1.9.0',
      'numpy>=1.21.0',
      'redis>=4.0.0',
      'scikit-learn>=1.0.0'
    ]
    
    if (fs.existsSync(requirementsFile)) {
      // 备份原文件
      fs.copyFileSync(requirementsFile, requirementsFile + '.backup')
      
      // 读取现有依赖
      const existingRequirements = fs.readFileSync(requirementsFile, 'utf8')
      
      // 添加新依赖
      const updatedRequirements = existingRequirements + '\n' + newRequirements.join('\n')
      
      fs.writeFileSync(requirementsFile, updatedRequirements)
    } else {
      // 创建新文件
      fs.writeFileSync(requirementsFile, newRequirements.join('\n'))
    }
    
    console.log('✅ 后端依赖配置完成')
  }

  async modifyFrontendConfig() {
    console.log('🔧 修改前端配置...')
    
    // 修改main.js
    const mainJs = path.join(this.projectRoot, 'frontend', 'src', 'main.js')
    if (fs.existsSync(mainJs)) {
      let content = fs.readFileSync(mainJs, 'utf8')
      
      // 检查是否已经添加过插件
      if (!content.includes('IntelligentCachePlugin')) {
        // 备份原文件
        fs.copyFileSync(mainJs, mainJs + '.backup')
        
        // 添加插件导入和注册
        const importStatement = `import IntelligentCachePlugin from '../../../plugins/intelligent-cache/frontend/index.js'\n`
        const useStatement = `app.use(IntelligentCachePlugin, {\n  enabled: true,\n  config: {\n    debug: { enabled: true }\n  }\n})\n`
        
        // 在createApp之后添加
        content = content.replace(
          /const app = createApp\(App\)/,
          `const app = createApp(App)\n\n// 智能缓存插件\n${importStatement}\n${useStatement}`
        )
        
        fs.writeFileSync(mainJs, content)
        console.log('✅ 前端主文件配置完成')
      } else {
        console.log('⚠️  插件已存在于前端配置中')
      }
    }
  }

  async modifyBackendConfig() {
    console.log('🔧 修改后端配置...')
    
    // 修改app.py
    const appPy = path.join(this.projectRoot, 'backend', 'app.py')
    if (fs.existsSync(appPy)) {
      let content = fs.readFileSync(appPy, 'utf8')
      
      // 检查是否已经添加过插件
      if (!content.includes('intelligent_cache')) {
        // 备份原文件
        fs.copyFileSync(appPy, appPy + '.backup')
        
        // 添加插件导入和注册
        const importStatement = `\n# 智能缓存插件\nsys.path.append('../plugins/intelligent-cache/backend')\nfrom index import register_intelligent_cache_routes\n`
        const registerStatement = `\n# 注册智能缓存路由\nregister_intelligent_cache_routes(app)\n`
        
        // 在import部分添加
        content = content.replace(
          /(import.*\n)+/,
          `$&${importStatement}`
        )
        
        // 在app创建后添加
        content = content.replace(
          /app = Flask\(__name__\)/,
          `app = Flask(__name__)${registerStatement}`
        )
        
        fs.writeFileSync(appPy, content)
        console.log('✅ 后端主文件配置完成')
      } else {
        console.log('⚠️  插件已存在于后端配置中')
      }
    }
  }

  async createDatabaseTables() {
    console.log('🗄️  创建数据库表...')
    
    // 这里可以添加数据库表创建逻辑
    // 如果使用PostgreSQL，可以执行SQL脚本
    // 如果使用SQLite，可以创建表结构
    
    const sqlScript = `
-- 用户行为表
CREATE TABLE IF NOT EXISTS user_behaviors (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100),
    action VARCHAR(50),
    layer VARCHAR(100),
    zoom_level INTEGER,
    x_coord INTEGER,
    y_coord INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- 缓存元数据表
CREATE TABLE IF NOT EXISTS cache_metadata (
    id SERIAL PRIMARY KEY,
    tile_id VARCHAR(200) UNIQUE,
    layer VARCHAR(100),
    zoom_level INTEGER,
    x_coord INTEGER,
    y_coord INTEGER,
    size_bytes INTEGER,
    importance_score FLOAT,
    access_count INTEGER DEFAULT 1,
    last_access TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 预测结果表
CREATE TABLE IF NOT EXISTS prediction_results (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100),
    predicted_tiles JSONB,
    actual_tiles JSONB,
    accuracy_score FLOAT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_user_behaviors_user_id ON user_behaviors(user_id);
CREATE INDEX IF NOT EXISTS idx_user_behaviors_timestamp ON user_behaviors(timestamp);
CREATE INDEX IF NOT EXISTS idx_cache_metadata_tile_id ON cache_metadata(tile_id);
CREATE INDEX IF NOT EXISTS idx_cache_metadata_layer ON cache_metadata(layer);
CREATE INDEX IF NOT EXISTS idx_prediction_results_user_id ON prediction_results(user_id);
`
    
    // 保存SQL脚本
    const sqlFile = path.join(this.pluginRoot, 'database', 'install.sql')
    fs.mkdirSync(path.dirname(sqlFile), { recursive: true })
    fs.writeFileSync(sqlFile, sqlScript)
    
    console.log('✅ 数据库脚本已生成: plugins/intelligent-cache/database/install.sql')
    console.log('⚠️  请手动执行SQL脚本创建数据库表')
  }

  async copyModelFiles() {
    console.log('📁 复制模型文件...')
    
    const modelsDir = path.join(this.pluginRoot, 'models')
    if (!fs.existsSync(modelsDir)) {
      fs.mkdirSync(modelsDir, { recursive: true })
    }
    
    // 创建模型占位文件
    const modelPlaceholder = {
      name: 'behavior_predictor',
      version: '1.0.0',
      type: 'tensorflow_js',
      description: 'User behavior prediction model for intelligent caching',
      input_shape: [20],
      output_shape: [10],
      training_data: 'User interaction logs from WebGIS applications'
    }
    
    fs.writeFileSync(
      path.join(modelsDir, 'behavior_predictor.json'),
      JSON.stringify(modelPlaceholder, null, 2)
    )
    
    console.log('✅ 模型文件已创建')
  }

  async rollback() {
    console.log('🔄 回滚安装更改...')
    
    try {
      // 恢复备份文件
      const backupFiles = [
        path.join(this.projectRoot, 'frontend', 'package.json.backup'),
        path.join(this.projectRoot, 'backend', 'requirements.txt.backup'),
        path.join(this.projectRoot, 'frontend', 'src', 'main.js.backup'),
        path.join(this.projectRoot, 'backend', 'app.py.backup')
      ]
      
      for (const backupFile of backupFiles) {
        if (fs.existsSync(backupFile)) {
          const originalFile = backupFile.replace('.backup', '')
          fs.copyFileSync(backupFile, originalFile)
          fs.unlinkSync(backupFile)
        }
      }
      
      console.log('✅ 回滚完成')
    } catch (error) {
      console.error('❌ 回滚失败:', error.message)
    }
  }
}

// 执行安装
if (require.main === module) {
  const installer = new PluginInstaller()
  installer.install()
}

module.exports = PluginInstaller 