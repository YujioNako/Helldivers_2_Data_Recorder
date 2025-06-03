from flask import Flask, jsonify, render_template, request
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from database import DatabaseManager
from config import Config
import time

app = Flask(__name__)
app.config.from_object(Config)

# 初始化数据库管理器
db_manager = DatabaseManager()

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# 数据限制配置
DATA_LIMITS = {
    'default_hours': 24,
    'max_data_points': 100,
    'chart_data_points': 50,
    'news_default_limit': 20,
    'news_max_limit': 100
}

@app.route('/')
def dashboard():
    """主页面"""
    return render_template('dashboard.html')

@app.route('/src/<path:fileName>')
def serve_src_file(fileName):
    """配套文件"""
    return render_template('src/' + fileName)

@app.route('/api/war-status-trend')
def war_status_trend():
    """获取战争状态趋势数据（限制数据点）"""
    try:
        conn = get_db_connection()
        hours = request.args.get('hours', DATA_LIMITS['default_hours'], type=int)
        limit = request.args.get('limit', DATA_LIMITS['chart_data_points'], type=int)
        
        since = int((datetime.now() - timedelta(hours=hours)).timestamp())
        
        # 使用子查询限制数据点数量
        data = conn.execute('''
            SELECT * FROM (
                SELECT timestamp, super_earth_planets, enemy_planets, total_players, impact_multiplier
                FROM war_status_history 
                WHERE timestamp > ?
                ORDER BY timestamp DESC
                LIMIT ?
            ) ORDER BY timestamp ASC
        ''', (since, limit)).fetchall()
        
        conn.close()
        return jsonify([dict(row) for row in data])
    except Exception as e:
        logging.error(f"获取战争状态趋势失败: {e}")
        return jsonify({"error": "Failed to fetch war status trend"}), 500

@app.route('/api/major-orders-progress')
def major_orders_progress():
    """获取主要订单进度数据（去重并限制）"""
    try:
        conn = get_db_connection()
        limit = request.args.get('limit', DATA_LIMITS['max_data_points'], type=int)
        
        # 获取活跃订单的最新进度
        data = conn.execute('''
            SELECT 
                mo.order_id,
                mo.title,
                mo.brief,
                mo.target_value,
                mop.timestamp,
                mop.current_progress,
                mop.progress_percentage,
                mop.expires_in
            FROM major_orders mo
            JOIN major_orders_progress mop ON mo.order_id = mop.order_id
            WHERE mop.expires_in > 0
            ORDER BY mop.timestamp DESC
            LIMIT ?
        ''', (limit,)).fetchall()
        
        conn.close()
        
        result = []
        seen_orders = set()
        for row in data:
            order_id = row[0]
            if order_id not in seen_orders:
                seen_orders.add(order_id)
                result.append({
                    'order_id': order_id,
                    'title': row[1],
                    'brief': row[2],
                    'target_value': row[3],
                    'timestamp': row[4],
                    'current_progress': row[5],
                    'progress_percentage': row[6],
                    'expires_in': row[7]
                })
        
        return jsonify(result)
    except Exception as e:
        logging.error(f"获取主要订单进度失败: {e}")
        return jsonify({"error": "Failed to fetch major orders progress"}), 500

@app.route('/api/major-order-history/<int:order_id>')
def major_order_history(order_id):
    """获取特定订单的历史进度"""
    try:
        conn = get_db_connection()
        limit = request.args.get('limit', DATA_LIMITS['chart_data_points'], type=int)
        
        data = conn.execute('''
            SELECT timestamp, current_progress, progress_percentage, expires_in
            FROM major_orders_progress 
            WHERE order_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (order_id, limit)).fetchall()
        
        conn.close()
        return jsonify([dict(row) for row in reversed(data)])
    except Exception as e:
        logging.error(f"获取订单历史失败: {e}")
        return jsonify({"error": "Failed to fetch order history"}), 500

@app.route('/api/war-stats-trend')
def war_stats_trend():
    """获取战争统计趋势（限制数据点）"""
    try:
        conn = get_db_connection()
        hours = request.args.get('hours', DATA_LIMITS['default_hours'], type=int)
        limit = request.args.get('limit', DATA_LIMITS['chart_data_points'], type=int)
        
        since = int((datetime.now() - timedelta(hours=hours)).timestamp())
        
        data = conn.execute('''
            SELECT * FROM (
                SELECT timestamp, missions_won, missions_lost, mission_success_rate,
                       bug_kills, automaton_kills, illuminate_kills, total_deaths, accuracy
                FROM war_stats_history 
                WHERE timestamp > ?
                ORDER BY timestamp DESC
                LIMIT ?
            ) ORDER BY timestamp ASC
        ''', (since, limit)).fetchall()
        
        conn.close()
        return jsonify([dict(row) for row in data])
    except Exception as e:
        logging.error(f"获取战争统计趋势失败: {e}")
        return jsonify({"error": "Failed to fetch war stats trend"}), 500

@app.route('/api/planets-by-sector')
def planets_by_sector():
    """按sector分类获取星球数据"""
    try:
        conn = get_db_connection()
        
        # 获取最新的星球状态数据，按sector分组
        latest_timestamp = conn.execute(
            'SELECT MAX(timestamp) FROM planet_status_history'
        ).fetchone()[0]
        
        if not latest_timestamp:
            return jsonify({"error": "No planet data available"}), 404
        
        planets_data = conn.execute('''
            SELECT 
                pi.planet_index,
                pi.sector,
                pi.max_health,
                pi.position_x,
                pi.position_y,
                psh.owner,
                psh.health,
                psh.players,
                psh.regen_per_second
            FROM planets_info pi
            JOIN planet_status_history psh ON pi.planet_index = psh.planet_index
            WHERE psh.timestamp = ?
            ORDER BY pi.sector, pi.planet_index
        ''', (latest_timestamp,)).fetchall()
        
        conn.close()
        
        # 按sector分组
        sectors = {}
        planet_count = 0
        for row in planets_data:
            sector = row[1]
            if sector not in sectors:
                sectors[sector] = []
            
            sectors[sector].append({
                'index': row[0],
                'sector': sector,
                'max_health': row[2],
                'position': {'x': row[3], 'y': row[4]},
                'owner': row[5],
                'health': row[6],
                'players': row[7],
                'regen_per_second': row[8]
            })
            planet_count = planet_count + 1
        
        return jsonify({
            'total': planet_count,
            'sectors': sectors,
            'timestamp': latest_timestamp
        })
        
    except Exception as e:
        logging.error(f"获取分sector星球数据失败: {e}")
        return jsonify({"error": "Failed to fetch planets by sector"}), 500

@app.route('/api/planet-details/<int:planet_index>')
def planet_details(planet_index):
    """获取特定星球的详细信息"""
    try:
        conn = get_db_connection()
        
        # 获取星球基本信息
        planet_info = conn.execute('''
            SELECT planet_index, sector, max_health, position_x, position_y
            FROM planets_info WHERE planet_index = ?
        ''', (planet_index,)).fetchone()
        
        if not planet_info:
            return jsonify({"error": "Planet not found"}), 404
        
        # 获取最新状态
        latest_status = conn.execute('''
            SELECT owner, health, players, regen_per_second, timestamp
            FROM planet_status_history 
            WHERE planet_index = ?
            ORDER BY timestamp DESC
            LIMIT 1
        ''', (planet_index,)).fetchone()
        
        # 获取地区信息和最新状态
        regions_data = conn.execute('''
            SELECT 
                pri.region_index,
                pri.max_health,
                pri.region_size,
                prh.owner,
                prh.health,
                prh.regen_per_second,
                prh.is_available,
                prh.players
            FROM planet_regions_info pri
            LEFT JOIN planet_regions_history prh ON 
                pri.planet_index = prh.planet_index AND 
                pri.region_index = prh.region_index
            WHERE pri.planet_index = ? AND 
                  prh.timestamp = (
                      SELECT MAX(timestamp) FROM planet_regions_history 
                      WHERE planet_index = ? AND region_index = pri.region_index
                  )
            ORDER BY pri.region_index
        ''', (planet_index, planet_index)).fetchall()
        
        conn.close()
        
        regions = []
        for row in regions_data:
            regions.append({
                'regionIndex': row[0],
                'maxHealth': row[1],
                'regionSize': row[2],
                'owner': row[3] if row[3] is not None else 1,
                'health': row[4] if row[4] is not None else row[1],
                'regerPerSecond': row[5] if row[5] is not None else 0,
                'isAvailable': bool(row[6]) if row[6] is not None else True,
                'players': row[7] if row[7] is not None else 0
            })
        
        return jsonify({
            'planet': {
                'index': planet_info[0],
                'sector': planet_info[1],
                'max_health': planet_info[2],
                'position': {'x': planet_info[3], 'y': planet_info[4]},
                'owner': latest_status[0] if latest_status else 1,
                'health': latest_status[1] if latest_status else planet_info[2],
                'players': latest_status[2] if latest_status else 0,
                'regen_per_second': latest_status[3] if latest_status else 0
            },
            'regions': regions
        })
        
    except Exception as e:
        logging.error(f"获取星球详情失败: {e}")
        return jsonify({"error": "Failed to fetch planet details"}), 500

@app.route('/api/planet-health-history/<int:planet_index>')
def planet_health_history(planet_index):
    """获取星球生命值历史（限制数据点）"""
    try:
        conn = get_db_connection()
        hours = request.args.get('hours', 24, type=int)
        limit = request.args.get('limit', DATA_LIMITS['chart_data_points'], type=int)
        
        since = int((datetime.now() - timedelta(hours=hours)).timestamp())
        
        data = conn.execute('''
            SELECT * FROM (
                SELECT timestamp, health, players, regen_per_second, owner
                FROM planet_status_history 
                WHERE planet_index = ? AND timestamp > ?
                ORDER BY timestamp DESC
                LIMIT ?
            ) ORDER BY timestamp ASC
        ''', (planet_index, since, limit)).fetchall()
        
        conn.close()
        return jsonify([dict(row) for row in data])
    except Exception as e:
        logging.error(f"获取星球生命值历史失败: {e}")
        return jsonify({"error": "Failed to fetch planet health history"}), 500

@app.route('/api/region-health-history/<int:planet_index>/<int:region_index>')
def region_health_history(planet_index, region_index):
    """获取地区生命值历史（限制数据点）"""
    try:
        conn = get_db_connection()
        hours = request.args.get('hours', 24, type=int)
        limit = request.args.get('limit', DATA_LIMITS['chart_data_points'], type=int)
        
        since = int((datetime.now() - timedelta(hours=hours)).timestamp())
        
        data = conn.execute('''
            SELECT * FROM (
                SELECT timestamp, health, regen_per_second, players, owner
                FROM planet_regions_history 
                WHERE planet_index = ? AND region_index = ? AND timestamp > ?
                ORDER BY timestamp DESC
                LIMIT ?
            ) ORDER BY timestamp ASC
        ''', (planet_index, region_index, since, limit)).fetchall()
        
        conn.close()
        return jsonify([dict(row) for row in data])
    except Exception as e:
        logging.error(f"获取地区生命值历史失败: {e}")
        return jsonify({"error": "Failed to fetch region health history"}), 500

@app.route('/api/global-resources-trend')
def global_resources_trend():
    """获取全局资源趋势（限制数据点）"""
    try:
        conn = get_db_connection()
        hours = request.args.get('hours', DATA_LIMITS['default_hours'], type=int)
        limit = request.args.get('limit', DATA_LIMITS['chart_data_points'], type=int)
        
        since = int((datetime.now() - timedelta(hours=hours)).timestamp())
        
        data = conn.execute('''
            SELECT * FROM (
                SELECT timestamp, resource_id, current_value, max_value, percentage
                FROM global_resources_history 
                WHERE timestamp > ?
                ORDER BY timestamp DESC
                LIMIT ?
            ) ORDER BY timestamp ASC
        ''', (since, limit)).fetchall()
        
        conn.close()
        return jsonify([dict(row) for row in data])
    except Exception as e:
        logging.error(f"获取全局资源趋势失败: {e}")
        return jsonify({"error": "Failed to fetch global resources trend"}), 500
        
@app.route('/api/major-order-progress-history/<int:order_id>')
def major_order_progress_history(order_id):
    """获取特定主要订单的进度历史曲线"""
    try:
        conn = get_db_connection()
        hours = request.args.get('hours', 48, type=int)  # 默认48小时
        limit = request.args.get('limit', DATA_LIMITS['chart_data_points'], type=int)
        
        since = int((datetime.now() - timedelta(hours=hours)).timestamp())
        
        # 获取订单基本信息
        order_info = conn.execute('''
            SELECT order_id, title, brief, target_value
            FROM major_orders 
            WHERE order_id = ?
        ''', (order_id,)).fetchone()
        
        if not order_info:
            return jsonify({"error": "Order not found"}), 404
        
        # 获取进度历史数据
        progress_data = conn.execute('''
            SELECT * FROM (
                SELECT timestamp, current_progress, progress_percentage, expires_in
                FROM major_orders_progress 
                WHERE order_id = ? AND timestamp > ?
                ORDER BY timestamp DESC
                LIMIT ?
            ) ORDER BY timestamp ASC
        ''', (order_id, since, limit)).fetchall()
        
        conn.close()
        
        return jsonify({
            'order_info': {
                'order_id': order_info[0],
                'title': order_info[1],
                'brief': order_info[2],
                'target_value': order_info[3]
            },
            'progress_history': [dict(row) for row in progress_data]
        })
        
    except Exception as e:
        logging.error(f"获取订单进度历史失败: {e}")
        return jsonify({"error": "Failed to fetch order progress history"}), 500

@app.route('/api/all-major-orders-summary')
def all_major_orders_summary():
    """获取所有活跃订单的摘要信息"""
    try:
        conn = get_db_connection()
        
        # 获取所有有进度记录的订单
        orders_data = conn.execute('''
            SELECT 
                mo.order_id,
                mo.title,
                mo.brief,
                mo.target_value,
                mop_latest.current_progress,
                mop_latest.progress_percentage,
                mop_latest.expires_in,
                mop_latest.timestamp as last_update,
                mop_first.timestamp as first_seen
            FROM major_orders mo
            JOIN (
                SELECT order_id, current_progress, progress_percentage, expires_in, timestamp,
                       ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY timestamp DESC) as rn
                FROM major_orders_progress
            ) mop_latest ON mo.order_id = mop_latest.order_id AND mop_latest.rn = 1
            JOIN (
                SELECT order_id, timestamp,
                       ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY timestamp ASC) as rn
                FROM major_orders_progress
            ) mop_first ON mo.order_id = mop_first.order_id AND mop_first.rn = 1
            WHERE mop_latest.expires_in > 0
            ORDER BY mop_latest.timestamp DESC
        ''').fetchall()
        
        conn.close()
        
        result = []
        for row in orders_data:
            # 计算订单活跃时间
            duration_hours = (row[7] - row[8]) / 3600 if row[8] else 0
            
            result.append({
                'order_id': row[0],
                'title': row[1],
                'brief': row[2],
                'target_value': row[3],
                'current_progress': row[4],
                'progress_percentage': row[5],
                'expires_in': row[6],
                'last_update': row[7],
                'duration_hours': duration_hours,
                'is_active': row[7] + row[6] >= time.time() and time.time() - row[7] < 20*60
            })
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"获取订单摘要失败: {e}")
        return jsonify({"error": "Failed to fetch orders summary"}), 500

# ============= 新闻相关API端点 =============

@app.route('/api/news')
def news_list():
    """获取新闻列表"""
    try:
        conn = get_db_connection()
        
        # 获取查询参数
        limit = request.args.get('limit', DATA_LIMITS['news_default_limit'], type=int)
        news_type = request.args.get('type', type=int)  # 可选的新闻类型筛选
        offset = request.args.get('offset', 0, type=int)  # 分页偏移
        
        # 限制最大返回数量
        if limit > DATA_LIMITS['news_max_limit']:
            limit = DATA_LIMITS['news_max_limit']
        
        # 构建查询
        query = "SELECT news_id, published, type, tag_ids, message, stored_at, updated_at FROM news WHERE 1=1"
        params = []
        
        if news_type is not None:
            query += " AND type = ?"
            params.append(news_type)
        
        query += " ORDER BY published DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        data = conn.execute(query, params).fetchall()
        
        # 获取总数量（用于分页）
        count_query = "SELECT COUNT(*) FROM news WHERE 1=1"
        count_params = []
        if news_type is not None:
            count_query += " AND type = ?"
            count_params.append(news_type)
        
        total_count = conn.execute(count_query, count_params).fetchone()[0]
        
        conn.close()
        
        # 格式化结果
        news_list = []
        for row in data:
            # 确保message不为None
            message = row[4] if row[4] is not None else ''
            tag_ids_str = row[3] if row[3] is not None else '[]'
            
            try:
                tag_ids = json.loads(tag_ids_str)
            except (json.JSONDecodeError, TypeError):
                tag_ids = []
                logging.warning(f"新闻ID {row[0]} 的tag_ids解析失败，使用空数组")
            
            news_item = {
                'id': row[0],
                'published': row[1],
                'type': row[2],
                'tagIds': tag_ids,
                'message': message,
                'stored_at': row[5],
                'updated_at': row[6] if len(row) > 6 and row[6] is not None else row[5]  # 兼容旧数据
            }
            news_list.append(news_item)
        
        return jsonify({
            'news': news_list,
            'total_count': total_count,
            'limit': limit,
            'offset': offset,
            'has_more': offset + limit < total_count
        })
        
    except Exception as e:
        logging.error(f"获取新闻失败: {e}")
        return jsonify({"error": "Failed to fetch news"}), 500

@app.route('/api/news/latest')
def latest_news():
    """获取最新新闻（快捷接口）"""
    try:
        conn = get_db_connection()
        
        limit = request.args.get('limit', 10, type=int)
        if limit > 50:  # 限制最新新闻的最大数量
            limit = 50
        
        data = conn.execute('''
            SELECT news_id, published, type, tag_ids, message, stored_at, updated_at
            FROM news 
            ORDER BY published DESC 
            LIMIT ?
        ''', (limit,)).fetchall()
        
        conn.close()
        
        news_list = []
        for row in data:
            # 确保message不为None
            message = row[4] if row[4] is not None else ''
            tag_ids_str = row[3] if row[3] is not None else '[]'
            
            try:
                tag_ids = json.loads(tag_ids_str)
            except (json.JSONDecodeError, TypeError):
                tag_ids = []
                logging.warning(f"新闻ID {row[0]} 的tag_ids解析失败，使用空数组")
            
            news_item = {
                'id': row[0],
                'published': row[1],
                'type': row[2],
                'tagIds': tag_ids,
                'message': message,
                'stored_at': row[5],
                'updated_at': row[6] if len(row) > 6 and row[6] is not None else row[5]  # 兼容旧数据
            }
            news_list.append(news_item)
        
        logging.info(f"返回 {len(news_list)} 条最新新闻")
        return jsonify(news_list)
        
    except Exception as e:
        logging.error(f"获取最新新闻失败: {e}")
        return jsonify({"error": "Failed to fetch latest news"}), 500

@app.route('/api/news/<int:news_id>')
def news_detail(news_id):
    """获取特定新闻的详细信息"""
    try:
        conn = get_db_connection()
        
        data = conn.execute('''
            SELECT news_id, published, type, tag_ids, message, stored_at, updated_at
            FROM news 
            WHERE news_id = ?
        ''', (news_id,)).fetchone()
        
        conn.close()
        
        if not data:
            return jsonify({"error": "News not found"}), 404
        
        # 确保message不为None
        message = data[4] if data[4] is not None else ''
        tag_ids_str = data[3] if data[3] is not None else '[]'
        
        try:
            tag_ids = json.loads(tag_ids_str)
        except (json.JSONDecodeError, TypeError):
            tag_ids = []
            logging.warning(f"新闻ID {news_id} 的tag_ids解析失败，使用空数组")
        
        news_item = {
            'id': data[0],
            'published': data[1],
            'type': data[2],
            'tagIds': tag_ids,
            'message': message,
            'stored_at': data[5],
            'updated_at': data[6] if len(data) > 6 and data[6] is not None else data[5]  # 兼容旧数据
        }
        
        return jsonify(news_item)
        
    except Exception as e:
        logging.error(f"获取新闻详情失败: {e}")
        return jsonify({"error": "Failed to fetch news detail"}), 500

@app.route('/api/news/types')
def news_types():
    """获取所有新闻类型及其数量"""
    try:
        conn = get_db_connection()
        
        data = conn.execute('''
            SELECT type, COUNT(*) as count
            FROM news 
            GROUP BY type
            ORDER BY type
        ''').fetchall()
        
        conn.close()
        
        types_data = []
        for row in data:
            types_data.append({
                'type': row[0],
                'count': row[1]
            })
        
        return jsonify(types_data)
        
    except Exception as e:
        logging.error(f"获取新闻类型失败: {e}")
        return jsonify({"error": "Failed to fetch news types"}), 500

@app.route('/api/news/stats')
def news_stats():
    """获取新闻统计信息"""
    try:
        conn = get_db_connection()
        
        # 总新闻数量
        total_count = conn.execute('SELECT COUNT(*) FROM news').fetchone()[0]
        
        # 各类型新闻数量
        type_stats = conn.execute('''
            SELECT type, COUNT(*) as count
            FROM news 
            GROUP BY type
            ORDER BY count DESC
        ''').fetchall()
        
        # 最新新闻发布时间
        latest_published = conn.execute('''
            SELECT MAX(published) FROM news
        ''').fetchone()[0]
        
        # 最早新闻发布时间
        earliest_published = conn.execute('''
            SELECT MIN(published) FROM news
        ''').fetchone()[0]
        
        # 最近24小时新增新闻数量
        since_24h = int((datetime.now() - timedelta(hours=24)).timestamp())
        recent_count = conn.execute('''
            SELECT COUNT(*) FROM news WHERE stored_at > ?
        ''', (since_24h,)).fetchone()[0]
        
        conn.close()
        
        type_breakdown = []
        for row in type_stats:
            type_breakdown.append({
                'type': row[0],
                'count': row[1]
            })
        
        return jsonify({
            'total_count': total_count,
            'latest_published': latest_published,
            'earliest_published': earliest_published,
            'recent_24h_count': recent_count,
            'type_breakdown': type_breakdown
        })
        
    except Exception as e:
        logging.error(f"获取新闻统计失败: {e}")
        return jsonify({"error": "Failed to fetch news statistics"}), 500

if __name__ == '__main__':
    # 配置日志
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    app.run(debug=Config.DEBUG, host=Config.HOST, port=Config.PORT)