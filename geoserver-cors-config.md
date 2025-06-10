<!--
 * @Author: WangNing
 * @Date: 2025-06-10 10:16:59
 * @LastEditors: WangNing
 * @LastEditTime: 2025-06-10 10:18:24
 * @FilePath: \shpservice\geoserver-cors-config.md
 * @Description: 
 * Copyright (c) 2025 by VGE, All Rights Reserved. 
-->
# GeoServer CORS 配置指南

## 方法一：修改 web.xml 文件

1. 找到GeoServer的 `web.xml` 文件：
   - Windows: `{GEOSERVER_HOME}/webapps/geoserver/WEB-INF/web.xml`
   - 或者 `{TOMCAT_HOME}/webapps/geoserver/WEB-INF/web.xml`

2. 在 `web.xml` 文件中添加CORS过滤器：

```xml
<!-- 在 <web-app> 标签内添加以下内容 -->

<!-- CORS Filter -->
<filter>
    <filter-name>CorsFilter</filter-name>
    <filter-class>org.apache.catalina.filters.CorsFilter</filter-class>
    <init-param>
        <param-name>cors.allowed.origins</param-name>
        <param-value>*</param-value>
    </init-param>
    <init-param>
        <param-name>cors.allowed.methods</param-name>
        <param-value>GET,POST,HEAD,OPTIONS,PUT,DELETE</param-value>
    </init-param>
    <init-param>
        <param-name>cors.allowed.headers</param-name>
        <param-value>Content-Type,X-Requested-With,accept,Origin,Access-Control-Request-Method,Access-Control-Request-Headers,Authorization</param-value>
    </init-param>
    <init-param>
        <param-name>cors.exposed.headers</param-name>
        <param-value>Access-Control-Allow-Origin,Access-Control-Allow-Credentials</param-value>
    </init-param>
    <init-param>
        <param-name>cors.support.credentials</param-name>
        <param-value>true</param-value>
    </init-param>
</filter>

<filter-mapping>
    <filter-name>CorsFilter</filter-name>
    <url-pattern>/rest/*</url-pattern>
</filter-mapping>
```

3. 重启GeoServer服务

## 方法二：使用HTTP服务器

如果无法修改GeoServer配置，可以通过HTTP服务器运行HTML文件：

```bash
# 使用Python启动HTTP服务器
cd /path/to/your/html/file
python -m http.server 8080

# 然后访问: http://localhost:8080/geoserver-api-test.html
```

## 方法三：使用代理

创建一个简单的代理服务器来转发请求到GeoServer。 