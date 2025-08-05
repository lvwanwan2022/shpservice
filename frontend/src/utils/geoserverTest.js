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
    
    // 检查是否需要特殊处理（远程服务器或不同端口）
    const currentOrigin = window.location.origin; // 例如: http://10.20.186.58:8080
    const isLocalhost = server_url.includes('localhost') || server_url.includes('127.0.0.1');
    const isSameOrigin = server_url.startsWith(currentOrigin);
    
    // 对于非本地且非同源的服务器，提供新窗口测试选项
    const needsAlternativeTest = !isLocalhost && !isSameOrigin;
    
    console.log(`🔍 连接测试检查:`, {
      server_url,
      currentOrigin,
      isLocalhost,
      isSameOrigin,
      needsAlternativeTest
    });
    
    if (needsAlternativeTest) {
      console.warn('检测到需要特殊处理的GeoServer，提供新窗口测试选项');
      // 提供新窗口测试作为替代方案
      return {
        success: false,
        message: '检测到远程GeoServer服务，前端直接测试受CORS限制',
        data: {
          suggestion: '建议使用"后端测试"或"新窗口测试"',
          technical: '远程服务器的CORS策略阻止了直接访问',
          isRemoteServer: true,
          showWindowTest: true,
          server_url: server_url,
          username: username,
          password: password
        }
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
      
      // 先尝试代理方式
      const proxyResult = await testGeoserverViaProxy(config);
      
      // 如果代理也失败，返回友好的错误信息
      if (!proxyResult.success) {
        return {
          success: false,
          message: '前端测试受跨域限制无法完成',
          data: {
            suggestion: '建议使用"后端测试"按钮，后端测试不受浏览器CORS限制',
            technical: '前端直接访问远程GeoServer被浏览器安全策略阻止',
            originalError: corsError.message,
            proxyError: proxyResult.message
          }
        };
      }
      
      return proxyResult;
    }
    
  } catch (error) {
    console.error('Geoserver连接测试失败:', error);
    
    if (error.name === 'TypeError' && error.message.includes('CORS')) {
      return {
        success: false,
        message: '跨域访问被阻止，请使用"后端测试"或配置GeoServer的CORS策略',
        data: {
          suggestion: '建议使用"后端测试"按钮进行连接测试',
          technical: 'CORS错误通常发生在浏览器直接访问远程服务时'
        }
      };
    } else if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
      return {
        success: false,
        message: '网络连接失败，请检查GeoServer地址和网络连接',
        data: {
          suggestion: '请确认GeoServer地址正确且服务正在运行'
        }
      };
    } else if (error.message === 'timeout') {
      return {
        success: false,
        message: '连接超时，请检查GeoServer服务是否正常运行',
        data: {
          suggestion: '请检查GeoServer服务状态或尝试后端测试'
        }
      };
    } else {
      return {
        success: false,
        message: `连接测试失败: ${error.message}`,
        data: {
          suggestion: '如果问题持续，请尝试使用后端测试'
        }
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
    
    // 检查是否可以通过代理访问（包含本地或配置的GeoServer地址）
    const canUseProxy = server_url.includes('localhost') || 
                       server_url.includes('127.0.0.1') || 
                       server_url.includes(window.location.hostname) ||
                       server_url.includes('10.20.186.58'); // 添加配置的GeoServer地址
    
    if (canUseProxy) {
      
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
        message: '无法通过代理访问该GeoServer地址，请使用后端测试或检查GeoServer配置',
        data: {
          suggestion: '请尝试使用"后端测试"按钮，或确保GeoServer地址正确'
        }
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
 * 新窗口测试GeoServer连接
 * @param {Object} config 连接配置
 * @returns {Promise<{success: boolean, message: string, data?: Object}>}
 */
export async function testGeoserverInNewWindow(config) {
  const { server_url, username, password } = config;
  
  return new Promise((resolve) => {
    try {
      // 构建GeoServer Web界面URL
      let geoserverUrl = server_url;
      if (!geoserverUrl.endsWith('/')) {
        geoserverUrl += '/';
      }
      
      // 添加web界面路径
      if (!geoserverUrl.includes('/web')) {
        geoserverUrl += 'web/';
      }
      
      console.log(`🔍 新窗口测试URL: ${geoserverUrl}`);
      
      // 创建测试指导页面的HTML内容
      const testPageHTML = `
        <!DOCTYPE html>
        <html>
        <head>
          <title>GeoServer连接测试</title>
          <meta charset="utf-8">
          <style>
            body { font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }
            .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .header { text-align: center; margin-bottom: 30px; }
            .icon { font-size: 48px; margin-bottom: 10px; }
            .title { color: #2c3e50; margin: 0; }
            .subtitle { color: #7f8c8d; margin: 10px 0 0 0; }
            .credentials { background: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0; }
            .btn { background: #3498db; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; margin: 10px 5px; text-decoration: none; display: inline-block; }
            .btn:hover { background: #2980b9; }
            .btn-success { background: #27ae60; }
            .btn-success:hover { background: #229954; }
            .btn-danger { background: #e74c3c; }
            .btn-danger:hover { background: #c0392b; }
            .instructions { margin: 20px 0; line-height: 1.6; }
            .step { margin: 10px 0; padding: 10px; background: #f8f9fa; border-left: 4px solid #3498db; }
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <div class="icon">🌐</div>
              <h1 class="title">GeoServer连接测试</h1>
              <p class="subtitle">请按照以下步骤测试连接</p>
            </div>
            
            <div class="credentials">
              <h3>🔑 登录凭据</h3>
              <p><strong>用户名:</strong> ${username}</p>
              <p><strong>密码:</strong> ${password}</p>
            </div>
            
            <div class="instructions">
              <div class="step">
                <strong>步骤 1:</strong> 点击下方按钮访问GeoServer
              </div>
              <div class="step">
                <strong>步骤 2:</strong> 使用上方凭据登录
              </div>
              <div class="step">
                <strong>步骤 3:</strong> 如果能正常登录并看到管理界面，说明连接成功
              </div>
              <div class="step">
                <strong>步骤 4:</strong> 根据测试结果点击下方按钮
              </div>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
              <a href="${geoserverUrl}" target="_blank" class="btn">🚀 访问GeoServer</a>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
              <button onclick="reportSuccess()" class="btn btn-success">✅ 连接成功</button>
              <button onclick="reportFailure()" class="btn btn-danger">❌ 连接失败</button>
            </div>
          </div>
          
          <script>
            function reportSuccess() {
              if (window.opener) {
                window.opener.postMessage({
                  type: 'geoserver-test-result',
                  success: true,
                  message: '连接测试成功，可以正常访问GeoServer管理界面'
                }, '*');
              }
              window.close();
            }
            
            function reportFailure() {
              if (window.opener) {
                window.opener.postMessage({
                  type: 'geoserver-test-result',
                  success: false,
                  message: '连接测试失败，无法访问GeoServer或登录失败'
                }, '*');
              }
              window.close();
            }
            
            // 自动检测窗口关闭
            window.addEventListener('beforeunload', function() {
              if (window.opener && !window.testReported) {
                window.opener.postMessage({
                  type: 'geoserver-test-result',
                  success: false,
                  message: '测试窗口已关闭，未完成测试'
                }, '*');
              }
            });
          </script>
        </body>
        </html>
      `;
      
      // 打开新窗口
      const testWindow = window.open('', 'geoserver-test', 'width=700,height=600,scrollbars=yes,resizable=yes');
      
      if (!testWindow) {
        resolve({
          success: false,
          message: '无法打开测试窗口，请检查浏览器弹窗设置'
        });
        return;
      }
      
      // 写入测试页面内容
      testWindow.document.write(testPageHTML);
      testWindow.document.close();
      
      // 监听来自测试窗口的消息
      const messageHandler = (event) => {
        if (event.data && event.data.type === 'geoserver-test-result') {
          window.removeEventListener('message', messageHandler);
          testWindow.testReported = true;
          resolve({
            success: event.data.success,
            message: event.data.message,
            data: {
              testMethod: 'new-window',
              url: geoserverUrl
            }
          });
        }
      };
      
      window.addEventListener('message', messageHandler);
      
      // 设置超时（5分钟）
      setTimeout(() => {
        window.removeEventListener('message', messageHandler);
        if (testWindow && !testWindow.closed) {
          testWindow.close();
        }
        resolve({
          success: false,
          message: '测试超时，请重试'
        });
      }, 300000); // 5分钟超时
      
    } catch (error) {
      resolve({
        success: false,
        message: `新窗口测试失败: ${error.message}`
      });
    }
  });
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