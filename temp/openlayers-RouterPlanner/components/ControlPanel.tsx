
import React, { useRef } from 'react';
import { X, Pencil, Download, Upload, Settings2, PenLine, CornerUpLeft, MousePointer2, GitCommit, Waves, Car } from 'lucide-react';
import { InteractionMode, IndustryMode } from '../types';

interface ControlPanelProps {
  isOpen: boolean;
  onClose: () => void;
  mode: InteractionMode;
  setMode: (mode: InteractionMode) => void;
  
  industryMode: IndustryMode;
  setIndustryMode: (mode: IndustryMode) => void;

  defaultRadius: number;
  setDefaultRadius: (r: number) => void;
  defaultSpiralLen: number;
  setDefaultSpiralLen: (l: number) => void;

  selectedRadius: number | null;
  onSelectedRadiusChange: (r: number) => void;
  selectedSpiralLen: number | null;
  onSelectedSpiralLenChange: (l: number) => void;

  hasSelection: boolean;
  onExport: () => void;
  onImport: (file: File) => void;
}

const ControlPanel: React.FC<ControlPanelProps> = ({
  isOpen,
  onClose,
  mode,
  setMode,
  industryMode,
  setIndustryMode,
  defaultRadius,
  setDefaultRadius,
  defaultSpiralLen,
  setDefaultSpiralLen,
  selectedRadius,
  onSelectedRadiusChange,
  selectedSpiralLen,
  onSelectedSpiralLenChange,
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
        
        {/* Industry Selection */}
        <section className="space-y-3">
            <div className="flex bg-slate-100 p-1 rounded-lg">
                <button 
                    onClick={() => setIndustryMode(IndustryMode.WATER)}
                    className={`flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-md text-xs font-semibold transition-all ${
                        industryMode === IndustryMode.WATER 
                        ? 'bg-white text-blue-600 shadow-sm' 
                        : 'text-slate-500 hover:text-slate-700'
                    }`}
                >
                    <Waves size={14} /> 水利行业
                </button>
                <button 
                    onClick={() => setIndustryMode(IndustryMode.HIGHWAY)}
                    className={`flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-md text-xs font-semibold transition-all ${
                        industryMode === IndustryMode.HIGHWAY 
                        ? 'bg-white text-purple-600 shadow-sm' 
                        : 'text-slate-500 hover:text-slate-700'
                    }`}
                >
                    <Car size={14} /> 公路行业
                </button>
            </div>
            {industryMode === IndustryMode.HIGHWAY && (
                <div className="text-[10px] text-purple-600 bg-purple-50 p-2 rounded border border-purple-100">
                    公路模式启用缓和曲线 (回旋线)。<br/>连接方式: 直线-回旋线-圆-回旋线-直线。
                </div>
            )}
        </section>

        {/* Tools Section */}
        <section className="space-y-4">
          <label className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
            <MousePointer2 size={12} /> 交互模式
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
        </section>

        {/* Selected Point Properties */}
        <section className="space-y-4">
          <label className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
            <CornerUpLeft size={12} /> 参数设置
          </label>
          
          {hasSelection && selectedRadius !== null ? (
            <div className={`space-y-3 p-4 rounded-xl border transition-all ${industryMode === IndustryMode.HIGHWAY ? 'bg-purple-50/50 border-purple-100' : 'bg-blue-50/50 border-blue-100'}`}>
              <div className="flex justify-between items-center mb-1">
                 <span className="text-sm font-semibold text-slate-700">选中角点</span>
              </div>
              
              {/* Radius Input */}
              <div className="space-y-1">
                  <div className="flex justify-between text-xs text-slate-500">
                      <span>圆曲线半径 (R)</span>
                      <span>{selectedRadius} m</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <input
                      type="range"
                      min="0"
                      max="10000" 
                      step="10"
                      value={selectedRadius}
                      onChange={(e) => onSelectedRadiusChange(Number(e.target.value))}
                      className={`flex-1 h-2 rounded-lg appearance-none cursor-pointer ${industryMode === IndustryMode.HIGHWAY ? 'bg-purple-200 accent-purple-600' : 'bg-blue-200 accent-blue-600'}`}
                    />
                    <input
                        type="number"
                        min="0"
                        value={selectedRadius}
                        onChange={(e) => onSelectedRadiusChange(Math.max(0, Number(e.target.value)))}
                        className="w-20 pl-2 pr-1 py-1 text-sm border border-slate-200 rounded text-right focus:outline-none"
                    />
                  </div>
              </div>

              {/* Spiral Input (Highway Only) */}
              {industryMode === IndustryMode.HIGHWAY && selectedSpiralLen !== null && (
                <div className="space-y-1 pt-2 border-t border-purple-200/50">
                    <div className="flex justify-between text-xs text-slate-500">
                        <span>缓和曲线长 (Ls)</span>
                        <span>{selectedSpiralLen} m</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <input
                        type="range"
                        min="0"
                        max="2000" 
                        step="10"
                        value={selectedSpiralLen}
                        onChange={(e) => onSelectedSpiralLenChange(Number(e.target.value))}
                        className="flex-1 h-2 bg-purple-200 rounded-lg appearance-none cursor-pointer accent-purple-600"
                        />
                        <input
                            type="number"
                            min="0"
                            value={selectedSpiralLen}
                            onChange={(e) => onSelectedSpiralLenChange(Math.max(0, Number(e.target.value)))}
                            className="w-20 pl-2 pr-1 py-1 text-sm border border-slate-200 rounded text-right focus:outline-none"
                        />
                    </div>
                </div>
              )}
            </div>
          ) : (
             <div className="p-4 rounded-xl border border-dashed border-slate-300 text-center text-slate-400 text-sm">
                在地图上选择一个控制点以编辑其参数。
             </div>
          )}

          {/* Default Config */}
          <div className="pt-4 border-t border-slate-100 space-y-3">
             <div className="space-y-1">
                 <div className="flex justify-between items-center">
                     <span className="text-xs font-medium text-slate-500">默认半径 (R)</span>
                     <span className="text-xs font-mono text-slate-400">{defaultRadius} m</span>
                 </div>
                 <input
                    type="range"
                    min="0"
                    max="10000" 
                    step="50"
                    value={defaultRadius}
                    onChange={(e) => setDefaultRadius(Number(e.target.value))}
                    className="w-full h-1 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-slate-400"
                  />
             </div>
             
             {industryMode === IndustryMode.HIGHWAY && (
                 <div className="space-y-1">
                     <div className="flex justify-between items-center">
                         <span className="text-xs font-medium text-slate-500">默认缓和曲线 (Ls)</span>
                         <span className="text-xs font-mono text-slate-400">{defaultSpiralLen} m</span>
                     </div>
                     <input
                        type="range"
                        min="0"
                        max="2000" 
                        step="10"
                        value={defaultSpiralLen}
                        onChange={(e) => setDefaultSpiralLen(Number(e.target.value))}
                        className="w-full h-1 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-slate-400"
                      />
                 </div>
             )}
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
              导出 CSV
            </button>
            <button 
                onClick={() => fileInputRef.current?.click()}
                className="flex items-center justify-center gap-2 p-3 rounded-lg border border-slate-200 hover:bg-slate-50 hover:border-slate-300 text-slate-700 text-sm font-medium transition-colors"
            >
              <Upload size={16} />
              导入 CSV
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
