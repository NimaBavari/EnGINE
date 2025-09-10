# Step-by-Step Resolution Instructions

## Phase 1: Infrastructure Setup (Prerequisites)

### Step 1.1: Set up External Services

```bash
# Start Elasticsearch
docker run -d --name elasticsearch \
  -p 9200:9200 -p 9300:9300 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  elasticsearch:8.14.0

# Start Redis
docker run -d --name redis -p 6379:6379 redis:7-alpine

# Start PostgreSQL
docker run -d --name postgres \
  -p 5432:5432 \
  -e POSTGRES_DB=engine \
  -e POSTGRES_USER=engine_user \
  -e POSTGRES_PASSWORD=engine_pass \
  postgres:15-alpine
```

### Step 1.2: Create Elasticsearch Index

```bash
# Create search index with proper mapping
curl -X PUT "localhost:9200/web_pages" -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "properties": {
      "content": {
        "type": "text",
        "analyzer": "standard"
      },
      "url": {
        "type": "keyword"
      },
      "frequency": {
        "type": "integer"
      },
      "doc_length": {
        "type": "integer"
      }
    }
  }
}'
```

## Phase 2: Testing and Validation

### Step 2.1: Build and Start Services

```bash
# Create Docker network
docker network create transport

# Build and start all services
docker-compose up --build
```

### Step 2.2: Verify Services

```bash
# Test search API
curl "http://localhost:5050/search?q=test"

# Test ML API
curl "http://localhost:5070/user_profiles/"

# Test client
open http://localhost:8000
```

### Step 2.3: Run Tests

```bash
make test
```
