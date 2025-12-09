
import React, { useEffect, useRef } from 'react';
import Map from 'ol/Map';
import View from 'ol/View';
import TileLayer from 'ol/layer/Tile';
import OSM from 'ol/source/OSM';
import VectorLayer from 'ol/layer/Vector';
import VectorSource from 'ol/source/Vector';
import { Style, Stroke, Circle as CircleStyle, Fill } from 'ol/style';
import { Draw, Modify, Snap } from 'ol/interaction';
import { defaults as defaultControls } from 'ol/control';
import Feature from 'ol/Feature';
import LineString from 'ol/geom/LineString';
import Point from 'ol/geom/Point';
import Overlay from 'ol/Overlay';
import { Coordinate, InteractionMode, RouteNode, RouteSegment, IndustryMode } from '../types';
import { generateFilletedSegments } from '../utils/geometry';

interface MapEditorProps {
  mode: InteractionMode;
  industryMode: IndustryMode;
  nodes: RouteNode[];
  onNodesChange: (nodes: RouteNode[]) => void;
  selectedNodeIndex: number | null;
  onNodeSelect: (index: number | null) => void;
  defaultRadius: number;
  defaultSpiralLen: number;
}

const MapEditor: React.FC<MapEditorProps> = ({ 
  mode, 
  industryMode,
  nodes, 
  onNodesChange, 
  selectedNodeIndex,
  onNodeSelect,
  defaultRadius,
  defaultSpiralLen
}) => {
  const mapElement = useRef<HTMLDivElement>(null);
  const mapRef = useRef<Map | null>(null);
  
  // Layer Sources
  const controlSourceRef = useRef(new VectorSource()); // The polyline user edits
  const arcSourceRef = useRef(new VectorSource());     // Generated arcs
  const spiralSourceRef = useRef(new VectorSource());  // Generated spirals
  const lineSourceRef = useRef(new VectorSource());    // Generated straight lines
  const pointSourceRef = useRef(new VectorSource());   // Control points visualization

  // Overlay for Distance Tooltip
  const tooltipElementRef = useRef<HTMLDivElement | null>(null);
  const tooltipOverlayRef = useRef<Overlay | null>(null);

  const drawInteractionRef = useRef<Draw | null>(null);
  const modifyInteractionRef = useRef<Modify | null>(null);
  const snapInteractionRef = useRef<Snap | null>(null);

  // Drawing state tracking
  const isDrawingRef = useRef(false);
  const sketchFeatureRef = useRef<Feature | null>(null);

  // Refs for current state inside event handlers
  const nodesRef = useRef(nodes);
  const modeRef = useRef(mode);
  const segmentsRef = useRef<RouteSegment[]>([]);

  useEffect(() => {
    nodesRef.current = nodes;
  }, [nodes]);

  useEffect(() => {
    modeRef.current = mode;
  }, [mode]);

  // Initialize Map
  useEffect(() => {
    if (!mapElement.current) return;

    // Create Tooltip Element
    const tooltipEl = document.createElement('div');
    tooltipEl.style.position = 'absolute';
    tooltipEl.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
    tooltipEl.style.color = 'white';
    tooltipEl.style.padding = '4px 8px';
    tooltipEl.style.borderRadius = '4px';
    tooltipEl.style.fontSize = '12px';
    tooltipEl.style.whiteSpace = 'nowrap';
    tooltipEl.style.pointerEvents = 'none';
    tooltipEl.style.zIndex = '1000';
    tooltipEl.style.display = 'none'; // Hidden by default
    tooltipElementRef.current = tooltipEl;
    document.body.appendChild(tooltipEl);

    const overlay = new Overlay({
      element: tooltipEl,
      offset: [10, 0],
      positioning: 'bottom-left',
      stopEvent: false
    });
    tooltipOverlayRef.current = overlay;

    // Styles
    const controlStyle = new Style({
      stroke: new Stroke({
        color: 'rgba(59, 130, 246, 0.3)', // Faint blue
        width: 1,
        lineDash: [5, 5],
      }),
    });

    // Style for straight parts of the route
    const lineStyle = new Style({
      stroke: new Stroke({
        color: '#2563eb', // Blue-600
        width: 3,
      }),
    });

    // Style for arcs
    const arcStyle = new Style({
      stroke: new Stroke({
        color: '#ef4444', // Red-500
        width: 3,
      }),
    });

    // Style for spirals (Highway Mode)
    const spiralStyle = new Style({
      stroke: new Stroke({
        color: '#9333ea', // Purple-600
        width: 3,
      }),
    });

    // Style function for control points
    const pointStyleFunc = (feature: any) => {
      const isSelected = feature.get('isSelected');
      return new Style({
        image: new CircleStyle({
          radius: isSelected ? 8 : 5,
          fill: new Fill({ color: isSelected ? '#ef4444' : '#ffffff' }),
          stroke: new Stroke({ color: '#3b82f6', width: 2 }),
        }),
      });
    };

    const map = new Map({
      target: mapElement.current,
      layers: [
        new TileLayer({ source: new OSM() }),
        new VectorLayer({ source: lineSourceRef.current, style: lineStyle }),
        new VectorLayer({ source: spiralSourceRef.current, style: spiralStyle }),
        new VectorLayer({ source: arcSourceRef.current, style: arcStyle }),
        new VectorLayer({ source: controlSourceRef.current, style: controlStyle }),
        new VectorLayer({ source: pointSourceRef.current, style: pointStyleFunc as any }),
      ],
      view: new View({ center: [0, 0], zoom: 2 }),
      controls: defaultControls({ zoom: false, rotate: false, attribution: false }),
      overlays: [overlay]
    });

    mapRef.current = map;

    // Click handler for node selection
    map.on('click', (e) => {
      const pixel = e.pixel;
      const feature = map.forEachFeatureAtPixel(pixel, (feat) => feat, {
        layerFilter: (layer) => layer.getSource() === pointSourceRef.current,
        hitTolerance: 10
      });

      if (feature) {
        const index = feature.get('index');
        onNodeSelect(index);
      } else {
        onNodeSelect(null);
      }
    });

    // Double Click Handler for Inserting Nodes
    map.on('dblclick', (e) => {
      if (modeRef.current !== InteractionMode.EDIT) return;

      const clickCoords = e.coordinate;
      const nodes = nodesRef.current;
      if (nodes.length < 2) return;

      const mapResolution = map.getView().getResolution() || 1;
      const threshold = 10 * mapResolution; // 10 pixels tolerance

      let minDistance = Infinity;
      let insertIndex = -1;
      let insertPoint = { x: 0, y: 0 };

      // Helper to find closest point on segment
      const getClosest = (p: Coordinate, a: Coordinate, b: Coordinate) => {
        const atob = { x: b.x - a.x, y: b.y - a.y };
        const atop = { x: p.x - a.x, y: p.y - a.y };
        const lenSq = atob.x * atob.x + atob.y * atob.y;
        if (lenSq === 0) return a;
        const dot = atop.x * atob.x + atop.y * atob.y;
        const t = Math.max(0, Math.min(1, dot / lenSq));
        return {
            x: a.x + atob.x * t,
            y: a.y + atob.y * t
        };
      };

      for (let i = 0; i < nodes.length - 1; i++) {
         const p1 = nodes[i];
         const p2 = nodes[i+1];
         const closest = getClosest({ x: clickCoords[0], y: clickCoords[1] }, p1, p2);
         const dist = Math.sqrt((closest.x - clickCoords[0])**2 + (closest.y - clickCoords[1])**2);
         
         if (dist < minDistance) {
             minDistance = dist;
             insertIndex = i + 1;
             insertPoint = closest;
         }
      }

      if (insertIndex !== -1 && minDistance < threshold) {
          const newNodes = [...nodes];
          newNodes.splice(insertIndex, 0, { ...insertPoint, radius: defaultRadius });
          onNodesChange(newNodes);
          return false;
      }
    });

    // Pointer move for distance tooltip
    map.on('pointermove', (e) => {
      if (tooltipElementRef.current && tooltipOverlayRef.current) {
         const mapResolution = map.getView().getResolution() || 1;
         const segments = segmentsRef.current;
         const coordinate = e.coordinate;
         const threshold = 15 * mapResolution; 

         let closestDist = Infinity;
         let distanceAtCursor = -1;
         let bestPosition: number[] | null = null;
         let currentSegmentStartDist = 0;

         for (const segment of segments) {
            const coords = segment.coordinates.map(c => [c.x, c.y]);
            if (coords.length < 2) continue;
            
            const line = new LineString(coords);
            const closestPoint = line.getClosestPoint(coordinate);
            const dist = Math.sqrt((closestPoint[0]-coordinate[0])**2 + (closestPoint[1]-coordinate[1])**2);
            
            if (dist < closestDist) {
              closestDist = dist;
              bestPosition = closestPoint;
              
              let lengthAlongSegment = 0;
              for (let i = 0; i < coords.length - 1; i++) {
                 const p1 = coords[i];
                 const p2 = coords[i+1];
                 const segLen = Math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2);
                 const d1 = Math.sqrt((p1[0]-closestPoint[0])**2 + (p1[1]-closestPoint[1])**2);
                 const d2 = Math.sqrt((closestPoint[0]-p2[0])**2 + (closestPoint[1]-p2[1])**2);
                 
                 if (Math.abs((d1 + d2) - segLen) < 1e-3) {
                     lengthAlongSegment += d1;
                     break;
                 } else {
                     lengthAlongSegment += segLen;
                 }
              }
              
              const totalSegLen = line.getLength();
              if (lengthAlongSegment > totalSegLen) lengthAlongSegment = totalSegLen;

              distanceAtCursor = currentSegmentStartDist + lengthAlongSegment;
            }

            currentSegmentStartDist += line.getLength();
         }

         if (closestDist < threshold && bestPosition && distanceAtCursor !== -1) {
            tooltipElementRef.current.style.display = 'block';
            tooltipElementRef.current.innerHTML = `${distanceAtCursor.toFixed(1)} m`;
            tooltipOverlayRef.current.setPosition(bestPosition);
         } else {
            tooltipElementRef.current.style.display = 'none';
         }
      }
    });

    return () => {
      if (tooltipElementRef.current && tooltipElementRef.current.parentNode) {
        tooltipElementRef.current.parentNode.removeChild(tooltipElementRef.current);
      }
      map.setTarget(undefined);
    };
  }, []); 

  // -----------------------------
  // Render Logic
  // -----------------------------
  useEffect(() => {
    // 1. Control Line
    const coords = nodes.map(n => [n.x, n.y]);
    const features = controlSourceRef.current.getFeatures();
    
    if (nodes.length > 1) {
      if (features.length > 0) {
        const geom = features[0].getGeometry();
        if (geom instanceof LineString) {
          geom.setCoordinates(coords);
        }
      } else {
        const feature = new Feature(new LineString(coords));
        controlSourceRef.current.addFeature(feature);
      }
    } else {
      controlSourceRef.current.clear();
    }

    // 2. Control Points
    pointSourceRef.current.clear();
    nodes.forEach((node, idx) => {
      const feat = new Feature(new Point([node.x, node.y]));
      feat.set('index', idx);
      feat.set('isSelected', idx === selectedNodeIndex);
      pointSourceRef.current.addFeature(feat);
    });

    // 3. Generate Segments
    const segments = generateFilletedSegments(nodes, industryMode, defaultSpiralLen);
    segmentsRef.current = segments;
    
    arcSourceRef.current.clear();
    lineSourceRef.current.clear();
    spiralSourceRef.current.clear();

    segments.forEach(seg => {
      const geom = new LineString(seg.coordinates.map(c => [c.x, c.y]));
      const feat = new Feature(geom);
      if (seg.type === 'arc') {
        arcSourceRef.current.addFeature(feat);
      } else if (seg.type === 'spiral') {
        spiralSourceRef.current.addFeature(feat);
      } else {
        lineSourceRef.current.addFeature(feat);
      }
    });

  }, [nodes, selectedNodeIndex, industryMode, defaultRadius, defaultSpiralLen]);


  // -----------------------------
  // Interaction Logic
  // -----------------------------
  useEffect(() => {
    if (!mapRef.current) return;
    const map = mapRef.current;

    [drawInteractionRef.current, modifyInteractionRef.current, snapInteractionRef.current].forEach(i => {
      if (i) map.removeInteraction(i);
    });

    const snap = new Snap({ source: controlSourceRef.current });
    const snapPoints = new Snap({ source: pointSourceRef.current });

    if (mode === InteractionMode.DRAW) {
      const draw = new Draw({
        source: controlSourceRef.current,
        type: 'LineString',
      });

      draw.on('drawstart', (e) => {
         isDrawingRef.current = true;
         sketchFeatureRef.current = e.feature;
         const currentNodes = nodesRef.current;
         if (currentNodes.length > 2) {
          const geom = e.feature.getGeometry();
          if (geom instanceof LineString) {
            const coords = geom.getCoordinates();
            if (coords.length > 0) {
               const startX = coords[0][0];
               const startY = coords[0][1];
               const isIntermediate = currentNodes.slice(1, -1).some(n => {
                 const d = Math.sqrt(Math.pow(n.x - startX, 2) + Math.pow(n.y - startY, 2));
                 return d < 0.1; 
               });
               if (isIntermediate) draw.abortDrawing();
            }
          }
        }
      });

      draw.on('drawend', (e) => {
        isDrawingRef.current = false;
        sketchFeatureRef.current = null;
        
        const currentNodes = nodesRef.current;
        const geom = e.feature.getGeometry();
        
        if (geom instanceof LineString) {
          const newCoords = geom.getCoordinates().map(c => ({ x: c[0], y: c[1] }));
          let updatedNodes = [...currentNodes];
          
          if (updatedNodes.length > 0) {
             // Basic merging logic for drawing extension
             const lastNode = updatedNodes[updatedNodes.length - 1];
             const firstNode = updatedNodes[0];
             const newFirst = newCoords[0];
             const newLast = newCoords[newCoords.length - 1];
             const dist = (a: Coordinate, b: Coordinate) => Math.sqrt((a.x-b.x)**2 + (a.y-b.y)**2);
             const TOLERANCE = 100;

             // Helper to add nodes with default properties
             const mapToNodes = (coords: Coordinate[]) => coords.map(c => ({ 
                 ...c, 
                 radius: defaultRadius,
                 spiralLength: defaultSpiralLen 
             }));

             if (dist(lastNode, newFirst) < TOLERANCE) {
                updatedNodes = [...updatedNodes, ...mapToNodes(newCoords.slice(1))];
             } else if (dist(firstNode, newLast) < TOLERANCE) {
                updatedNodes = [...mapToNodes(newCoords.slice(0, -1)), ...updatedNodes];
             } else if (dist(lastNode, newLast) < TOLERANCE) {
                 updatedNodes = [...updatedNodes, ...mapToNodes([...newCoords].reverse().slice(1))];
             } else if (dist(firstNode, newFirst) < TOLERANCE) {
                 updatedNodes = [...mapToNodes([...newCoords].reverse().slice(0, -1)), ...updatedNodes];
             } else {
                 updatedNodes = mapToNodes(newCoords);
             }
          } else {
             updatedNodes = newCoords.map(c => ({ 
                 ...c, 
                 radius: defaultRadius,
                 spiralLength: defaultSpiralLen 
             }));
          }

          onNodesChange(updatedNodes);
          setTimeout(() => { controlSourceRef.current.clear(); }, 0);
        }
      });

      draw.on('drawabort', () => {
         isDrawingRef.current = false;
         sketchFeatureRef.current = null;
      });

      map.addInteraction(draw);
      drawInteractionRef.current = draw;
    } else if (mode === InteractionMode.EDIT) {
       const modify = new Modify({ source: pointSourceRef.current });
       modify.on('modifyend', (e) => {
         const features = pointSourceRef.current.getFeatures();
         const newNodes = [...nodesRef.current];
         features.forEach(f => {
           const idx = f.get('index');
           const geom = f.getGeometry();
           if (geom instanceof Point && typeof idx === 'number' && newNodes[idx]) {
             const coords = geom.getCoordinates();
             newNodes[idx] = { ...newNodes[idx], x: coords[0], y: coords[1] };
           }
         });
         onNodesChange(newNodes);
       });
       map.addInteraction(modify);
       modifyInteractionRef.current = modify;
    }

    map.addInteraction(snap);
    map.addInteraction(snapPoints);
    snapInteractionRef.current = snap;

    return () => {
      map.removeInteraction(snap);
      map.removeInteraction(snapPoints);
      if (drawInteractionRef.current) map.removeInteraction(drawInteractionRef.current);
      if (modifyInteractionRef.current) map.removeInteraction(modifyInteractionRef.current);
    };

  }, [mode, defaultRadius, defaultSpiralLen, onNodesChange, onNodeSelect]);

  // Handle ESC for Undo
  useEffect(() => {
      const handleKeyDown = (e: KeyboardEvent) => {
         if (e.key === 'Escape') {
             if (mode === InteractionMode.DRAW) {
                 e.preventDefault();
                 e.stopPropagation();
                 if (isDrawingRef.current && drawInteractionRef.current) {
                     const sketch = sketchFeatureRef.current;
                     if (sketch) {
                         const geom = sketch.getGeometry();
                         if (geom instanceof LineString && geom.getCoordinates().length > 2) {
                             drawInteractionRef.current.removeLastPoint();
                         } else {
                             drawInteractionRef.current.abortDrawing();
                         }
                     }
                 } else {
                     if (nodesRef.current.length > 0) {
                         onNodesChange(nodesRef.current.slice(0, -1));
                     }
                 }
             }
         }
      };
      document.addEventListener('keydown', handleKeyDown, { capture: true });
      return () => document.removeEventListener('keydown', handleKeyDown, { capture: true });
  }, [mode, onNodesChange]);

  return <div ref={mapElement} className="w-full h-full" />;
};

export default MapEditor;
