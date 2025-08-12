/**
 * 前端加密工具类
 * 用于保护服务连接中的敏感信息
 * 支持RSA公钥加密敏感数据后发送给后端
 */

import { ElMessage } from 'element-plus'

class FrontendEncryption {
  constructor() {
    this.publicKey = null
    this.isInitialized = false
    // 需要加密的敏感字段
    this.sensitiveFields = new Set([
      'password',
      'api_key',
      'file_service_password'
    ])
  }

  /**
   * 初始化加密服务，获取服务器公钥
   */
  async initialize() {
    if (this.isInitialized && this.publicKey) {
      return true
    }

    try {
      const response = await fetch('/api/service-connections/encryption/public-key')
      const result = await response.json()
      
      if (result.success && result.data.public_key) {
        this.publicKey = result.data.public_key
        this.isInitialized = true
        console.log('🔒 前端加密服务初始化成功')
        return true
      } else {
        console.error('❌ 获取公钥失败:', result.error)
        return false
      }
    } catch (error) {
      console.error('❌ 初始化加密服务失败:', error)
      return false
    }
  }

  /**
   * 使用RSA公钥加密文本
   * 注意：这里我们使用Web Crypto API进行RSA加密
   */
  async rsaEncrypt(text) {
    if (!text || !this.publicKey) {
      return null
    }

    try {
      // 将PEM格式的公钥转换为ArrayBuffer
      const publicKeyData = this.pemToArrayBuffer(this.publicKey)
      
      // 导入公钥
      const cryptoKey = await window.crypto.subtle.importKey(
        'spki',
        publicKeyData,
        {
          name: 'RSA-OAEP',
          hash: 'SHA-256'
        },
        false,
        ['encrypt']
      )

      // 加密数据
      const encoder = new TextEncoder()
      const data = encoder.encode(text)
      const encrypted = await window.crypto.subtle.encrypt(
        {
          name: 'RSA-OAEP'
        },
        cryptoKey,
        data
      )

      // 转换为base64
      return this.arrayBufferToBase64(encrypted)
    } catch (error) {
      console.error('❌ RSA加密失败:', error)
      return null
    }
  }

  /**
   * 将PEM格式的公钥转换为ArrayBuffer
   */
  pemToArrayBuffer(pem) {
    const base64 = pem
      .replace(/-----BEGIN PUBLIC KEY-----/g, '')
      .replace(/-----END PUBLIC KEY-----/g, '')
      .replace(/\r\n/g, '')
      .replace(/\n/g, '')
      .replace(/\s/g, '')
    
    return this.base64ToArrayBuffer(base64)
  }

  /**
   * Base64字符串转ArrayBuffer
   */
  base64ToArrayBuffer(base64) {
    const binaryString = window.atob(base64)
    const bytes = new Uint8Array(binaryString.length)
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i)
    }
    return bytes.buffer
  }

  /**
   * ArrayBuffer转Base64字符串
   */
  arrayBufferToBase64(buffer) {
    const bytes = new Uint8Array(buffer)
    let binary = ''
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i])
    }
    return window.btoa(binary)
  }

  /**
   * 加密表单数据中的敏感字段
   */
  async encryptFormData(formData) {
    // 确保加密服务已初始化
    if (!this.isInitialized) {
      const initialized = await this.initialize()
      if (!initialized) {
        console.warn('⚠️ 加密服务未初始化，使用明文传输')
        return formData
      }
    }

    const encryptedData = { ...formData }

    // 加密敏感字段
    for (const field of this.sensitiveFields) {
      if (encryptedData[field] && encryptedData[field].trim()) {
        try {
          const encrypted = await this.rsaEncrypt(encryptedData[field])
          if (encrypted) {
            encryptedData[field] = encrypted
            // 添加加密标记
            encryptedData[`${field}_rsa_encrypted`] = true
            console.log(`🔒 字段 ${field} 已加密`)
          }
        } catch (error) {
          console.error(`❌ 加密字段 ${field} 失败:`, error)
          // 如果加密失败，可以选择使用明文或终止操作
          ElMessage.warning(`敏感字段 ${field} 加密失败，将使用明文传输`)
        }
      }
    }

    return encryptedData
  }

  /**
   * 生成随机字符串（用于某些场景的安全性增强）
   */
  generateRandomString(length = 16) {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    let result = ''
    for (let i = 0; i < length; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length))
    }
    return result
  }

  /**
   * 检查浏览器是否支持Web Crypto API
   */
  isCryptoSupported() {
    return !!(window.crypto && window.crypto.subtle)
  }

  /**
   * 简单的字符串混淆（不是真正的加密，仅用于前端临时存储）
   */
  obfuscateString(str) {
    if (!str) return str
    
    // 简单的Base64编码（注意：这不是安全的加密）
    return btoa(encodeURIComponent(str))
  }

  /**
   * 解混淆字符串
   */
  deobfuscateString(obfuscated) {
    if (!obfuscated) return obfuscated
    
    try {
      return decodeURIComponent(atob(obfuscated))
    } catch (error) {
      console.error('解混淆失败:', error)
      return obfuscated
    }
  }

  /**
   * 遮蔽敏感信息显示
   */
  maskSensitiveValue(value, showLength = 4) {
    if (!value) return value
    
    const str = String(value)
    if (str.length <= showLength) {
      return '*'.repeat(str.length)
    }
    
    const visibleLength = Math.floor(showLength / 2)
    const start = str.substring(0, visibleLength)
    const end = str.substring(str.length - visibleLength)
    const masked = '*'.repeat(str.length - showLength)
    
    return start + masked + end
  }
}

// 创建全局实例
const frontendEncryption = new FrontendEncryption()

// 检查浏览器兼容性
if (!frontendEncryption.isCryptoSupported()) {
  console.warn('⚠️ 当前浏览器不支持Web Crypto API，某些加密功能可能无法使用')
  ElMessage.warning('当前浏览器不支持加密功能，建议使用现代浏览器以获得更好的安全性')
}

export default frontendEncryption