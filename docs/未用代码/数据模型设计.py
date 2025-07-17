#4.1用户行为数据模型
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class UserBehavior(Base):
    __tablename__ = 'user_behaviors'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), index=True)
    session_id = Column(String(100), index=True)
    timestamp = Column(DateTime, index=True)
    action_type = Column(String(50))  # 'zoom', 'pan', 'scene_switch', 'layer_toggle'
    
    # 地理信息
    center_lng = Column(Float)
    center_lat = Column(Float)
    zoom_level = Column(Integer)
    bounds = Column(JSON)
    
    # 场景信息
    scene_id = Column(String(50), index=True)
    layer_ids = Column(JSON)
    
    # 上下文信息
    device_type = Column(String(20))
    network_type = Column(String(20))
    time_spent = Column(Float)
    
    # 额外元数据
    metadata = Column(JSON)

class PredictionCache(Base):
    __tablename__ = 'prediction_cache'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), index=True)
    prediction_type = Column(String(50))  # 'quick', 'deep'
    context_hash = Column(String(64), index=True)
    predictions = Column(JSON)
    confidence_score = Column(Float)
    created_at = Column(DateTime)
    expires_at = Column(DateTime)

#4.2Redis缓存结构
class CacheKeys:
    # 用户行为序列
    USER_BEHAVIOR_SEQ = "user_behavior:{user_id}"
    
    # 快速预测结果
    QUICK_PREDICTION = "quick_pred:{user_id}:{context_hash}"
    
    # 深度预测结果
    DEEP_PREDICTION = "deep_pred:{user_id}:{model_version}"
    
    # 全局热点
    GLOBAL_HOTSPOTS = "global_hotspots:{zoom_level}"
    
    # 用户热点
    USER_HOTSPOTS = "user_hotspots:{user_id}"
    
    # 相似用户群
    SIMILAR_USERS = "similar_users:{user_id}"

#5.1接口
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel

app = FastAPI()

class PredictionRequest(BaseModel):
    user_id: str
    current_context: dict
    prediction_type: str = "quick"

class PredictionResponse(BaseModel):
    tiles: list
    confidence: float
    cache_duration: int

@app.post("/api/predict/quick")
async def quick_prediction(request: PredictionRequest) -> PredictionResponse:
    """快速预测接口"""
    service = QuickPredictionService()
    tiles = service.predict_next_tiles(request.user_id, request.current_context)
    
    return PredictionResponse(
        tiles=tiles,
        confidence=0.85,
        cache_duration=300  # 5分钟
    )

@app.post("/api/predict/deep")
async def deep_prediction(request: PredictionRequest, background_tasks: BackgroundTasks) -> PredictionResponse:
    """深度预测接口"""
    service = DeepPredictionService()
    
    # 异步启动深度预测
    background_tasks.add_task(service.train_user_model, request.user_id)
    
    # 返回现有预测结果
    tiles = service.get_cached_predictions(request.user_id, request.current_context)
    
    return PredictionResponse(
        tiles=tiles,
        confidence=0.92,
        cache_duration=1800  # 30分钟
    )

class BehaviorReport(BaseModel):
    user_id: str
    actions: list
    timestamp: datetime

@app.post("/api/behavior/report")
async def report_behavior(report: BehaviorReport, background_tasks: BackgroundTasks):
    """用户行为上报"""
    # 存储行为数据
    behavior_service = BehaviorService()
    background_tasks.add_task(behavior_service.store_behaviors, report)
    
    # 触发增量学习
    if len(report.actions) > 10:  # 足够的行为数据
        background_tasks.add_task(behavior_service.incremental_training, report.user_id)
    
    return {"status": "success"}

class ModelOptimizer:
    def __init__(self):
        self.model_cache = {}
        self.feature_cache = LRUCache(maxsize=1000)
    
    def optimize_inference(self, model, input_data):
        """优化推理性能"""
        # 1. 量化模型
        if hasattr(model, 'quantize'):
            model = model.quantize()
        
        # 2. 批处理推理
        if len(input_data) > 1:
            return model.predict_batch(input_data)
        
        # 3. 缓存特征
        feature_hash = hash(str(input_data))
        if feature_hash in self.feature_cache:
            return self.feature_cache[feature_hash]
        
        result = model.predict(input_data)
        self.feature_cache[feature_hash] = result
        
        return result