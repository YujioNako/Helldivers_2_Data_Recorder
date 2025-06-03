import os

class Config:
    # API配置
    API_URL = "https://helldiverscompanion.com/api/hell-divers-2-api/get-all-api-data"
    POLL_INTERVAL = 900  # 15分钟轮询一次
    
    # 数据库配置
    DATABASE_PATH = "helldivers_data.db"
    
    # Flask配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'helldivers-secret-key'
    DEBUG = True
    USE_RELOADER = True
    HOST = '0.0.0.0'
    PORT = 5555
    
    # 日志配置
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'helldivers_monitor.log'
    
    # 数据限制配置
    DATA_LIMITS = {
        'default_hours': 24,
        'max_data_points': 100,
        'chart_data_points': 50,
        'max_chart_datasets': 10,
        'news_default_limit': 20
    }
