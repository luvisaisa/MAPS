# MAPS Deployment Checklist

Complete checklist for deploying MAPS to production.

---

##  Pre-Deployment Checklist

### Backend Setup

- [ ] **Install Dependencies**
  ```bash
  pip install -r requirements.txt
  pip install -r requirements-api.txt
  ```

- [ ] **Configure Environment Variables**
  ```bash
  cp .env.example .env
  ```
  Edit `.env` with production values:
  - `SUPABASE_URL`
  - `SUPABASE_KEY`
  - `SUPABASE_DB_URL`
  - `API_HOST` (0.0.0.0)
  - `API_PORT` (8000)
  - `CORS_ORIGINS` (your frontend domain)

- [ ] **Run Database Migrations**
  ```bash
  psql "$SUPABASE_DB_URL" -f migrations/*.sql
  ```

- [ ] **Test API**
  ```bash
  python start_api.py
  # Visit http://localhost:8000/health
  # Visit http://localhost:8000/docs
  ```

### Frontend Setup

- [ ] **Install Dependencies**
  ```bash
  cd web
  npm install
  ```

- [ ] **Configure Environment**
  ```bash
  cp .env.example .env
  ```
  Edit `web/.env` with:
  - `VITE_API_URL` (your API domain)
  - `VITE_SUPABASE_URL`
  - `VITE_SUPABASE_ANON_KEY`
  - `VITE_ENV=production`

- [ ] **Build for Production**
  ```bash
  npm run build
  # Output in web/dist/
  ```

- [ ] **Test Build Locally**
  ```bash
  npm run preview
  ```

### Testing

- [ ] **Run Backend Tests**
  ```bash
  pytest -q
  pytest -q tests/test_foundation_validation.py
  ```

- [ ] **Run Frontend Tests**
  ```bash
  cd web
  npm run lint
  npm test
  ```

- [ ] **Test Real-time Features**
  - [ ] WebSocket connection
  - [ ] SSE streaming
  - [ ] Supabase realtime updates

- [ ] **Test All API Endpoints**
  - [ ] Upload & parsing
  - [ ] Batch jobs
  - [ ] Keywords
  - [ ] Analytics
  - [ ] Search
  - [ ] Export

---

##  Deployment Options

### Option 1: Docker Deployment (Recommended)

#### 1. Build Docker Images

**Backend:**
```bash
docker build -t maps-api:latest .
```

**Frontend:**
```bash
cd web
docker build -t maps-web:latest .
```

#### 2. Deploy with Docker Compose

```bash
docker-compose up -d
```

#### 3. Verify Deployment

```bash
docker ps
docker logs maps-api
docker logs maps-web
```

### Option 2: Cloud Deployment (AWS/GCP/Azure)

#### Backend (API)

**Option A: AWS Elastic Beanstalk**
```bash
eb init -p python-3.12 maps-api
eb create maps-production
eb deploy
```

**Option B: Google Cloud Run**
```bash
gcloud run deploy maps-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

**Option C: Azure App Service**
```bash
az webapp up --name maps-api \
  --runtime "PYTHON:3.12" \
  --sku B1
```

#### Frontend (Web)

**Option A: Vercel (Recommended for React)**
```bash
cd web
vercel --prod
```

**Option B: Netlify**
```bash
cd web
npm run build
netlify deploy --prod --dir=dist
```

**Option C: AWS S3 + CloudFront**
```bash
cd web
npm run build
aws s3 sync dist/ s3://maps-web-prod
aws cloudfront create-invalidation \
  --distribution-id YOUR_ID \
  --paths "/*"
```

### Option 3: VPS Deployment (DigitalOcean/Linode)

#### 1. Set Up Server

```bash
# SSH into server
ssh root@your-server-ip

# Update system
apt update && apt upgrade -y

# Install Python 3.12
apt install python3.12 python3.12-venv python3-pip -y

# Install Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install nodejs -y

# Install Nginx
apt install nginx -y

# Install PostgreSQL client
apt install postgresql-client -y
```

#### 2. Deploy Backend

```bash
# Clone repository
cd /opt
git clone https://github.com/yourusername/MAPS.git
cd MAPS

# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-api.txt

# Configure environment
cp .env.example .env
nano .env  # Edit with production values

# Run migrations
psql "$SUPABASE_DB_URL" -f migrations/*.sql

# Test API
python start_api.py
# Ctrl+C to stop

# Install systemd service
sudo cp deployment/maps-api.service /etc/systemd/system/
sudo systemctl enable maps-api
sudo systemctl start maps-api
sudo systemctl status maps-api
```

#### 3. Deploy Frontend

```bash
cd /opt/MAPS/web

# Install dependencies
npm install

# Configure environment
cp .env.example .env
nano .env  # Edit with production values

# Build
npm run build

# Copy to nginx
sudo cp -r dist/* /var/www/maps/
```

#### 4. Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/maps
```

Add configuration:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        root /var/www/maps;
        try_files $uri $uri/ /index.html;
    }

    # API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # WebSocket
    location /api/v1/batch/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/maps /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 5. Set Up SSL (Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

---

##  Security Checklist

- [ ] **Environment Variables**
  - [ ] No secrets in code
  - [ ] Production credentials in `.env`
  - [ ] `.env` in `.gitignore`

- [ ] **CORS Configuration**
  - [ ] Update `CORS_ORIGINS` to specific domain
  - [ ] Remove wildcard `*` from CORS

- [ ] **Database Security**
  - [ ] Enable Supabase RLS policies
  - [ ] Use connection pooling
  - [ ] Set up database backups

- [ ] **API Security**
  - [ ] Add authentication (JWT)
  - [ ] Implement rate limiting
  - [ ] Add API key validation
  - [ ] Enable HTTPS only

- [ ] **Frontend Security**
  - [ ] Enable CSP headers
  - [ ] Sanitize user inputs
  - [ ] Validate file uploads
  - [ ] Add XSS protection

---

##  Monitoring & Logging

### Set Up Monitoring

- [ ] **Application Monitoring**
  - [ ] Sentry for error tracking
  - [ ] Datadog/New Relic for APM
  - [ ] CloudWatch/GCP Monitoring

- [ ] **Health Checks**
  - [ ] `/health` endpoint monitoring
  - [ ] Database connectivity check
  - [ ] Supabase connection check

- [ ] **Logs**
  - [ ] Centralized logging (ELK stack)
  - [ ] Log rotation
  - [ ] Error alerting

### Example: Sentry Setup

```bash
pip install sentry-sdk
```

```python
# In start_api.py
import sentry_sdk

sentry_sdk.init(
    dsn="your-sentry-dsn",
    environment="production",
)
```

---

##  CI/CD Pipeline

### GitHub Actions Example

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy MAPS

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt
      - run: pytest -q

  deploy-api:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to production
        run: |
          # Your deployment script
          ssh user@server 'cd /opt/MAPS && git pull && systemctl restart maps-api'

  deploy-web:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '20'
      - run: cd web && npm install && npm run build
      - name: Deploy to Vercel
        run: vercel --prod
        env:
          VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}
```

---

##  Post-Deployment Verification

### Smoke Tests

- [ ] **API Health**
  ```bash
  curl https://api.your-domain.com/health
  ```

- [ ] **Web Interface**
  - [ ] Open https://your-domain.com
  - [ ] Test login (if auth enabled)
  - [ ] Upload sample file
  - [ ] Check real-time progress
  - [ ] View analytics

- [ ] **WebSocket Connection**
  - [ ] Upload file and watch live progress
  - [ ] Verify connection status indicator

- [ ] **Supabase Realtime**
  - [ ] Process document and watch live updates
  - [ ] Check database connection status

- [ ] **All Features**
  - [ ] Dashboard loads
  - [ ] Upload works
  - [ ] Profiles accessible
  - [ ] History shows jobs
  - [ ] Keywords searchable
  - [ ] Analytics displays
  - [ ] Search functional
  - [ ] Export downloads

---

##  Performance Optimization

- [ ] **Backend**
  - [ ] Enable Redis caching
  - [ ] Optimize database queries
  - [ ] Add connection pooling
  - [ ] Enable gzip compression

- [ ] **Frontend**
  - [ ] Enable CDN for assets
  - [ ] Optimize images
  - [ ] Code splitting
  - [ ] Lazy loading

- [ ] **Database**
  - [ ] Add indexes
  - [ ] Analyze query performance
  - [ ] Set up read replicas

---

##  Maintenance

### Regular Tasks

- [ ] **Daily**
  - Monitor error rates
  - Check disk space
  - Review logs

- [ ] **Weekly**
  - Database backups
  - Update dependencies
  - Review performance metrics

- [ ] **Monthly**
  - Security updates
  - Load testing
  - User feedback review

---

##  Support & Rollback

### Rollback Plan

If deployment fails:

```bash
# Backend rollback
cd /opt/MAPS
git checkout <previous-commit>
systemctl restart maps-api

# Frontend rollback
cd web
vercel rollback  # or your deployment platform
```

### Support Contacts

- Development Team: dev@your-domain.com
- DevOps: ops@your-domain.com
- Emergency: +1-XXX-XXX-XXXX

---

##  Deployment Complete!

Congratulations! MAPS is now deployed to production.

**Next Steps:**
1. Monitor initial traffic and errors
2. Gather user feedback
3. Plan feature enhancements
4. Set up regular maintenance schedule

**Production URLs:**
- API: https://api.your-domain.com
- Docs: https://api.your-domain.com/docs
- Web: https://your-domain.com

---

Built with  for the medical imaging research community
