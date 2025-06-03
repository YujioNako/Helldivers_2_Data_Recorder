# Helldivers_2_Data_Recorder
Record data from public api (helldiverscompanion.com)

## How to Start
* Install requirements
* Set your config in `config.py`
* Run `run.py` for monitor and web server (You can run monitor with `monitor.py`, and run web server with `app.py` too)
* Open the url set in your `config.py` and surf the data

## API Endpoints
### 1. Page Routes

#### Get Main Dashboard
```http
GET /
```
Returns the main dashboard page.

#### Get Static Resources
```http
GET /src/<path:fileName>
```
Returns supporting static files.

### 2. War Status APIs

#### 2.1 Get War Status Trend
```http
GET /api/war-status-trend
```

**Query Parameters:**
- `hours` (optional): Time range in hours, default 24 hours (Decided on your config)
- `limit` (optional): Data point limit, default 50 (Decided on your config)

**Response Example:**
```json
[
  {
    "timestamp": 1701234567,
    "super_earth_planets": 45,
    "enemy_planets": 55,
    "total_players": 85000,
    "impact_multiplier": 1.5
  }
]
```

#### 2.2 Get War Statistics Trend
```http
GET /api/war-stats-trend
```

**Query Parameters:**
- `hours` (optional): Time range in hours, default 24 hours (Decided on your config)
- `limit` (optional): Data point limit, default 50 (Decided on your config)

**Response Example:**
```json
[
  {
    "timestamp": 1701234567,
    "missions_won": 1500,
    "missions_lost": 300,
    "mission_success_rate": 83.3,
    "bug_kills": 250000,
    "automaton_kills": 180000,
    "illuminate_kills": 0,
    "total_deaths": 45000,
    "accuracy": 72.5
  }
]
```

### 3. Major Orders APIs

#### 3.1 Get Major Orders Progress
```http
GET /api/major-orders-progress
```

**Query Parameters:**
- `limit` (optional): Data limit, default 100 (Decided on your config)

**Response Example:**
```json
[
  {
    "order_id": 12345,
    "title": "Liberate Creek Planet",
    "brief": "Free Creek planet from the Bug menace",
    "target_value": 1000000,
    "timestamp": 1701234567,
    "current_progress": 750000,
    "progress_percentage": 75.0,
    "expires_in": 86400
  }
]
```

#### 3.2 Get Specific Order History
```http
GET /api/major-order-history/<int:order_id>
```

**Path Parameters:**
- `order_id`: Order ID

**Query Parameters:**
- `limit` (optional): Data point limit, default 50 (Decided on your config)

**Response Example:**
```json
[
  {
    "timestamp": 1701234567,
    "current_progress": 750000,
    "progress_percentage": 75.0,
    "expires_in": 86400
  }
]
```

#### 3.3 Get Order Progress History Curve
```http
GET /api/major-order-progress-history/<int:order_id>
```

**Path Parameters:**
- `order_id`: Order ID

**Query Parameters:**
- `hours` (optional): Time range in hours, default 24 hours (Decided on your config)
- `limit` (optional): Data point limit, default 50 (Decided on your config)

**Response Example:**
```json
{
  "order_info": {
    "order_id": 12345,
    "title": "Liberate Creek Planet",
    "brief": "Free Creek planet from the Bug menace",
    "target_value": 1000000
  },
  "progress_history": [
    {
      "timestamp": 1701234567,
      "current_progress": 750000,
      "progress_percentage": 75.0,
      "expires_in": 86400
    }
  ]
}
```

#### 3.4 Get All Orders Summary
```http
GET /api/all-major-orders-summary
```

**Response Example:**
```json
[
  {
    "order_id": 12345,
    "title": "Liberate Creek Planet",
    "brief": "Free Creek planet from the Bug menace",
    "target_value": 1000000,
    "current_progress": 750000,
    "progress_percentage": 75.0,
    "expires_in": 86400,
    "last_update": 1701234567,
    "duration_hours": 24.5,
    "is_active": true
  }
]
```

### 4. Planet Information APIs

#### 4.1 Get Planets by Sector
```http
GET /api/planets-by-sector
```

**Response Example:**
```json
{
  "total": 100,
  "sectors": {
    "Galactic War Front": [
      {
        "index": 1,
        "sector": "Galactic War Front",
        "max_health": 1000000,
        "position": {"x": 100.5, "y": 200.3},
        "owner": 1,
        "health": 750000,
        "players": 1500,
        "regen_per_second": 100
      }
    ]
  },
  "timestamp": 1701234567
}
```

#### 4.2 Get Planet Details
```http
GET /api/planet-details/<int:planet_index>
```

**Path Parameters:**
- `planet_index`: Planet index

**Response Example:**
```json
{
  "planet": {
    "index": 1,
    "sector": "Galactic War Front",
    "max_health": 1000000,
    "position": {"x": 100.5, "y": 200.3},
    "owner": 1,
    "health": 750000,
    "players": 1500,
    "regen_per_second": 100
  },
  "regions": [
    {
      "regionIndex": 0,
      "maxHealth": 250000,
      "regionSize": 25,
      "owner": 1,
      "health": 200000,
      "regerPerSecond": 25,
      "isAvailable": true,
      "players": 375
    }
  ]
}
```

#### 4.3 Get Planet Health History
```http
GET /api/planet-health-history/<int:planet_index>
```

**Path Parameters:**
- `planet_index`: Planet index

**Query Parameters:**
- `hours` (optional): Time range in hours, default 24 hours (Decided on your config)
- `limit` (optional): Data point limit, default 50 (Decided on your config)

**Response Example:**
```json
[
  {
    "timestamp": 1701234567,
    "health": 750000,
    "players": 1500,
    "regen_per_second": 100,
    "owner": 1
  }
]
```

#### 4.4 Get Region Health History
```http
GET /api/region-health-history/<int:planet_index>/<int:region_index>
```

**Path Parameters:**
- `planet_index`: Planet index
- `region_index`: Region index

**Query Parameters:**
- `hours` (optional): Time range in hours, default 24 hours (Decided on your config)
- `limit` (optional): Data point limit, default 50 (Decided on your config)

**Response Example:**
```json
[
  {
    "timestamp": 1701234567,
    "health": 200000,
    "regen_per_second": 25,
    "players": 375,
    "owner": 1
  }
]
```

### 5. Global Resources APIs

#### 5.1 Get Global Resources Trend
```http
GET /api/global-resources-trend
```

**Query Parameters:**
- `hours` (optional): Time range in hours, default 24 hours (Decided on your config)
- `limit` (optional): Data point limit, default 50 (Decided on your config)

**Response Example:**
```json
[
  {
    "timestamp": 1701234567,
    "resource_id": 1,
    "current_value": 75000,
    "max_value": 100000,
    "percentage": 75.0
  }
]
```

### 6. News APIs

#### 6.1 Get News List
```http
GET /api/news
```

**Query Parameters:**
- `limit` (optional): Return limit, default 20, maximum 100 (Decided on your config)
- `type` (optional): News type filter
- `offset` (optional): Pagination offset, default 0

**Response Example:**
```json
{
  "news": [
    {
      "id": 12345,
      "published": 1701234567,
      "type": 1,
      "tagIds": [101, 102],
      "message": "New Major Order has been issued!",
      "stored_at": 1701234567,
      "updated_at": 1701234567
    }
  ],
  "total_count": 150,
  "limit": 20,
  "offset": 0,
  "has_more": true
}
```

#### 6.2 Get Latest News
```http
GET /api/news/latest
```

**Query Parameters:**
- `limit` (optional): Return limit, default 10, maximum 50

**Response Example:**
```json
[
  {
    "id": 12345,
    "published": 1701234567,
    "type": 1,
    "tagIds": [101, 102],
    "message": "New Major Order has been issued!",
    "stored_at": 1701234567,
    "updated_at": 1701234567
  }
]
```

#### 6.3 Get News Details
```http
GET /api/news/<int:news_id>
```

**Path Parameters:**
- `news_id`: News ID

**Response Example:**
```json
{
  "id": 12345,
  "published": 1701234567,
  "type": 1,
  "tagIds": [101, 102],
  "message": "New Major Order has been issued!",
  "stored_at": 1701234567,
  "updated_at": 1701234567
}
```

#### 6.4 Get News Types
```http
GET /api/news/types
```

**Response Example:**
```json
[
  {
    "type": 1,
    "count": 45
  },
  {
    "type": 2,
    "count": 30
  }
]
```

#### 6.5 Get News Statistics
```http
GET /api/news/stats
```

**Response Example:**
```json
{
  "total_count": 150,
  "latest_published": 1701234567,
  "earliest_published": 1701200000,
  "recent_24h_count": 5,
  "type_breakdown": [
    {
      "type": 1,
      "count": 45
    },
    {
      "type": 2,
      "count": 30
    }
  ]
}
```
