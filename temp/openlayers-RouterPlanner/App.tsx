import React, { useState, useCallback, useEffect } from 'react';
import { PanelLeftOpen } from 'lucide-react';
import MapEditor from './components/MapEditor';
import ControlPanel from './components/ControlPanel';
import { InteractionMode, RouteNode, IndustryMode } from './types';
import { getCornerData, getSpiralCornerData } from './utils/geometry';

function App() {
  const [isPanelOpen, setIsPanelOpen] = useState(false);
  const [mode, setMode] = useState<InteractionMode>(InteractionMode.DRAW);
  const [industryMode, setIndustryMode] = useState<IndustryMode>(IndustryMode.WATER);
  
  // State for the route
  const [routeNodes, setRouteNodes] = useState<RouteNode[]>([]);
  
  // State for selection
  const [selectedNodeIndex, setSelectedNodeIndex] = useState<number | null>(null);
  
  // Defaults
  const [defaultRadius, setDefaultRadius] = useState<number>(500); 
  const [defaultSpiralLen, setDefaultSpiralLen] = useState<number>(100);

  // Handle Delete Key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isPanelOpen || mode !== InteractionMode.EDIT) return;
      
      if (e.key === 'Delete' || e.key === 'Backspace') {
        if (selectedNodeIndex !== null) {
          const newNodes = [...routeNodes];
          newNodes.splice(selectedNodeIndex, 1);
          setRouteNodes(newNodes);
          setSelectedNodeIndex(null); 
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
    
    const isHighway = industryMode === IndustryMode.HIGHWAY;

    // Define headers dynamically
    let headers = ["x", "y", "radius"];
    if (isHighway) {
      headers.push("spiral_length");
    }
    headers.push("arc_center_x", "arc_center_y", "arc_start_x", "arc_start_y", "arc_end_x", "arc_end_y");

    let csvContent = "data:text/csv;charset=utf-8," + headers.join(",") + "\n";
    
    routeNodes.forEach((node, i) => {
        let arcData = { 
          cx: '', cy: '', 
          sx: '', sy: '', 
          ex: '', ey: '' 
        };

        // Calculate arc geometry for intermediate nodes based on current industry mode
        if (i > 0 && i < routeNodes.length - 1) {
          const pPrev = routeNodes[i - 1];
          const pNext = routeNodes[i + 1];
          
          let corner;
          const processingNode = {
             ...node,
             spiralLength: node.spiralLength !== undefined ? node.spiralLength : defaultSpiralLen
          };

          if (isHighway) {
              corner = getSpiralCornerData(pPrev, processingNode, pNext);
          } else {
              corner = getCornerData(pPrev, processingNode, pNext);
          }
          
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
        
        const r = node.radius;
        
        // Construct row
        let row: (number | string)[] = [node.x, node.y, r];
        
        if (isHighway) {
             const l = node.spiralLength !== undefined ? node.spiralLength : defaultSpiralLen;
             row.push(l);
        }

        row.push(arcData.cx, arcData.cy, arcData.sx, arcData.sy, arcData.ex, arcData.ey);

        csvContent += row.join(",") + "\n";
    });

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `route_data_${industryMode.toLowerCase()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }, [routeNodes, industryMode, defaultSpiralLen]);

  // Handle CSV Import
  const handleImport = useCallback((file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
        const text = e.target?.result as string;
        if (!text) return;

        const lines = text.split('\n');
        if (lines.length < 2) return;

        // Check header for column existence
        const header = lines[0].toLowerCase();
        const hasSpiral = header.includes('spiral_length');

        const newNodes: RouteNode[] = [];

        for(let i = 1; i < lines.length; i++) {
            const line = lines[i].trim();
            if(!line) continue;
            
            const parts = line.split(',');
            const x = Number(parts[0]);
            const y = Number(parts[1]);
            const r = Number(parts[2]);
            
            // If spiral exists in CSV, read it (index 3), otherwise default
            let spiralLength = defaultSpiralLen;
            if (hasSpiral) {
                const l = Number(parts[3]);
                if (!isNaN(l)) spiralLength = l;
            }

            if (!isNaN(x) && !isNaN(y)) {
                const radius = !isNaN(r) ? r : defaultRadius;
                newNodes.push({ x, y, radius, spiralLength });
            }
        }

        if (newNodes.length > 0) {
            setRouteNodes(newNodes);
            setMode(InteractionMode.EDIT); 
            setSelectedNodeIndex(null);
            
            // Auto-switch mode based on CSV content if possible?
            // For now, we respect the user's current choice, but data is loaded correctly.
            if (hasSpiral) {
                setIndustryMode(IndustryMode.HIGHWAY);
            } else {
                setIndustryMode(IndustryMode.WATER);
            }
        } else {
            alert("CSV 解析失败或文件为空。");
        }
    };
    reader.readAsText(file);
  }, [defaultRadius, defaultSpiralLen]);

  const handleSelectedRadiusChange = (newRadius: number) => {
    if (selectedNodeIndex === null) return;
    const updated = [...routeNodes];
    if (updated[selectedNodeIndex]) {
        updated[selectedNodeIndex] = { ...updated[selectedNodeIndex], radius: newRadius };
        setRouteNodes(updated);
    }
  };

  const handleSelectedSpiralLenChange = (newLen: number) => {
    if (selectedNodeIndex === null) return;
    const updated = [...routeNodes];
    if (updated[selectedNodeIndex]) {
        updated[selectedNodeIndex] = { ...updated[selectedNodeIndex], spiralLength: newLen };
        setRouteNodes(updated);
    }
  };

  const currentMapMode = isPanelOpen ? mode : InteractionMode.NONE;

  return (
    <div className="relative w-screen h-screen overflow-hidden bg-slate-200">
      
      {/* Map Layer */}
      <div className="absolute inset-0 z-0">
        <MapEditor 
            mode={currentMapMode} 
            industryMode={industryMode}
            nodes={routeNodes}
            onNodesChange={setRouteNodes}
            selectedNodeIndex={selectedNodeIndex}
            onNodeSelect={setSelectedNodeIndex}
            defaultRadius={defaultRadius}
            defaultSpiralLen={defaultSpiralLen}
        />
      </div>

      {/* Toggle Button */}
      {!isPanelOpen && (
        <button
          onClick={() => setIsPanelOpen(true)}
          className="absolute top-4 right-4 z-20 bg-white p-3 rounded-full shadow-lg border border-slate-200 text-slate-700 hover:text-blue-600 hover:shadow-xl transition-all group"
          title="打开编辑器"
        >
          <PanelLeftOpen size={24} className="group-hover:scale-110 transition-transform" />
        </button>
      )}

      {/* Control Panel */}
      <ControlPanel
        isOpen={isPanelOpen}
        onClose={() => setIsPanelOpen(false)}
        mode={mode}
        setMode={setMode}
        industryMode={industryMode}
        setIndustryMode={setIndustryMode}
        defaultRadius={defaultRadius}
        setDefaultRadius={setDefaultRadius}
        defaultSpiralLen={defaultSpiralLen}
        setDefaultSpiralLen={setDefaultSpiralLen}
        selectedRadius={selectedNodeIndex !== null && routeNodes[selectedNodeIndex] ? routeNodes[selectedNodeIndex].radius : null}
        onSelectedRadiusChange={handleSelectedRadiusChange}
        selectedSpiralLen={selectedNodeIndex !== null && routeNodes[selectedNodeIndex] ? (routeNodes[selectedNodeIndex].spiralLength ?? defaultSpiralLen) : null}
        onSelectedSpiralLenChange={handleSelectedSpiralLenChange}
        hasSelection={selectedNodeIndex !== null}
        onExport={handleExport}
        onImport={handleImport}
      />

      {/* Legend */}
      {isPanelOpen && (
        <div className="absolute bottom-6 right-6 z-10 bg-white/90 backdrop-blur-sm px-5 py-3 rounded-xl shadow-lg border border-slate-200 text-xs text-slate-600 pointer-events-none select-none flex flex-col gap-2">
          <h4 className="font-bold text-slate-800 uppercase tracking-wider text-[10px]">图例 ({industryMode === IndustryMode.WATER ? '水利' : '公路'})</h4>
          <div className="flex items-center gap-3">
              <span className="w-6 h-0.5 bg-blue-400 border-dashed border-b border-blue-400 block"></span>
              <span>控制路径</span>
          </div>
          <div className="flex items-center gap-3">
              <span className="w-6 h-1 bg-blue-600 block rounded-full"></span>
              <span>直线段</span>
          </div>
          {industryMode === IndustryMode.HIGHWAY && (
             <div className="flex items-center gap-3">
               <span className="w-6 h-1 bg-purple-600 block rounded-full"></span>
               <span>缓和曲线</span>
             </div>
          )}
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