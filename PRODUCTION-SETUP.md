# Production Setup Guide

## ⚠️ Critical Requirements

### PostgreSQL is REQUIRED for Production

**This application requires PostgreSQL for production deployments.**

SQLite is only suitable for:
- Local development
- Testing environments
- Single-user scenarios

## Why PostgreSQL?

1. **Concurrency**: PostgreSQL handles multiple concurrent writes efficiently
2. **Reliability**: ACID compliance ensures data integrity
3. **Scalability**: Supports horizontal scaling with replication
4. **Performance**: Better query optimization for complex workloads
5. **Features**: Advanced indexing, full-text search, JSON support
6. **Backup & Recovery**: Point-in-time recovery and incremental backups

## Quick Production Setup

### Option 1: Managed Database Service (Recommended)

#### AWS RDS PostgreSQL
```bash
# 1. Create RDS instance via AWS Console
#    - Engine: PostgreSQL 14+
#    - Instance class: db.t3.medium or higher
#    - Storage: 100GB GP3 SSD
#    - Enable automated backups

# 2. Configure security group
#    - Allow inbound traffic on port 5432 from app server

# 3. Get connection details from RDS console
#    - Endpoint
#    - Port
#    - Database name
#    - Master username
```

#### DigitalOcean Managed Database
```bash
# 1. Create managed PostgreSQL cluster
#    - Version: 14+
#    - Plan: Basic ($15/month) or higher
#    - Region: Same as app server

# 2. Add trusted sources (app server IP)

# 3. Get connection details from dashboard
```

#### Render PostgreSQL
```bash
# 1. Create new PostgreSQL database
#    - Version: Latest stable
#    - Region: Same as app

# 2. Get connection string from dashboard
```

### Option 2: Self-Hosted PostgreSQL

#### Ubuntu/Debian Server
```bash
# 1. Install PostgreSQL 14+
sudo apt update
sudo apt install postgresql postgresql-contrib

# 2. Start and enable service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 3. Create database and user
sudo -u postgres psql

CREATE DATABASE ai_coaching;
CREATE USER ai_coach_user WITH ENCRYPTED PASSWORD 'your-secure-password';
GRANT ALL PRIVILEGES ON DATABASE ai_coaching TO ai_coach_user;

# Grant schema privileges
\c ai_coaching
GRANT ALL ON SCHEMA public TO ai_coach_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ai_coach_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ai_coach_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ai_coach_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO ai_coach_user;

\q

# 4. Configure PostgreSQL for remote connections (if needed)
sudo nano /etc/postgresql/14/main/postgresql.conf
# Set: listen_addresses = '*'

sudo nano /etc/postgresql/14/main/pg_hba.conf
# Add: host    all    all    0.0.0.0/0    md5

# 5. Restart PostgreSQL
sudo systemctl restart postgresql

# 6. Configure firewall
sudo ufw allow 5432/tcp
```

## Environment Configuration

Update your `.env` file for production:

```bash
# ============================================
# Environment
# ============================================
ENVIRONMENT=production

# ============================================
# PostgreSQL Database (REQUIRED)
# ============================================
DB_USER=ai_coach_user
DB_PASSWORD=your-secure-password-here
DB_HOST=your-db-host.amazonaws.com  # Or localhost for self-hosted
DB_PORT=5432
DB_NAME=ai_coaching

# DO NOT use SQLite in production
# SQLITE_DB_PATH should be commented out or removed

# ============================================
# Other required settings...
# ============================================
```

## Database Migration

### Initial Setup
```bash
# The app will automatically create tables on first run
# Make sure your PostgreSQL connection is configured correctly

# 1. Activate your Python environment
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the migration script to create performance indexes
python migrate_performance_indexes.py

# 4. Start the backend (tables will be created automatically)
cd backend
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Migrating from SQLite to PostgreSQL

If you have existing data in SQLite:

```bash
# 1. Export data from SQLite
sqlite3 ai_coaching.db .dump > sqlite_dump.sql

# 2. Clean up the dump file for PostgreSQL compatibility
# Remove SQLite-specific commands
sed -i '/^PRAGMA/d' sqlite_dump.sql
sed -i 's/AUTOINCREMENT/SERIAL/g' sqlite_dump.sql

# 3. Import to PostgreSQL
psql -h your-db-host -U ai_coach_user -d ai_coaching -f sqlite_dump.sql

# 4. Run performance index migration
python migrate_performance_indexes.py
```

## Performance Tuning

### PostgreSQL Configuration
```sql
-- Connect to your database
psql -h your-db-host -U ai_coach_user -d ai_coaching

-- Recommended settings for the app
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;
ALTER SYSTEM SET work_mem = '4MB';
ALTER SYSTEM SET min_wal_size = '1GB';
ALTER SYSTEM SET max_wal_size = '4GB';

-- Restart PostgreSQL to apply changes
```

### Connection Pooling

The application includes connection pooling by default:
- Pool size: 10 connections
- Max overflow: 20 connections
- Pre-ping: Enabled (checks connection health)
- Recycle: 3600 seconds (1 hour)

For high-traffic scenarios, consider using PgBouncer:

```bash
# Install PgBouncer
sudo apt install pgbouncer

# Configure /etc/pgbouncer/pgbouncer.ini
[databases]
ai_coaching = host=localhost port=5432 dbname=ai_coaching

[pgbouncer]
listen_addr = 127.0.0.1
listen_port = 6432
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 20

# Update your app to connect to PgBouncer
DB_HOST=localhost
DB_PORT=6432
```

## Monitoring

### Health Checks
```bash
# Check database connectivity
psql -h your-db-host -U ai_coach_user -d ai_coaching -c "SELECT version();"

# Check connection count
psql -h your-db-host -U ai_coach_user -d ai_coaching -c "SELECT count(*) FROM pg_stat_activity;"

# Check database size
psql -h your-db-host -U ai_coach_user -d ai_coaching -c "SELECT pg_size_pretty(pg_database_size('ai_coaching'));"
```

### Performance Monitoring
```sql
-- Check slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan;

-- Check table statistics
SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del
FROM pg_stat_user_tables;
```

## Backup Strategy

### Automated Backups

#### Using pg_dump
```bash
# Create backup script
cat > /usr/local/bin/backup-ai-coaching.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups/ai-coaching"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

pg_dump -h your-db-host -U ai_coach_user ai_coaching | gzip > $BACKUP_DIR/ai_coaching_$TIMESTAMP.sql.gz

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
EOF

chmod +x /usr/local/bin/backup-ai-coaching.sh

# Add to crontab (daily at 2 AM)
echo "0 2 * * * /usr/local/bin/backup-ai-coaching.sh" | crontab -
```

#### Using AWS RDS
- Enable automated backups in RDS console
- Set backup retention period (7-35 days)
- Enable point-in-time recovery

## Security Checklist

- ✅ Use strong passwords (minimum 16 characters)
- ✅ Enable SSL/TLS for database connections
- ✅ Restrict database access by IP address
- ✅ Use environment variables for credentials
- ✅ Enable connection encryption
- ✅ Regular security updates
- ✅ Monitor failed login attempts
- ✅ Use least privilege principle for database user

## Troubleshooting

### Connection Issues
```bash
# Test connectivity
telnet your-db-host 5432

# Check PostgreSQL logs
# Managed service: Check dashboard
# Self-hosted: tail -f /var/log/postgresql/postgresql-14-main.log
```

### Performance Issues
```bash
# Check if indexes exist
python migrate_performance_indexes.py

# Analyze tables
psql -h your-db-host -U ai_coach_user -d ai_coaching -c "ANALYZE;"

# Check for table bloat
psql -h your-db-host -U ai_coach_user -d ai_coaching -c "VACUUM ANALYZE;"
```

### Migration Issues
```bash
# Check table structure
psql -h your-db-host -U ai_coach_user -d ai_coaching -c "\dt"

# Check indexes
psql -h your-db-host -U ai_coach_user -d ai_coaching -c "\di"

# Verify permissions
psql -h your-db-host -U ai_coach_user -d ai_coaching -c "\du"
```

## Support Resources

- PostgreSQL Documentation: https://www.postgresql.org/docs/
- AWS RDS PostgreSQL: https://docs.aws.amazon.com/rds/
- DigitalOcean Managed Databases: https://docs.digitalocean.com/products/databases/
- PostgreSQL Performance Tuning: https://wiki.postgresql.org/wiki/Performance_Optimization

## Next Steps

1. ✅ Set up PostgreSQL database
2. ✅ Configure environment variables
3. ✅ Run migration script
4. ✅ Test connectivity
5. ✅ Configure backups
6. ✅ Set up monitoring
7. ✅ Deploy application

For complete deployment instructions, see:
- `README.md` - Complete setup guide
- `DEPLOYMENT-CHECKLIST.md` - Production deployment checklist
- `QUICK-START.md` - 10-minute setup guide
