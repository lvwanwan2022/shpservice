# GeoServer跨域问题解决方案

## 问题描述

在前端使用Leaflet加载GeoServer发布的WMS服务时，经常遇到跨域（CORS）问题，导致图层无法正常显示。

## 解决方案

### 方案一：GeoServer Windows安装版

#### 1. 修改web.xml配置文件

打开 `geoserver安装目录\webapps\geoserver\WEB-INF\web.xml` 文件，取消以下内容的注释：

```xml
<!-- Uncomment following filter to enable CORS -->
<filter>
    <filter-name>cross-origin</filter-name>
    <filter-class>org.eclipse.jetty.servlets.CrossOriginFilter</filter-class>
    <init-param>
        <param-name>chainPreflight</param-name>
        <param-value>false</param-value>
    </init-param>
    <init-param>
        <param-name>allowedOrigins</param-name>
        <param-value>*</param-value>
    </init-param>
    <init-param>
        <param-name>allowedMethods</param-name>
        <param-value>GET,POST,PUT,DELETE,HEAD,OPTIONS</param-value>
    </init-param>
    <init-param>
        <param-name>allowedHeaders</param-name>
        <param-value>*</param-value>
    </init-param>
</filter>

<!-- Uncomment following filter to enable CORS -->
<filter-mapping>
    <filter-name>cross-origin</filter-name>
    <url-pattern>/*</url-pattern>
</filter-mapping>
```

#### 2. 复制必要的JAR文件

从 `geoserver安装目录\lib` 目录复制以下文件到 `geoserver安装目录\webapps\geoserver\WEB-INF\lib`：

- `jetty-servlets-9.4.12.v20180830.jar`
- `jetty-util-9.4.12.v20180830.jar`

#### 3. 重启GeoServer服务

### 方案二：Tomcat部署的WAR包版本

#### 1. 修改web.xml配置文件

打开 `tomcat安装目录/webapps/geoserver/WEB-INF/web.xml` 文件，取消以下内容的注释：

```xml
<filter>
    <filter-name>cross-origin</filter-name>
    <filter-class>org.apache.catalina.filters.CorsFilter</filter-class>
    <init-param>
        <param-name>cors.allowed.origins</param-name>
        <param-value>*</param-value>
    </init-param>
    <init-param>
        <param-name>cors.allowed.methods</param-name>
        <param-value>GET,POST,PUT,DELETE,HEAD,OPTIONS</param-value>
    </init-param>
    <init-param>
        <param-name>cors.allowed.headers</param-name>
        <param-value>*</param-value>
    </init-param>
</filter>

<filter-mapping>
    <filter-name>cross-origin</filter-name>
    <url-pattern>/*</url-pattern>
</filter-mapping>
```

#### 2. 添加必要的JAR文件

下载并复制以下文件到 `tomcat安装目录/webapps/geoserver/WEB-INF/lib`：

- `cors-filter-1.7.jar`
- `java-property-utils-1.9.jar`

#### 3. 重启Tomcat服务

## 测试验证

重启服务后，可以通过以下方式验证跨域配置是否生效：

1. 打开浏览器开发者工具
2. 访问前端应用，加载WMS图层
3. 检查Network标签，看是否还有CORS错误
4. 查看Console标签，确认没有跨域相关错误信息

## 常见问题

### Q: 配置后仍然有跨域问题
A: 
1. 确认已完全重启GeoServer服务
2. 检查JAR文件是否正确复制到lib目录
3. 验证web.xml文件格式是否正确

### Q: WMS图层仍然无法显示
A:
1. 检查图层名称是否正确
2. 验证坐标系是否匹配（推荐使用EPSG:3857）
3. 确认图层已正确发布到GeoServer

### Q: 生产环境安全考虑
A: 生产环境中不建议设置 `allowedOrigins` 为 `*`，应该指定具体的域名：

```xml
<init-param>
    <param-name>allowedOrigins</param-name>
    <param-value>https://yourdomain.com,https://www.yourdomain.com</param-value>
</init-param>
```

## 参考资料

- [GeoServer官方CORS文档](http://docs.geoserver.org/stable/en/user/production/container.html#enabling-cors)
- [Leaflet WMS图层文档](https://leafletjs.com/examples/wms/wms.html)
- [MDN CORS文档](https://developer.mozilla.org/zh-CN/docs/Web/HTTP/CORS) 