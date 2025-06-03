import sqlite3
import json
import time
import logging
from typing import Dict, List, Any, Optional
from config import Config

class DatabaseManager:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or Config.DATABASE_PATH
        self.connection = None
        self.setup_database()
    
    def get_connection(self):
        """获取数据库连接"""
        if not self.connection:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
        return self.connection
    
    def setup_database(self):
        """初始化数据库结构"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 主要订单表（不重复存储同一订单）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS major_orders (
                order_id INTEGER PRIMARY KEY,
                title TEXT,
                brief TEXT,
                task_type INTEGER,
                target_value INTEGER,
                created_at INTEGER,
                expires_at INTEGER
            )
        ''')
        
        # 主要订单进度历史表（仅记录进度变化）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS major_orders_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER,
                order_id INTEGER,
                current_progress INTEGER,
                progress_percentage REAL,
                expires_in INTEGER,
                FOREIGN KEY (order_id) REFERENCES major_orders (order_id)
            )
        ''')
        
        # 星球信息表（静态信息）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS planets_info (
                planet_index INTEGER PRIMARY KEY,
                sector INTEGER,
                max_health INTEGER,
                initial_owner INTEGER,
                position_x REAL,
                position_y REAL
            )
        ''')
        
        # 星球状态历史表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS planet_status_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER,
                planet_index INTEGER,
                owner INTEGER,
                health INTEGER,
                players INTEGER,
                regen_per_second REAL,
                FOREIGN KEY (planet_index) REFERENCES planets_info (planet_index)
            )
        ''')
        
        # 星球地区信息表（静态信息）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS planet_regions_info (
                planet_index INTEGER,
                region_index INTEGER,
                max_health INTEGER,
                region_size INTEGER,
                PRIMARY KEY (planet_index, region_index),
                FOREIGN KEY (planet_index) REFERENCES planets_info (planet_index)
            )
        ''')
        
        # 星球地区状态历史表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS planet_regions_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER,
                planet_index INTEGER,
                region_index INTEGER,
                owner INTEGER,
                health INTEGER,
                regen_per_second REAL,
                is_available BOOLEAN,
                players INTEGER,
                FOREIGN KEY (planet_index, region_index) REFERENCES planet_regions_info (planet_index, region_index)
            )
        ''')
        
        # 战争状态历史表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS war_status_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER,
                war_id INTEGER,
                war_time INTEGER,
                impact_multiplier REAL,
                total_planets INTEGER,
                super_earth_planets INTEGER,
                enemy_planets INTEGER,
                total_players INTEGER
            )
        ''')
        
        # 战争统计历史表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS war_stats_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER,
                missions_won INTEGER,
                missions_lost INTEGER,
                mission_success_rate REAL,
                bug_kills INTEGER,
                automaton_kills INTEGER,
                illuminate_kills INTEGER,
                total_deaths INTEGER,
                accuracy REAL
            )
        ''')
        
        # 全局资源历史表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS global_resources_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER,
                resource_id INTEGER,
                current_value INTEGER,
                max_value INTEGER,
                percentage REAL
            )
        ''')
        
        # 新闻表（不重复存储，支持内容更新）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news (
                news_id INTEGER PRIMARY KEY,
                published INTEGER,
                type INTEGER,
                tag_ids TEXT,
                message TEXT,
                stored_at INTEGER,
                updated_at INTEGER
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_major_orders_progress_timestamp ON major_orders_progress(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_planet_status_timestamp ON planet_status_history(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_planet_regions_timestamp ON planet_regions_history(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_war_status_timestamp ON war_status_history(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_war_stats_timestamp ON war_stats_history(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_planet_status_planet ON planet_status_history(planet_index, timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_planet_regions_planet ON planet_regions_history(planet_index, region_index, timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_published ON news(published)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_type ON news(type)')
        
        conn.commit()
        logging.info("数据库初始化完成")
    
    def store_api_data(self, data: Dict[str, Any]):
        """存储API数据到数据库"""
        timestamp = int(time.time())
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 存储星球信息（仅在第一次时存储）
            if 'warInfo' in data and 'planetInfos' in data['warInfo']:
                for planet in data['warInfo']['planetInfos']:
                    cursor.execute('''
                        INSERT OR IGNORE INTO planets_info 
                        (planet_index, sector, max_health, initial_owner, position_x, position_y)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        planet.get('index'),
                        planet.get('sector'),
                        planet.get('maxHealth'),
                        planet.get('initialOwner'),
                        planet.get('position', {}).get('x', 0),
                        planet.get('position', {}).get('y', 0)
                    ))
            
            # 存储星球地区信息（仅在第一次时存储）
            if 'warInfo' in data and 'planetRegions' in data['warInfo']:
                for region in data['warInfo']['planetRegions']:
                    cursor.execute('''
                        INSERT OR IGNORE INTO planet_regions_info 
                        (planet_index, region_index, max_health, region_size)
                        VALUES (?, ?, ?, ?)
                    ''', (
                        region.get('planetIndex'),
                        region.get('regionIndex'),
                        region.get('maxHealth'),
                        region.get('regionSize')
                    ))
            
            # 存储主要订单（避免重复）
            if 'majorOrders' in data:
                for order in data['majorOrders']:
                    order_id = order.get('id32')
                    setting = order.get('setting', {})
                    tasks = setting.get('tasks', [])
                    
                    # 获取目标值
                    target_value = 0
                    if tasks and len(tasks) > 0:
                        values = tasks[0].get('values', [])
                        if len(values) > 2:
                            target_value = values[2]
                    
                    # 插入或忽略订单基本信息
                    cursor.execute('''
                        INSERT OR IGNORE INTO major_orders 
                        (order_id, title, brief, task_type, target_value, created_at, expires_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        order_id,
                        setting.get('overrideTitle', ''),
                        setting.get('overrideBrief', ''),
                        setting.get('type', 0),
                        target_value,
                        timestamp,
                        timestamp + order.get('expiresIn', 0)
                    ))
                    
                    # 记录进度变化
                    progress = order.get('progress', [])
                    current_progress = progress[0] if progress else 0
                    progress_percentage = (current_progress / target_value * 100) if target_value > 0 else 0
                    
                    cursor.execute('''
                        INSERT INTO major_orders_progress 
                        (timestamp, order_id, current_progress, progress_percentage, expires_in)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        timestamp,
                        order_id,
                        current_progress,
                        progress_percentage,
                        order.get('expiresIn', 0)
                    ))
            
            # 存储战争状态数据
            if 'warStatus' in data:
                war_status = data['warStatus']
                planet_status = war_status.get('planetStatus', [])
                
                # 统计星球控制情况
                super_earth_planets = sum(1 for p in planet_status if p.get('owner') == 1)
                enemy_planets = len(planet_status) - super_earth_planets
                total_players = sum(p.get('players', 0) for p in planet_status)
                
                cursor.execute('''
                    INSERT INTO war_status_history 
                    (timestamp, war_id, war_time, impact_multiplier, total_planets, 
                     super_earth_planets, enemy_planets, total_players)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    timestamp,
                    war_status.get('warId'),
                    war_status.get('time'),
                    war_status.get('impactMultiplier'),
                    len(planet_status),
                    super_earth_planets,
                    enemy_planets,
                    total_players
                ))
                
                # 存储各星球状态
                for planet in planet_status:
                    cursor.execute('''
                        INSERT INTO planet_status_history 
                        (timestamp, planet_index, owner, health, players, regen_per_second)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        timestamp,
                        planet.get('index'),
                        planet.get('owner'),
                        planet.get('health'),
                        planet.get('players'),
                        planet.get('regenPerSecond')
                    ))
                
                # 存储星球地区状态
                if 'planetRegions' in war_status:
                    for region in war_status['planetRegions']:
                        cursor.execute('''
                            INSERT INTO planet_regions_history 
                            (timestamp, planet_index, region_index, owner, health, regen_per_second, 
                             is_available, players)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            timestamp,
                            region.get('planetIndex'),
                            region.get('regionIndex'),
                            region.get('owner'),
                            region.get('health'),
                            region.get('regerPerSecond'),
                            region.get('isAvailable'),
                            region.get('players')
                        ))
                
                # 存储全局资源
                if 'globalResources' in war_status:
                    for resource in war_status['globalResources']:
                        current = resource.get('currentValue', 0)
                        max_val = resource.get('maxValue', 1)
                        percentage = (current / max_val * 100) if max_val > 0 else 0
                        
                        cursor.execute('''
                            INSERT INTO global_resources_history 
                            (timestamp, resource_id, current_value, max_value, percentage)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (
                            timestamp,
                            resource.get('id32'),
                            current,
                            max_val,
                            percentage
                        ))
            
            # 存储战争统计数据
            if 'warStats' in data and 'galaxy_stats' in data['warStats']:
                stats = data['warStats']['galaxy_stats']
                cursor.execute('''
                    INSERT INTO war_stats_history 
                    (timestamp, missions_won, missions_lost, mission_success_rate,
                     bug_kills, automaton_kills, illuminate_kills, total_deaths, accuracy)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    timestamp,
                    stats.get('missionsWon'),
                    stats.get('missionsLost'),
                    stats.get('missionSuccessRate'),
                    stats.get('bugKills'),
                    stats.get('automatonKills'),
                    stats.get('illuminateKills'),
                    stats.get('deaths'),
                    stats.get('accuracy')
                ))
            
            # 存储新闻数据（支持内容更新）
            if 'news' in data and isinstance(data['news'], list):
                new_news_count = 0
                updated_news_count = 0
                
                for news_item in data['news']:
                    news_id = news_item.get('id')
                    if news_id is None:
                        logging.warning(f"新闻项缺少ID，跳过: {news_item}")
                        continue
                    
                    # 获取新闻内容，确保不为None
                    message = news_item.get('message')
                    if message is None:
                        message = ''  # 将None转换为空字符串
                        logging.warning(f"新闻ID {news_id} 的message为None，设置为空字符串")
                    
                    published = news_item.get('published', 0)
                    news_type = news_item.get('type', 0)
                    tag_ids = json.dumps(news_item.get('tagIds', []))
                    
                    # 检查是否已存在该新闻
                    cursor.execute('SELECT message FROM news WHERE news_id = ?', (news_id,))
                    existing_row = cursor.fetchone()
                    
                    if existing_row is None:
                        # 新闻不存在，插入新记录
                        cursor.execute('''
                            INSERT INTO news 
                            (news_id, published, type, tag_ids, message, stored_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            news_id,
                            published,
                            news_type,
                            tag_ids,
                            message,
                            timestamp,
                            timestamp
                        ))
                        new_news_count += 1
                        logging.info(f"新增新闻: ID={news_id}, message长度={len(message)}")
                        
                    else:
                        # 新闻已存在，检查内容是否有变化
                        existing_message = existing_row[0] or ''  # 处理可能的None值
                        
                        if existing_message != message:
                            # 内容有变化，更新记录
                            cursor.execute('''
                                UPDATE news 
                                SET published = ?, type = ?, tag_ids = ?, message = ?, updated_at = ?
                                WHERE news_id = ?
                            ''', (
                                published,
                                news_type,
                                tag_ids,
                                message,
                                timestamp,
                                news_id
                            ))
                            updated_news_count += 1
                            logging.info(f"更新新闻: ID={news_id}, 旧消息长度={len(existing_message)}, 新消息长度={len(message)}")
                
                if new_news_count > 0 or updated_news_count > 0:
                    logging.info(f"新闻处理完成: 新增 {new_news_count} 条，更新 {updated_news_count} 条")
            
            conn.commit()
            logging.info(f"数据已存储，时间戳: {timestamp}")
            
        except Exception as e:
            logging.error(f"存储数据时出错: {e}")
            conn.rollback()
            raise
    
    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            self.connection = None