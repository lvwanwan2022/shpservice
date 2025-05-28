<?xml version="1.0" encoding="UTF-8"?>
<sld:StyledLayerDescriptor xmlns="http://www.opengis.net/sld" 
                           xmlns:sld="http://www.opengis.net/sld" 
                           xmlns:ogc="http://www.opengis.net/ogc" 
                           xmlns:gml="http://www.opengis.net/gml" 
                           version="1.0.0">
  <sld:NamedLayer>
    <sld:Name>line_blue_dashed</sld:Name>
    <sld:UserStyle>
      <sld:Name>line_blue_dashed</sld:Name>
      <sld:Title>Custom Style for line_blue_dashed</sld:Title>
      <sld:Abstract>Custom style generated from frontend configuration</sld:Abstract>
      <sld:FeatureTypeStyle>
        <!-- Point Symbolizer Rule -->
        <sld:Rule>
          <sld:Name>Point Rule</sld:Name>
          <sld:Title>Point Style</sld:Title>
          <ogc:Filter>
            <ogc:Or>
              <ogc:PropertyIsEqualTo>
                <ogc:Function name="geometryType">
                  <ogc:PropertyName>the_geom</ogc:PropertyName>
                </ogc:Function>
                <ogc:Literal>Point</ogc:Literal>
              </ogc:PropertyIsEqualTo>
              <ogc:PropertyIsEqualTo>
                <ogc:Function name="geometryType">
                  <ogc:PropertyName>the_geom</ogc:PropertyName>
                </ogc:Function>
                <ogc:Literal>MultiPoint</ogc:Literal>
              </ogc:PropertyIsEqualTo>
            </ogc:Or>
          </ogc:Filter>
          <sld:PointSymbolizer>
            <sld:Graphic>
              <sld:Mark>
                <sld:WellKnownName>circle</sld:WellKnownName>
                <sld:Fill>
                  <sld:CssParameter name="fill">#FF0000</sld:CssParameter>
                  <sld:CssParameter name="fill-opacity">1.0</sld:CssParameter>
                </sld:Fill>
                <sld:Stroke>
                  <sld:CssParameter name="stroke">#000000</sld:CssParameter>
                  <sld:CssParameter name="stroke-width">0.5</sld:CssParameter>
                </sld:Stroke>
              </sld:Mark>
              <sld:Size>6</sld:Size>
            </sld:Graphic>
          </sld:PointSymbolizer>
        </sld:Rule>
        <!-- Line Symbolizer Rule -->
        <sld:Rule>
          <sld:Name>Line Rule</sld:Name>
          <sld:Title>Line Style</sld:Title>
          <ogc:Filter>
            <ogc:Or>
              <ogc:PropertyIsEqualTo>
                <ogc:Function name="geometryType">
                  <ogc:PropertyName>the_geom</ogc:PropertyName>
                </ogc:Function>
                <ogc:Literal>LineString</ogc:Literal>
              </ogc:PropertyIsEqualTo>
              <ogc:PropertyIsEqualTo>
                <ogc:Function name="geometryType">
                  <ogc:PropertyName>the_geom</ogc:PropertyName>
                </ogc:Function>
                <ogc:Literal>MultiLineString</ogc:Literal>
              </ogc:PropertyIsEqualTo>
            </ogc:Or>
          </ogc:Filter>
          <sld:LineSymbolizer>
            <sld:Stroke>
              <sld:CssParameter name="stroke">#0000FF</sld:CssParameter>
              <sld:CssParameter name="stroke-width">3</sld:CssParameter>
              <sld:CssParameter name="stroke-opacity">0.8</sld:CssParameter>
              <sld:CssParameter name="stroke-linecap">round</sld:CssParameter>
              <sld:CssParameter name="stroke-linejoin">round</sld:CssParameter>
              <sld:CssParameter name="stroke-dasharray">5 5</sld:CssParameter>
            </sld:Stroke>
          </sld:LineSymbolizer>
        </sld:Rule>
        <!-- Polygon Symbolizer Rule -->
        <sld:Rule>
          <sld:Name>Polygon Rule</sld:Name>
          <sld:Title>Polygon Style</sld:Title>
          <ogc:Filter>
            <ogc:Or>
              <ogc:PropertyIsEqualTo>
                <ogc:Function name="geometryType">
                  <ogc:PropertyName>the_geom</ogc:PropertyName>
                </ogc:Function>
                <ogc:Literal>Polygon</ogc:Literal>
              </ogc:PropertyIsEqualTo>
              <ogc:PropertyIsEqualTo>
                <ogc:Function name="geometryType">
                  <ogc:PropertyName>the_geom</ogc:PropertyName>
                </ogc:Function>
                <ogc:Literal>MultiPolygon</ogc:Literal>
              </ogc:PropertyIsEqualTo>
            </ogc:Or>
          </ogc:Filter>
          <sld:PolygonSymbolizer>
            <sld:Fill>
              <sld:CssParameter name="fill">#00FF00</sld:CssParameter>
              <sld:CssParameter name="fill-opacity">0.7</sld:CssParameter>
            </sld:Fill>
            <sld:Stroke>
              <sld:CssParameter name="stroke">#000000</sld:CssParameter>
              <sld:CssParameter name="stroke-width">1</sld:CssParameter>
              <sld:CssParameter name="stroke-opacity">1.0</sld:CssParameter>
            </sld:Stroke>
          </sld:PolygonSymbolizer>
        </sld:Rule>
      </sld:FeatureTypeStyle>
    </sld:UserStyle>
  </sld:NamedLayer>
</sld:StyledLayerDescriptor>