import asyncio
import threading
import logging
import sys
import os
from monitor import HelldiversMonitor
from app import app
from config import Config

def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(Config.LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )

def run_flask_app():
    """在单独线程中运行Flask应用"""
    app.run(debug=False, host=Config.HOST, port=Config.PORT, use_reloader=False)

async def run_monitor():
    """运行数据监控"""
    monitor = HelldiversMonitor()
    await monitor.run_monitor()

def main():
    """主程序"""
    setup_logging()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "monitor":
            # 仅运行监控服务
            logging.info("启动数据监控服务...")
            asyncio.run(run_monitor())
        elif sys.argv[1] == "web":
            # 仅运行Web服务
            logging.info("启动Web服务...")
            app.run(debug=Config.DEBUG, host=Config.HOST, port=Config.PORT)
        else:
            print("用法: python run.py [monitor|web]")
            print("  monitor: 仅运行数据监控服务")
            print("  web: 仅运行Web服务")
            print("  无参数: 同时运行监控和Web服务")
    else:
        # 同时运行监控和Web服务
        logging.info("启动完整的Helldivers 2监控系统...")
        logging.info(f"Web界面: http://localhost:{Config.PORT}")
        
        # 启动Flask应用线程
        flask_thread = threading.Thread(target=run_flask_app, daemon=True)
        flask_thread.start()
        
        # 启动数据监控
        try:
            asyncio.run(run_monitor())
        except KeyboardInterrupt:
            logging.info("程序被用户中断")
        except Exception as e:
            logging.error(f"程序运行出错: {e}")

if __name__ == "__main__":
    main()