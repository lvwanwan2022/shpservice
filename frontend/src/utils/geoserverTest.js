/**
 * 前端Geoserver连接测试工具
 * 直接从浏览器测试Geoserver连接，无需通过后端
 */

/**
 * 测试Geoserver连接
 * @param {Object} config 连接配置
 * @param {string} config.server_url Geoserver服务地址
 * @param {string} config.username 用户名
 * @param {string} config.password 密码
 * @param {string} config.workspace 工作空间（可选）
 * @returns {Promise<{success: boolean, message: string, data?: Object}>}
 */
export async function testGeoserverConnection(config) {
  try {
    const { server_url, username, password, workspace } = config;
    
    if (!server_url || !username || !password) {
      return {
        success: false,
        message: '缺少必要的连接参数'
      };
    }
    
    // 标准化服务器URL
    let baseUrl = server_url.trim();
    if (!baseUrl.endsWith('/')) {
      baseUrl += '/';
    }
    
    // 构建基础认证头
    const credentials = btoa(`${username}:${password}`);
    const headers = {
      'Authorization': `Basic ${credentials}`,
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    };
    
    // 测试步骤1：检查Geoserver REST API是否可访问
    const restUrl = `${baseUrl}rest/about/version.json`;
    
    try {
      const versionResponse = await fetchWithTimeout(restUrl, {
        method: 'GET',
        headers,
        mode: 'cors'
      }, 10000);
      
      if (versionResponse.ok) {
        const versionData = await versionResponse.json();
        const geoserverVersion = versionData?.about?.resource?.find(r => r.name === 'GeoServer')?.Version || 'Unknown';
        
        // 测试步骤2：检查工作空间列表
        const workspacesUrl = `${baseUrl}rest/workspaces.json`;
        const workspacesResponse = await fetchWithTimeout(workspacesUrl, {
          method: 'GET',
          headers,
          mode: 'cors'
        }, 5000);
        
        if (workspacesResponse.ok) {
          const workspacesData = await workspacesResponse.json();
          const workspaces = workspacesData?.workspaces?.workspace || [];
          const workspaceCount = Array.isArray(workspaces) ? workspaces.length : 0;
          
          // 如果指定了工作空间，检查是否存在
          let workspaceExists = true;
          if (workspace && workspace !== 'default') {
            workspaceExists = workspaces.some(ws => ws.name === workspace);
          }
          
          return {
            success: true,
            message: `Geoserver连接成功 (v${geoserverVersion})，找到 ${workspaceCount} 个工作空间${!workspaceExists ? `，但指定的工作空间 "${workspace}" 不存在` : ''}`,
            data: {
              version: geoserverVersion,
              workspaceCount,
              workspaces: workspaces.map(ws => ws.name),
              workspaceExists,
              testMethod: 'frontend'
            }
          };
        } else if (workspacesResponse.status === 401) {
          return {
            success: false,
            message: '认证失败，请检查用户名和密码'
          };
        } else {
          return {
            success: false,
            message: `无法访问工作空间列表，HTTP状态码: ${workspacesResponse.status}`
          };
        }
      } else if (versionResponse.status === 401) {
        return {
          success: false,
          message: '认证失败，请检查用户名和密码'
        };
      } else {
        return {
          success: false,
          message: `无法访问Geoserver REST API，HTTP状态码: ${versionResponse.status}`
        };
      }
    } catch (corsError) {
      // 如果遇到CORS错误，尝试通过代理访问
      console.warn('直接访问遇到CORS问题，尝试通过代理访问:', corsError.message);
      return await testGeoserverViaProxy(config);
    }
    
  } catch (error) {
    console.error('Geoserver连接测试失败:', error);
    
    if (error.name === 'TypeError' && error.message.includes('CORS')) {
      return {
        success: false,
        message: '跨域访问被阻止，建议配置Geoserver的CORS策略或使用后端代理'
      };
    } else if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
      return {
        success: false,
        message: '网络连接失败，请检查Geoserver地址和网络连接'
      };
    } else if (error.message === 'timeout') {
      return {
        success: false,
        message: '连接超时，请检查Geoserver服务是否正常运行'
      };
    } else {
      return {
        success: false,
        message: `连接测试失败: ${error.message}`
      };
    }
  }
}

/**
 * 通过代理测试Geoserver连接（备用方案）
 * @param {Object} config 连接配置
 * @returns {Promise<{success: boolean, message: string, data?: Object}>}
 */
async function testGeoserverViaProxy(config) {
  try {
    // 如果是本地开发环境的Geoserver，可以尝试通过Vue代理访问
    const { server_url, username, password } = config;
    
    // 检查是否是本地Geoserver（可以通过代理访问）
    if (server_url.includes('localhost') || server_url.includes('127.0.0.1') || 
        server_url.includes(window.location.hostname)) {
      
      const credentials = btoa(`${username}:${password}`);
      const headers = {
        'Authorization': `Basic ${credentials}`,
        'Accept': 'application/json'
      };
      
      // 通过Vue代理访问
      const proxyUrl = '/geoserver/rest/about/version.json';
      const response = await fetchWithTimeout(proxyUrl, {
        method: 'GET',
        headers
      }, 5000);
      
      if (response.ok) {
        const data = await response.json();
        const version = data?.about?.resource?.find(r => r.name === 'GeoServer')?.Version || 'Unknown';
        
        return {
          success: true,
          message: `Geoserver连接成功 (v${version})，通过代理访问`,
          data: {
            version,
            testMethod: 'proxy'
          }
        };
      } else if (response.status === 401) {
        return {
          success: false,
          message: '认证失败，请检查用户名和密码'
        };
      } else {
        return {
          success: false,
          message: `代理访问失败，HTTP状态码: ${response.status}`
        };
      }
    } else {
      return {
        success: false,
        message: '无法直接访问远程Geoserver，建议在Geoserver中配置CORS或使用后端代理测试'
      };
    }
  } catch (error) {
    return {
      success: false,
      message: `代理测试失败: ${error.message}`
    };
  }
}

/**
 * 带超时的fetch请求
 * @param {string} url 请求URL
 * @param {Object} options fetch选项
 * @param {number} timeout 超时时间（毫秒）
 * @returns {Promise<Response>}
 */
function fetchWithTimeout(url, options = {}, timeout = 5000) {
  return new Promise((resolve, reject) => {
    const timeoutId = setTimeout(() => {
      reject(new Error('timeout'));
    }, timeout);
    
    fetch(url, options)
      .then(response => {
        clearTimeout(timeoutId);
        resolve(response);
      })
      .catch(error => {
        clearTimeout(timeoutId);
        reject(error);
      });
  });
}

/**
 * 测试Martin连接
 * @param {Object} config Martin连接配置
 * @param {string} config.server_url Martin服务地址
 * @param {string} config.api_key API密钥（可选）
 * @returns {Promise<{success: boolean, message: string, data?: Object}>}
 */
export async function testMartinConnection(config) {
  try {
    const { server_url, api_key } = config;
    
    if (!server_url) {
      return {
        success: false,
        message: '缺少服务器地址'
      };
    }
    
    let baseUrl = server_url.trim();
    if (!baseUrl.endsWith('/')) {
      baseUrl += '/';
    }
    
    const headers = {
      'Accept': 'application/json'
    };
    
    if (api_key) {
      headers['Authorization'] = `Bearer ${api_key}`;
    }
    
    // 尝试健康检查端点
    try {
      const healthUrl = `${baseUrl}health`;
      const healthResponse = await fetchWithTimeout(healthUrl, {
        method: 'GET',
        headers,
        mode: 'cors'
      }, 5000);
      
      if (healthResponse.ok) {
        const healthData = await healthResponse.json();
        return {
          success: true,
          message: 'Martin服务连接成功',
          data: {
            ...healthData,
            testMethod: 'frontend'
          }
        };
      }
    } catch (healthError) {
      console.warn('Health检查失败，尝试catalog端点:', healthError.message);
    }
    
    // 尝试目录端点
    const catalogUrl = `${baseUrl}catalog`;
    const catalogResponse = await fetchWithTimeout(catalogUrl, {
      method: 'GET',
      headers,
      mode: 'cors'
    }, 10000);
    
    if (catalogResponse.ok) {
      const catalogData = await catalogResponse.json();
      const tableCount = Array.isArray(catalogData) ? catalogData.length : 
                        (catalogData && typeof catalogData === 'object') ? Object.keys(catalogData).length : 0;
      
      return {
        success: true,
        message: `Martin服务连接成功，发现 ${tableCount} 个数据源`,
        data: {
          tableCount,
          tables: Array.isArray(catalogData) ? catalogData.slice(0, 5) : [],
          testMethod: 'frontend'
        }
      };
    } else if (catalogResponse.status === 401) {
      return {
        success: false,
        message: '认证失败，请检查API密钥'
      };
    } else {
      return {
        success: false,
        message: `连接失败，HTTP状态码: ${catalogResponse.status}`
      };
    }
    
  } catch (error) {
    console.error('Martin连接测试失败:', error);
    
    if (error.name === 'TypeError' && error.message.includes('CORS')) {
      return {
        success: false,
        message: '跨域访问被阻止，建议配置Martin服务的CORS策略'
      };
    } else if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
      return {
        success: false,
        message: '网络连接失败，请检查Martin服务地址和网络连接'
      };
    } else if (error.message === 'timeout') {
      return {
        success: false,
        message: '连接超时，请检查Martin服务是否正常运行'
      };
    } else {
      return {
        success: false,
        message: `连接测试失败: ${error.message}`
      };
    }
  }
}

/**
 * 通用的服务连接测试
 * @param {Object} config 连接配置
 * @param {string} config.service_type 服务类型：'geoserver' 或 'martin'
 * @param {boolean} useFrontend 是否使用前端直接测试
 * @returns {Promise<{success: boolean, message: string, data?: Object}>}
 */
export async function testServiceConnection(config, useFrontend = true) {
  if (!useFrontend) {
    throw new Error('后端测试功能未在此工具中实现，请使用原有的API调用');
  }
  
  const { service_type } = config;
  
  switch (service_type) {
    case 'geoserver':
      return await testGeoserverConnection(config);
    case 'martin':
      return await testMartinConnection(config);
    default:
      return {
        success: false,
        message: `不支持的服务类型: ${service_type}`
      };
  }
}