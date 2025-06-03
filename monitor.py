import asyncio
import aiohttp
import logging
import signal
import sys
from database import DatabaseManager
from config import Config

class HelldiversMonitor:
    def __init__(self):
        self.config = Config()
        self.db_manager = DatabaseManager()
        self.running = False
        
        # 设置信号处理
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """处理停止信号"""
        logging.info(f"接收到信号 {signum}，准备停止监控...")
        self.running = False
    
    async def fetch_api_data(self):
        """获取API数据"""
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(self.config.API_URL) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logging.error(f"API请求失败: {response.status}")
                        return None
        except asyncio.TimeoutError:
            logging.error("API请求超时")
            return None
        except Exception as e:
            logging.error(f"获取API数据时出错: {e}")
            return None
    
    async def run_monitor(self):
        """运行监控循环"""
        self.running = True
        logging.info("开始监控Helldivers 2数据...")
        
        while self.running:
            try:
                data = await self.fetch_api_data()
                if data:
                    self.db_manager.store_api_data(data)
                    logging.info("数据获取并存储成功")
                else:
                    logging.warning("未能获取API数据")
                
                # 等待下次轮询
                for _ in range(self.config.POLL_INTERVAL):
                    if not self.running:
                        break
                    await asyncio.sleep(1)
                
            except Exception as e:
                logging.error(f"监控循环出错: {e}")
                await asyncio.sleep(60)  # 出错时等待1分钟后重试
        
        logging.info("监控服务已停止")
        self.db_manager.close()

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(Config.LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    monitor = HelldiversMonitor()
    asyncio.run(monitor.run_monitor())