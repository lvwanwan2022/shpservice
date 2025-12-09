import React, { useRef } from 'react';
import { X, Pencil, Download, Upload, Settings2, PenLine, CornerUpLeft, MousePointer2 } from 'lucide-react';
import { InteractionMode } from '../types';

interface ControlPanelProps {
  isOpen: boolean;
  onClose: () => void;
  mode: InteractionMode;
  setMode: (mode: InteractionMode) => void;
  defaultRadius: number;
  setDefaultRadius: (r: number) => void;
  selectedRadius: number | null;
  onSelectedRadiusChange: (r: number) => void;
  hasSelection: boolean;
  onExport: () => void;
  onImport: (file: File) => void;
  onUndo?: () => void; 
}

const ControlPanel: React.FC<ControlPanelProps> = ({
  isOpen,
  onClose,
  mode,
  setMode,
  defaultRadius,
  setDefaultRadius,
  selectedRadius,
  onSelectedRadiusChange,
  hasSelection,
  onExport,
  onImport,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  return (
    <div className="absolute top-0 left-0 h-full w-80 bg-white shadow-2xl z-20 flex flex-col border-r border-slate-200 transition-transform duration-300">
      
      {/* Header */}
      <div className="p-5 border-b border-slate-100 flex justify-between items-center bg-slate-50">
        <h2 className="font-bold text-slate-800 flex items-center gap-2 text-lg">
          <Settings2 className="text-blue-600" size={24} />
          路径规划师
        </h2>
        <button 
          onClick={onClose}
          className="p-1 hover:bg-slate-200 rounded-full transition-colors text-slate-500"
        >
          <X size={20} />
        </button>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto p-5 space-y-8">
        
        {/* Tools Section */}
        <section className="space-y-4">
          <label className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
            <MousePointer2 size={12} /> 模式
          </label>
          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={() => setMode(InteractionMode.DRAW)}
              className={`flex flex-col items-center justify-center gap-2 p-4 rounded-xl border transition-all ${
                mode === InteractionMode.DRAW
                  ? 'bg-blue-600 text-white border-blue-600 shadow-lg shadow-blue-200/50'
                  : 'bg-white text-slate-600 border-slate-200 hover:border-blue-400 hover:text-blue-600 hover:shadow-sm'
              }`}
            >
              <PenLine size={24} />
              <span className="text-sm font-semibold">绘制</span>
            </button>
            <button
              onClick={() => setMode(InteractionMode.EDIT)}
              className={`flex flex-col items-center justify-center gap-2 p-4 rounded-xl border transition-all ${
                mode === InteractionMode.EDIT
                  ? 'bg-amber-500 text-white border-amber-500 shadow-lg shadow-amber-200/50'
                  : 'bg-white text-slate-600 border-slate-200 hover:border-amber-400 hover:text-amber-600 hover:shadow-sm'
              }`}
            >
              <Pencil size={24} />
              <span className="text-sm font-semibold">编辑</span>
            </button>
          </div>
          <div className="text-xs text-slate-500 bg-slate-50 p-3 rounded-lg border border-slate-100 leading-relaxed">
            {mode === InteractionMode.DRAW && "点击地图绘制线条。在端点附近绘制可延长路线。"}
            {mode === InteractionMode.EDIT && "拖动点以移动。双击线条插入点。点击白色控制点可编辑其转弯半径。"}
          </div>
        </section>

        {/* Selected Point Properties */}
        <section className="space-y-4">
          <label className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
            <CornerUpLeft size={12} /> 转弯半径
          </label>
          
          {hasSelection && selectedRadius !== null && selectedRadius !== undefined ? (
            <div className="space-y-3 bg-blue-50/50 p-4 rounded-xl border border-blue-100 transition-all">
              <div className="flex justify-between items-center mb-1">
                 <span className="text-sm font-semibold text-slate-700">选中角点</span>
              </div>
              
              <div className="flex items-center gap-2">
                <input
                  type="range"
                  min="0"
                  max="50000" 
                  step="50"
                  value={selectedRadius}
                  onChange={(e) => onSelectedRadiusChange(Number(e.target.value))}
                  className="flex-1 h-2 bg-blue-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                />
                <div className="relative w-24">
                  <input
                    type="number"
                    min="0"
                    value={selectedRadius}
                    onChange={(e) => onSelectedRadiusChange(Math.max(0, Number(e.target.value)))}
                    className="w-full pl-2 pr-6 py-1 text-sm border border-blue-200 rounded text-right text-slate-700 focus:outline-none focus:border-blue-500"
                  />
                  <span className="absolute right-2 top-1.5 text-xs text-slate-400">m</span>
                </div>
              </div>

              <p className="text-xs text-blue-400 mt-1">
                正在调整选中红点的半径。
              </p>
            </div>
          ) : (
             <div className="p-4 rounded-xl border border-dashed border-slate-300 text-center text-slate-400 text-sm">
                在地图上选择一个控制点以编辑其半径。
             </div>
          )}

          {/* Default Radius Config */}
          <div className="pt-4 border-t border-slate-100">
             <div className="flex justify-between items-center mb-2">
                 <span className="text-xs font-medium text-slate-500">默认半径 (新点)</span>
                 <span className="text-xs font-mono text-slate-400">{defaultRadius} m</span>
             </div>
             <input
                type="range"
                min="0"
                max="50000" 
                step="50"
                value={defaultRadius}
                onChange={(e) => setDefaultRadius(Number(e.target.value))}
                className="w-full h-1 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-slate-400"
              />
          </div>
        </section>

        {/* Data Management */}
        <section className="space-y-3 pt-2">
          <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">数据管理</label>
          <div className="grid grid-cols-2 gap-3">
            <button 
                onClick={onExport}
                className="flex items-center justify-center gap-2 p-3 rounded-lg border border-slate-200 hover:bg-slate-50 hover:border-slate-300 text-slate-700 text-sm font-medium transition-colors"
            >
              <Download size={16} />
              导出
            </button>
            <button 
                onClick={() => fileInputRef.current?.click()}
                className="flex items-center justify-center gap-2 p-3 rounded-lg border border-slate-200 hover:bg-slate-50 hover:border-slate-300 text-slate-700 text-sm font-medium transition-colors"
            >
              <Upload size={16} />
              导入
            </button>
            <input 
                type="file" 
                accept=".csv"
                ref={fileInputRef}
                className="hidden"
                onChange={(e) => {
                    if (e.target.files?.[0]) {
                        onImport(e.target.files[0]);
                        e.target.value = ''; 
                    }
                }}
            />
          </div>
        </section>

      </div>
      
      {/* Footer */}
      <div className="p-4 border-t border-slate-100 bg-slate-50 text-center">
        <p className="text-[10px] text-slate-400">
          左键点击选择点。双击地图结束绘制。按 Delete 删除选中点。
        </p>
      </div>
    </div>
  );
};

export default ControlPanel;