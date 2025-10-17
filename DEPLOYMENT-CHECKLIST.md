# 🚀 Deployment Checklist

Use this checklist when deploying the AI Coaching Platform to production.

---

## 📋 Pre-Deployment

### Code & Repository
- [ ] All code committed to version control
- [ ] Branch merged to `main` or `production` branch
- [ ] No sensitive data in repository (API keys, passwords)
- [ ] `.env` file added to `.gitignore`
- [ ] Version tagged (e.g., `v1.0.0`)

### Environment Setup
- [ ] Production server provisioned (see hardware requirements below)
- [ ] SSH access configured with key-based authentication
- [ ] Firewall configured (ports 80, 443, optionally 22)
- [ ] Domain name registered and DNS configured
- [ ] SSL certificate obtained (Let's Encrypt recommended)

### External Services
- [ ] AWS S3 bucket created and configured
- [ ] S3 bucket permissions verified (private bucket recommended)
- [ ] OpenAI API key obtained and tested
- [ ] OpenAI API credits loaded
- [ ] PostgreSQL database provisioned (recommended for production)

---

## ⚙️ Server Configuration

### Hardware Requirements (Production)

**Minimum for 50-100 concurrent users:**
```yaml
CPU: 4-8 cores (3.0 GHz+)
RAM: 16-32 GB
Storage: 200-500 GB NVMe SSD
Network: 1 Gbps
OS: Ubuntu 22.04 LTS
```

**Recommended Cloud Instances:**
- AWS: `t3.xlarge` or `c6i.xlarge` ($100-200/month)
- Google Cloud: `n2-standard-4` ($120-180/month)
- Azure: `Standard_D4s_v3` ($140-190/month)
- DigitalOcean: Performance Droplet 8GB ($96/month)

### System Setup

```bash
# Update system
- [ ] sudo apt update && sudo apt upgrade -y

# Install required packages
- [ ] sudo apt install -y python3.11 python3.11-venv python3-pip
- [ ] sudo apt install -y nodejs npm
- [ ] sudo apt install -y nginx
- [ ] sudo apt install -y tesseract-ocr tesseract-ocr-eng
- [ ] sudo apt install -y postgresql postgresql-contrib
- [ ] sudo apt install -y git curl wget

# Install certbot for SSL
- [ ] sudo apt install -y certbot python3-certbot-nginx
```

---

## 🔧 Application Deployment

### 1. Clone Repository

```bash
- [ ] cd /var/www
- [ ] sudo mkdir ai-coaching
- [ ] sudo chown $USER:$USER ai-coaching
- [ ] cd ai-coaching
- [ ] git clone https://github.com/Aime-Rick/AI-Coaching-Andreas.git .
```

### 2. Backend Setup

```bash
- [ ] python3.11 -m venv venv
- [ ] source venv/bin/activate
- [ ] pip install --upgrade pip
- [ ] pip install -r requirements.txt
- [ ] pip install gunicorn  # Production server
```

### 3. Environment Configuration

```bash
- [ ] cp .env.example .env
- [ ] nano .env  # Edit with production values
```

**Production `.env` Configuration:**
```env
# Required Changes:
- [ ] ENVIRONMENT=production
- [ ] DEBUG=false
- [ ] OPENAI_API_KEY=<your-production-key>
- [ ] AWS_ACCESS_KEY_ID=<your-production-key>
- [ ] AWS_SECRET_ACCESS_KEY=<your-production-secret>
- [ ] S3_BUCKET_NAME=<your-production-bucket>
- [ ] DB_USER=postgres
- [ ] DB_PASSWORD=<secure-password>
- [ ] DB_HOST=localhost (or RDS endpoint)
- [ ] DB_NAME=ai_coaching_prod
- [ ] VITE_API_URL=https://api.yourdomain.com
```

### 4. Database Setup

```bash
# Create PostgreSQL database
- [ ] sudo -u postgres psql
- [ ] CREATE DATABASE ai_coaching_prod;
- [ ] CREATE USER ai_coach WITH PASSWORD 'secure-password';
- [ ] GRANT ALL PRIVILEGES ON DATABASE ai_coaching_prod TO ai_coach;
- [ ] \q

# Run migrations
- [ ] source venv/bin/activate
- [ ] python3 migrate_performance_indexes.py
```

### 5. Frontend Build

```bash
- [ ] cd frontend
- [ ] npm install
- [ ] npm run build
- [ ] cd ..
```

Frontend build output: `frontend/dist/`

---

## 🌐 Web Server Configuration

### NGINX Setup

Create `/etc/nginx/sites-available/ai-coaching`:

```nginx
# Backend API
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for long-running requests
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
    
    # Increase body size for file uploads
    client_max_body_size 500M;
}

# Frontend
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    root /var/www/ai-coaching/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Static assets caching
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

```bash
# Enable site and restart nginx
- [ ] sudo ln -s /etc/nginx/sites-available/ai-coaching /etc/nginx/sites-enabled/
- [ ] sudo nginx -t  # Test configuration
- [ ] sudo systemctl restart nginx
```

### SSL Certificate

```bash
- [ ] sudo certbot --nginx -d api.yourdomain.com
- [ ] sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
- [ ] sudo systemctl reload nginx
```

---

## 🔄 Application Service

### Systemd Service

Create `/etc/systemd/system/ai-coaching.service`:

```ini
[Unit]
Description=AI Coaching Platform Backend
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/ai-coaching
Environment="PATH=/var/www/ai-coaching/venv/bin"
EnvironmentFile=/var/www/ai-coaching/.env

# Production: Use Gunicorn with multiple workers
ExecStart=/var/www/ai-coaching/venv/bin/gunicorn backend.api.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 300 \
    --access-logfile /var/log/ai-coaching/access.log \
    --error-logfile /var/log/ai-coaching/error.log

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Create log directory
- [ ] sudo mkdir -p /var/log/ai-coaching
- [ ] sudo chown www-data:www-data /var/log/ai-coaching

# Enable and start service
- [ ] sudo systemctl daemon-reload
- [ ] sudo systemctl enable ai-coaching
- [ ] sudo systemctl start ai-coaching
- [ ] sudo systemctl status ai-coaching
```

---

## 🔒 Security Hardening

### System Security
- [ ] Disable root SSH login
- [ ] Configure fail2ban
- [ ] Set up automatic security updates
- [ ] Configure firewall (ufw):
  ```bash
  sudo ufw allow 22/tcp  # SSH
  sudo ufw allow 80/tcp  # HTTP
  sudo ufw allow 443/tcp # HTTPS
  sudo ufw enable
  ```

### Application Security
- [ ] Secure `.env` file permissions: `chmod 600 .env`
- [ ] Use strong database passwords (20+ characters)
- [ ] Rotate API keys regularly
- [ ] Configure CORS for production domains only
- [ ] Enable rate limiting on API endpoints
- [ ] Set up database backups (automated)

### NGINX Security Headers

Add to NGINX server block:

```nginx
# Security headers
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
add_header Content-Security-Policy "default-src 'self' https: data: 'unsafe-inline' 'unsafe-eval';" always;
```

---

## 📊 Monitoring & Logging

### Log Rotation

Create `/etc/logrotate.d/ai-coaching`:

```
/var/log/ai-coaching/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload ai-coaching > /dev/null 2>&1 || true
    endscript
}
```

### Monitoring Setup

```bash
# Install monitoring tools
- [ ] sudo apt install -y htop iotop nethogs

# Optional: Set up monitoring services
- [ ] Install Prometheus
- [ ] Install Grafana
- [ ] Configure alerting
- [ ] Set up Sentry for error tracking
```

### Health Checks

```bash
# Backend health
- [ ] curl https://api.yourdomain.com/
- [ ] curl https://api.yourdomain.com/performance

# Frontend
- [ ] curl https://yourdomain.com

# SSL certificate
- [ ] curl -I https://yourdomain.com | grep -i strict
```

---

## 💾 Backup Configuration

### Database Backups

Create `/usr/local/bin/backup-database.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/ai-coaching"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup PostgreSQL
pg_dump -U ai_coach ai_coaching_prod > $BACKUP_DIR/db_$DATE.sql
gzip $BACKUP_DIR/db_$DATE.sql

# Keep only last 30 days
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +30 -delete
```

```bash
- [ ] sudo chmod +x /usr/local/bin/backup-database.sh
- [ ] sudo crontab -e
```

Add to crontab:
```
0 2 * * * /usr/local/bin/backup-database.sh
```

### S3 Backups
- [ ] Enable S3 versioning
- [ ] Configure S3 lifecycle rules
- [ ] Set up cross-region replication (optional)

---

## ✅ Post-Deployment Verification

### Functional Tests

```bash
# API endpoints
- [ ] curl https://api.yourdomain.com/
- [ ] curl https://api.yourdomain.com/performance
- [ ] curl https://api.yourdomain.com/docs

# Frontend
- [ ] Open https://yourdomain.com in browser
- [ ] Test file upload
- [ ] Test chat functionality
- [ ] Test report generation
- [ ] Check all pages load correctly
```

### Performance Tests

```bash
# Response times
- [ ] API response < 200ms for most endpoints
- [ ] Page load < 2 seconds
- [ ] File upload works for 50MB+ files
- [ ] Chat response < 6 seconds
- [ ] Cache hit rate > 70%

# Load test with Apache Bench (optional)
- [ ] ab -n 1000 -c 10 https://api.yourdomain.com/
```

### Security Checks

```bash
- [ ] SSL certificate valid (A+ rating on SSL Labs)
- [ ] No exposed sensitive data in responses
- [ ] HTTPS redirect working
- [ ] CORS configured correctly
- [ ] Rate limiting working
```

---

## 📈 Monitoring & Maintenance

### Daily Checks
- [ ] Check application logs for errors
- [ ] Monitor disk space usage
- [ ] Verify backups completed
- [ ] Check CPU/RAM usage

### Weekly Checks
- [ ] Review security logs
- [ ] Check for system updates
- [ ] Monitor API usage and costs
- [ ] Review performance metrics

### Monthly Checks
- [ ] Rotate API keys (recommended)
- [ ] Review and optimize database queries
- [ ] Check storage costs and optimization
- [ ] Update dependencies
- [ ] Review and clean up old files

---

## 🚨 Emergency Procedures

### Rollback Plan

```bash
# Stop service
- [ ] sudo systemctl stop ai-coaching

# Restore previous version
- [ ] cd /var/www/ai-coaching
- [ ] git checkout <previous-tag>
- [ ] source venv/bin/activate
- [ ] pip install -r requirements.txt

# Restore database backup
- [ ] gunzip /var/backups/ai-coaching/db_<timestamp>.sql.gz
- [ ] psql -U ai_coach ai_coaching_prod < /var/backups/ai-coaching/db_<timestamp>.sql

# Restart service
- [ ] sudo systemctl start ai-coaching
```

### Contact Information

**On-Call Personnel:**
- Developer: [contact info]
- DevOps: [contact info]
- Support: [contact info]

**Emergency Contacts:**
- AWS Support: [account number]
- OpenAI Support: [account info]
- Hosting Provider: [account info]

---

## 📝 Deployment Sign-Off

### Deployment Details
- **Date**: _________________
- **Version**: _________________
- **Deployed By**: _________________
- **Environment**: Production / Staging
- **Server**: _________________

### Checklist Completion
- [ ] All pre-deployment tasks completed
- [ ] Application deployed successfully
- [ ] Security hardening completed
- [ ] Monitoring configured
- [ ] Backups configured
- [ ] Documentation updated
- [ ] Team notified

### Sign-Off
- **Deployer**: _________________ (Date: _________)
- **Reviewer**: _________________ (Date: _________)
- **Approved By**: _________________ (Date: _________)

---

**Total Deployment Time**: 2-4 hours (depending on experience)

**Next Review Date**: _________________

---

For questions or issues during deployment, refer to:
- [README.md](README.md) - Full documentation
- [PERFORMANCE-OPTIMIZATION-GUIDE.md](PERFORMANCE-OPTIMIZATION-GUIDE.md) - Performance tuning
- [QUICK-START.md](QUICK-START.md) - Quick setup guide
