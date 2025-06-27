import tensorflow as tf
from tensorflow.keras import layers
import numpy as np

#2. 深度学习预测实现逻辑
#2.1 用户行为序列建模
class UserBehaviorLSTM:
    def __init__(self, sequence_length=50, feature_dim=20):
        self.sequence_length = sequence_length
        self.feature_dim = feature_dim
        self.model = self.build_model()
    
    def build_model(self):
        """构建LSTM模型"""
        model = tf.keras.Sequential([
            layers.LSTM(128, return_sequences=True, input_shape=(self.sequence_length, self.feature_dim)),
            layers.Dropout(0.2),
            layers.LSTM(64, return_sequences=False),
            layers.Dropout(0.2),
            layers.Dense(32, activation='relu'),
            layers.Dense(16, activation='relu'),
            # 多任务输出
            layers.Dense(self.feature_dim, activation='sigmoid', name='next_action'),
        ])
        
        model.compile(
            optimizer='adam',
            loss='mse',
            metrics=['mae']
        )
        return model
    
    def prepare_features(self, user_actions: list) -> np.ndarray:
        """准备特征数据"""
        features = []
        for action in user_actions:
            feature_vector = [
                action['zoom'] / 22.0,  # 归一化缩放级别
                action['center_x'] / 360.0 + 0.5,  # 归一化经度
                action['center_y'] / 180.0 + 0.5,  # 归一化纬度
                action['bounds_width'] / 360.0,    # 归一化边界宽度
                action['bounds_height'] / 180.0,   # 归一化边界高度
                action['scene_id'] / 1000.0,       # 归一化场景ID
                action['layer_count'] / 20.0,      # 归一化图层数
                action['time_hour'] / 24.0,        # 归一化小时
                action['time_weekday'] / 7.0,      # 归一化星期
                action['session_duration'] / 3600.0, # 归一化会话时长
                # 更多特征...
            ]
            features.append(feature_vector)
        
        return np.array(features)
    
    def predict_next_behavior(self, user_sequence: list) -> dict:
        """预测下一步行为"""
        if len(user_sequence) < self.sequence_length:
            # 填充序列
            padding = [user_sequence[0]] * (self.sequence_length - len(user_sequence))
            user_sequence = padding + user_sequence
        
        features = self.prepare_features(user_sequence[-self.sequence_length:])
        features = features.reshape(1, self.sequence_length, self.feature_dim)
        
        prediction = self.model.predict(features)[0]
        
        return {
            'predicted_zoom': int(prediction[0] * 22),
            'predicted_center_x': (prediction[1] - 0.5) * 360,
            'predicted_center_y': (prediction[2] - 0.5) * 180,
            'predicted_bounds_width': prediction[3] * 360,
            'predicted_bounds_height': prediction[4] * 180,
            'confidence': float(np.mean(prediction))
        }
#2.2 时空轨迹预测
class SpatioTemporalPredictor:
    def __init__(self):
        self.gru_model = self.build_gru_model()
        self.cnn_model = self.build_cnn_model()
    
    def build_gru_model(self):
        """构建GRU时序模型"""
        inputs = layers.Input(shape=(None, 6))  # [x, y, zoom, time, scene, action]
        
        # 双向GRU
        gru_forward = layers.GRU(64, return_sequences=True)(inputs)
        gru_backward = layers.GRU(64, return_sequences=True, go_backwards=True)(inputs)
        gru_merged = layers.Concatenate()([gru_forward, gru_backward])
        
        # 注意力机制
        attention = layers.MultiHeadAttention(num_heads=4, key_dim=32)(gru_merged, gru_merged)
        
        # 输出层
        outputs = layers.Dense(3, activation='linear')(attention[:, -1, :])  # [next_x, next_y, next_zoom]
        
        model = tf.keras.Model(inputs=inputs, outputs=outputs)
        model.compile(optimizer='adam', loss='mse')
        
        return model
    
    def build_cnn_model(self):
        """构建CNN空间模型"""
        # 用于处理空间网格数据
        inputs = layers.Input(shape=(32, 32, 3))  # 网格化的空间访问热力图
        
        conv1 = layers.Conv2D(32, (3, 3), activation='relu')(inputs)
        pool1 = layers.MaxPooling2D((2, 2))(conv1)
        
        conv2 = layers.Conv2D(64, (3, 3), activation='relu')(pool1)
        pool2 = layers.MaxPooling2D((2, 2))(conv2)
        
        conv3 = layers.Conv2D(128, (3, 3), activation='relu')(pool2)
        
        flatten = layers.Flatten()(conv3)
        dense1 = layers.Dense(128, activation='relu')(flatten)
        outputs = layers.Dense(4, activation='sigmoid')(dense1)  # [热点概率分布]
        
        model = tf.keras.Model(inputs=inputs, outputs=outputs)
        model.compile(optimizer='adam', loss='binary_crossentropy')
        
        return model
    
#2.3协同过滤预测
class CollaborativeFilteringPredictor:
    def __init__(self):
        self.user_similarity_model = self.build_similarity_model()
        self.matrix_factorization_model = self.build_mf_model()
    
    def build_similarity_model(self):
        """构建用户相似度模型"""
        from sklearn.metrics.pairwise import cosine_similarity
        from sklearn.feature_extraction.text import TfidfVectorizer
        
        return {
            'vectorizer': TfidfVectorizer(),
            'similarity_func': cosine_similarity
        }
    
    def build_mf_model(self):
        """构建矩阵分解模型"""
        from sklearn.decomposition import NMF
        
        return NMF(n_components=50, random_state=42)
    
    def find_similar_users(self, user_id: str, user_features: dict) -> list:
        """查找相似用户"""
        # 计算用户特征向量
        user_vector = self.encode_user_features(user_features)
        
        # 查找最相似的用户
        all_users = self.get_all_user_vectors()
        similarities = cosine_similarity([user_vector], all_users)[0]
        
        # 返回前N个最相似的用户
        similar_indices = np.argsort(similarities)[::-1][1:11]  # 前10个
        return similar_indices
    
    def predict_preferences(self, user_id: str, similar_users: list) -> dict:
        """基于相似用户预测偏好"""
        similar_behaviors = []
        for similar_user in similar_users:
            behaviors = self.get_user_behaviors(similar_user)
            similar_behaviors.extend(behaviors)
        
        # 聚合分析
        preferences = {
            'preferred_scenes': self.aggregate_scene_preferences(similar_behaviors),
            'preferred_zoom_levels': self.aggregate_zoom_preferences(similar_behaviors),
            'preferred_areas': self.aggregate_spatial_preferences(similar_behaviors),
            'preferred_layers': self.aggregate_layer_preferences(similar_behaviors)
        }
        
        return preferences