/**
 * 智能缓存插件卸载脚本
 */

const fs = require('fs')
const path = require('path')

class PluginUninstaller {
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
        if (!packageJson.plugin) {
          return currentDir
        }
      }
      currentDir = path.dirname(currentDir)
    }
    throw new Error('无法找到项目根目录')
  }

  async uninstall() {
    console.log('🗑️  开始卸载智能缓存插件...')
    
    try {
      // 1. 确认卸载
      await this.confirmUninstall()
      
      // 2. 清理前端配置
      await this.cleanupFrontendConfig()
      
      // 3. 清理后端配置
      await this.cleanupBackendConfig()
      
      // 4. 移除依赖
      await this.removeDependencies()
      
      // 5. 清理数据库（可选）
      await this.cleanupDatabase()
      
      // 6. 删除插件文件
      await this.removePluginFiles()
      
      console.log('✅ 智能缓存插件卸载成功！')
      console.log('')
      console.log('📋 后续步骤：')
      console.log('1. 重启前端开发服务器')
      console.log('2. 重启后端服务器')
      console.log('3. 运行 npm install 更新前端依赖')
      console.log('4. 运行 pip install -r requirements.txt 更新后端依赖')
      
    } catch (error) {
      console.error('❌ 插件卸载失败:', error.message)
      process.exit(1)
    }
  }

  async confirmUninstall() {
    // 在实际应用中，这里可以添加交互式确认
    console.log('⚠️  即将卸载智能缓存插件')
    console.log('⚠️  这将删除所有缓存数据和配置')
    
    // 简单确认（在实际应用中可以使用inquirer等库）
    const confirmFile = path.join(this.pluginRoot, 'CONFIRM_UNINSTALL')
    if (!fs.existsSync(confirmFile)) {
      console.log('💡 如需确认卸载，请创建文件: plugins/intelligent-cache/CONFIRM_UNINSTALL')
      throw new Error('卸载已取消')
    }
    
    // 删除确认文件
    fs.unlinkSync(confirmFile)
    console.log('✅ 卸载确认完成')
  }

  async cleanupFrontendConfig() {
    console.log('🧹 清理前端配置...')
    
    // 清理main.js
    const mainJs = path.join(this.projectRoot, 'frontend', 'src', 'main.js')
    if (fs.existsSync(mainJs)) {
      let content = fs.readFileSync(mainJs, 'utf8')
      
      // 检查是否包含插件代码
      if (content.includes('IntelligentCachePlugin')) {
        // 备份原文件
        fs.copyFileSync(mainJs, mainJs + '.uninstall_backup')
        
        // 移除插件相关代码
        content = content.replace(
          /import IntelligentCachePlugin.*\n/g,
          ''
        )
        content = content.replace(
          /\/\/ 智能缓存插件[\s\S]*?app\.use\(IntelligentCachePlugin[\s\S]*?\)\n/g,
          ''
        )
        
        // 清理空行
        content = content.replace(/\n\s*\n\s*\n/g, '\n\n')
        
        fs.writeFileSync(mainJs, content)
        console.log('✅ 前端配置清理完成')
      } else {
        console.log('ℹ️  前端配置中未找到插件代码')
      }
    }
  }

  async cleanupBackendConfig() {
    console.log('🧹 清理后端配置...')
    
    // 清理app.py
    const appPy = path.join(this.projectRoot, 'backend', 'app.py')
    if (fs.existsSync(appPy)) {
      let content = fs.readFileSync(appPy, 'utf8')
      
      // 检查是否包含插件代码
      if (content.includes('intelligent_cache')) {
        // 备份原文件
        fs.copyFileSync(appPy, appPy + '.uninstall_backup')
        
        // 移除插件相关代码
        content = content.replace(
          /# 智能缓存插件[\s\S]*?from index import register_intelligent_cache_routes\n/g,
          ''
        )
        content = content.replace(
          /# 注册智能缓存路由[\s\S]*?register_intelligent_cache_routes\(app\)\n/g,
          ''
        )
        
        // 清理空行
        content = content.replace(/\n\s*\n\s*\n/g, '\n\n')
        
        fs.writeFileSync(appPy, content)
        console.log('✅ 后端配置清理完成')
      } else {
        console.log('ℹ️  后端配置中未找到插件代码')
      }
    }
  }

  async removeDependencies() {
    console.log('📦 移除依赖...')
    
    // 移除前端依赖
    const frontendPackage = path.join(this.projectRoot, 'frontend', 'package.json')
    if (fs.existsSync(frontendPackage)) {
      const pkg = JSON.parse(fs.readFileSync(frontendPackage, 'utf8'))
      
      // 移除插件依赖
      const dependenciesToRemove = ['rbush', 'idb', '@tensorflow/tfjs']
      let hasChanges = false
      
      for (const dep of dependenciesToRemove) {
        if (pkg.dependencies && pkg.dependencies[dep]) {
          delete pkg.dependencies[dep]
          hasChanges = true
        }
      }
      
      if (hasChanges) {
        // 备份原文件
        fs.copyFileSync(frontendPackage, frontendPackage + '.uninstall_backup')
        
        // 写入新配置
        fs.writeFileSync(frontendPackage, JSON.stringify(pkg, null, 2))
        console.log('✅ 前端依赖移除完成')
      } else {
        console.log('ℹ️  前端依赖中未找到插件相关包')
      }
    }
    
    // 移除后端依赖
    const requirementsFile = path.join(this.projectRoot, 'backend', 'requirements.txt')
    if (fs.existsSync(requirementsFile)) {
      let content = fs.readFileSync(requirementsFile, 'utf8')
      
      // 移除插件依赖
      const dependenciesToRemove = [
        'torch>=1.9.0',
        'numpy>=1.21.0', 
        'redis>=4.0.0',
        'scikit-learn>=1.0.0'
      ]
      
      let hasChanges = false
      for (const dep of dependenciesToRemove) {
        if (content.includes(dep)) {
          content = content.replace(new RegExp(`\\n?${dep.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\n?`, 'g'), '\n')
          hasChanges = true
        }
      }
      
      if (hasChanges) {
        // 备份原文件
        fs.copyFileSync(requirementsFile, requirementsFile + '.uninstall_backup')
        
        // 清理空行并写入
        content = content.replace(/\n\s*\n/g, '\n').trim()
        fs.writeFileSync(requirementsFile, content)
        console.log('✅ 后端依赖移除完成')
      } else {
        console.log('ℹ️  后端依赖中未找到插件相关包')
      }
    }
  }

  async cleanupDatabase() {
    console.log('🗄️  清理数据库（可选）...')
    
    // 生成清理SQL脚本
    const cleanupScript = `
-- 清理智能缓存插件相关数据表
-- 警告：这将删除所有用户行为数据和缓存元数据！

-- 删除表（如果需要保留数据，请注释掉以下语句）
-- DROP TABLE IF EXISTS user_behaviors;
-- DROP TABLE IF EXISTS cache_metadata;
-- DROP TABLE IF EXISTS prediction_results;

-- 或者只清空数据（保留表结构）
TRUNCATE TABLE user_behaviors;
TRUNCATE TABLE cache_metadata;
TRUNCATE TABLE prediction_results;

-- 重置序列（PostgreSQL）
-- ALTER SEQUENCE user_behaviors_id_seq RESTART WITH 1;
-- ALTER SEQUENCE cache_metadata_id_seq RESTART WITH 1;
-- ALTER SEQUENCE prediction_results_id_seq RESTART WITH 1;
`
    
    // 保存清理脚本
    const cleanupFile = path.join(this.pluginRoot, 'database', 'cleanup.sql')
    if (fs.existsSync(path.dirname(cleanupFile))) {
      fs.writeFileSync(cleanupFile, cleanupScript)
      console.log('✅ 数据库清理脚本已生成: plugins/intelligent-cache/database/cleanup.sql')
      console.log('⚠️  请根据需要手动执行SQL脚本清理数据库')
    } else {
      console.log('ℹ️  未找到数据库目录，跳过数据库清理')
    }
  }

  async removePluginFiles() {
    console.log('📁 删除插件文件...')
    
    // 创建删除确认文件
    const deleteConfirmFile = path.join(this.pluginRoot, 'DELETE_PLUGIN_FILES')
    if (!fs.existsSync(deleteConfirmFile)) {
      console.log('⚠️  插件文件保留在: ' + this.pluginRoot)
      console.log('💡 如需完全删除，请创建文件: plugins/intelligent-cache/DELETE_PLUGIN_FILES')
      console.log('💡 然后重新运行卸载脚本')
      return
    }
    
    try {
      // 递归删除插件目录
      this.removeDirectory(this.pluginRoot)
      console.log('✅ 插件文件删除完成')
    } catch (error) {
      console.error('❌ 删除插件文件失败:', error.message)
      console.log('💡 请手动删除目录: ' + this.pluginRoot)
    }
  }

  removeDirectory(dirPath) {
    if (fs.existsSync(dirPath)) {
      const files = fs.readdirSync(dirPath)
      
      for (const file of files) {
        const filePath = path.join(dirPath, file)
        const stat = fs.statSync(filePath)
        
        if (stat.isDirectory()) {
          this.removeDirectory(filePath)
        } else {
          fs.unlinkSync(filePath)
        }
      }
      
      fs.rmdirSync(dirPath)
    }
  }

  // 静态方法：快速卸载（用于开发测试）
  static async quickUninstall() {
    console.log('⚡ 快速卸载模式（开发测试用）')
    
    const uninstaller = new PluginUninstaller()
    
    // 创建确认文件
    const confirmFile = path.join(uninstaller.pluginRoot, 'CONFIRM_UNINSTALL')
    fs.writeFileSync(confirmFile, 'quick uninstall')
    
    // 创建删除文件确认
    const deleteFile = path.join(uninstaller.pluginRoot, 'DELETE_PLUGIN_FILES')
    fs.writeFileSync(deleteFile, 'delete all files')
    
    // 执行卸载
    await uninstaller.uninstall()
  }
}

// 执行卸载
if (require.main === module) {
  const args = process.argv.slice(2)
  
  if (args.includes('--quick')) {
    PluginUninstaller.quickUninstall()
  } else {
    const uninstaller = new PluginUninstaller()
    uninstaller.uninstall()
  }
}

module.exports = PluginUninstaller 