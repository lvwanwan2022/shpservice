import React, { useState, useCallback, useEffect } from 'react';
import { Menu, PanelLeftOpen } from 'lucide-react';
import MapEditor from './components/MapEditor';
import ControlPanel from './components/ControlPanel';
import { InteractionMode, RouteNode } from './types';
import { getCornerData } from './utils/geometry';

function App() {
  const [isPanelOpen, setIsPanelOpen] = useState(false); // Default closed per request implication
  const [mode, setMode] = useState<InteractionMode>(InteractionMode.DRAW);
  
  // State for the route
  const [routeNodes, setRouteNodes] = useState<RouteNode[]>([]);
  
  // State for selection
  const [selectedNodeIndex, setSelectedNodeIndex] = useState<number | null>(null);
  
  // Default radius for NEW points
  const [defaultRadius, setDefaultRadius] = useState<number>(5000); 

  // Handle Delete Key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isPanelOpen || mode !== InteractionMode.EDIT) return;
      
      if (e.key === 'Delete' || e.key === 'Backspace') {
        if (selectedNodeIndex !== null) {
          const newNodes = [...routeNodes];
          // Remove the selected node
          newNodes.splice(selectedNodeIndex, 1);
          setRouteNodes(newNodes);
          setSelectedNodeIndex(null); // Deselect
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isPanelOpen, mode, selectedNodeIndex, routeNodes]);

  // Handle CSV Export
  const handleExport = useCallback(() => {
    if (routeNodes.length === 0) {
      alert("没有可导出的路径。");
      return;
    }
    
    // Extended Header
    let csvContent = "data:text/csv;charset=utf-8,x,y,radius,arc_center_x,arc_center_y,arc_start_x,arc_start_y,arc_end_x,arc_end_y\n";
    
    routeNodes.forEach((node, i) => {
        let arcData = { 
          cx: '', cy: '', 
          sx: '', sy: '', 
          ex: '', ey: '' 
        };

        // Calculate arc geometry for intermediate nodes
        if (i > 0 && i < routeNodes.length - 1) {
          const pPrev = routeNodes[i - 1];
          const pNext = routeNodes[i + 1];
          const corner = getCornerData(pPrev, node, pNext);
          
          if (corner) {
            arcData = {
              cx: corner.center.x.toFixed(3),
              cy: corner.center.y.toFixed(3),
              sx: corner.t1.x.toFixed(3),
              sy: corner.t1.y.toFixed(3),
              ex: corner.t2.x.toFixed(3),
              ey: corner.t2.y.toFixed(3)
            };
          }
        }

        csvContent += `${node.x},${node.y},${node.radius},${arcData.cx},${arcData.cy},${arcData.sx},${arcData.sy},${arcData.ex},${arcData.ey}\n`;
    });

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "route_data.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }, [routeNodes]);

  // Handle CSV Import
  const handleImport = useCallback((file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
        const text = e.target?.result as string;
        if (!text) return;

        const lines = text.split('\n');
        const newNodes: RouteNode[] = [];

        // Skip header (index 0)
        for(let i = 1; i < lines.length; i++) {
            const line = lines[i].trim();
            if(!line) continue;
            
            // Read first 3 columns, ignore the rest if they exist
            const parts = line.split(',');
            const x = Number(parts[0]);
            const y = Number(parts[1]);
            const r = Number(parts[2]);

            if (!isNaN(x) && !isNaN(y)) {
                // If radius is missing or invalid, use default
                const radius = !isNaN(r) ? r : defaultRadius;
                newNodes.push({ x, y, radius });
            }
        }

        if (newNodes.length > 0) {
            setRouteNodes(newNodes);
            setMode(InteractionMode.EDIT); 
            setSelectedNodeIndex(null);
        } else {
            alert("CSV 解析失败或文件为空。");
        }
    };
    reader.readAsText(file);
  }, [defaultRadius]);

  const handleSelectedRadiusChange = (newRadius: number) => {
    if (selectedNodeIndex === null) return;
    
    const updated = [...routeNodes];
    if (updated[selectedNodeIndex]) {
        updated[selectedNodeIndex] = { ...updated[selectedNodeIndex], radius: newRadius };
        setRouteNodes(updated);
    }
  };

  // If panel is closed, force NONE mode (Browse only)
  const currentMapMode = isPanelOpen ? mode : InteractionMode.NONE;

  return (
    <div className="relative w-screen h-screen overflow-hidden bg-slate-200">
      
      {/* Map Layer */}
      <div className="absolute inset-0 z-0">
        <MapEditor 
            mode={currentMapMode} 
            nodes={routeNodes}
            onNodesChange={setRouteNodes}
            selectedNodeIndex={selectedNodeIndex}
            onNodeSelect={setSelectedNodeIndex}
            defaultRadius={defaultRadius}
        />
      </div>

      {/* Toggle Button (Top Right) */}
      {!isPanelOpen && (
        <button
          onClick={() => setIsPanelOpen(true)}
          className="absolute top-4 right-4 z-20 bg-white p-3 rounded-full shadow-lg border border-slate-200 text-slate-700 hover:text-blue-600 hover:shadow-xl transition-all group"
          title="打开编辑器"
        >
          <PanelLeftOpen size={24} className="group-hover:scale-110 transition-transform" />
        </button>
      )}

      {/* Control Panel (Left Side) */}
      <ControlPanel
        isOpen={isPanelOpen}
        onClose={() => setIsPanelOpen(false)}
        mode={mode}
        setMode={setMode}
        defaultRadius={defaultRadius}
        setDefaultRadius={setDefaultRadius}
        selectedRadius={selectedNodeIndex !== null && routeNodes[selectedNodeIndex] ? routeNodes[selectedNodeIndex].radius : null}
        onSelectedRadiusChange={handleSelectedRadiusChange}
        hasSelection={selectedNodeIndex !== null}
        onExport={handleExport}
        onImport={handleImport}
      />

      {/* Info Legend Overlay (Bottom Right) - Only visible when panel is open */}
      {isPanelOpen && (
        <div className="absolute bottom-6 right-6 z-10 bg-white/90 backdrop-blur-sm px-5 py-3 rounded-xl shadow-lg border border-slate-200 text-xs text-slate-600 pointer-events-none select-none flex flex-col gap-2">
          <h4 className="font-bold text-slate-800 uppercase tracking-wider text-[10px]">图例</h4>
          <div className="flex items-center gap-3">
              <span className="w-6 h-0.5 bg-blue-400 border-dashed border-b border-blue-400 block"></span>
              <span>控制路径</span>
          </div>
          <div className="flex items-center gap-3">
              <span className="w-6 h-1 bg-blue-600 block rounded-full"></span>
              <span>直线段</span>
          </div>
          <div className="flex items-center gap-3">
              <span className="w-6 h-1 bg-red-500 block rounded-full"></span>
              <span>圆弧段</span>
          </div>
          <div className="flex items-center gap-3 mt-1">
              <div className="w-3 h-3 rounded-full border-2 border-blue-500 bg-white"></div>
              <span>控制点</span>
          </div>
        </div>
      )}

    </div>
  );
}

export default App;