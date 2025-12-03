# Guía de Despliegue - Sistema de Control de Apuestas RushBet

## Requisitos del Sistema

### Requisitos Mínimos
- **CPU**: 2 núcleos
- **RAM**: 4GB
- **Almacenamiento**: 20GB SSD
- **Sistema Operativo**: Ubuntu 20.04+ / Windows Server 2019+
- **Python**: 3.11+
- **Node.js**: 18+
- **Base de Datos**: MySQL 8.0+ / PostgreSQL 13+

### Requisitos Recomendados
- **CPU**: 4 núcleos
- **RAM**: 8GB
- **Almacenamiento**: 50GB SSD
- **Red**: Conexión de 100 Mbps

## Preparación del Entorno

### 1. Instalación de Dependencias

#### Ubuntu/Debian
```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python
sudo apt install python3.11 python3.11-venv python3.11-dev -y

# Instalar Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Instalar MySQL
sudo apt install mysql-server mysql-client -y

# Instalar herramientas adicionales
sudo apt install git nginx supervisor redis-server -y
```

#### Windows
```powershell
# Instalar Chocolatey (si no está instalado)
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Instalar dependencias
choco install python311 nodejs mysql git nginx -y
```

### 2. Configuración de Base de Datos

#### MySQL
```sql
-- Crear base de datos
CREATE DATABASE betcontrol CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Crear usuario
CREATE USER 'betcontrol'@'localhost' IDENTIFIED BY 'secure_password_here';
GRANT ALL PRIVILEGES ON betcontrol.* TO 'betcontrol'@'localhost';
FLUSH PRIVILEGES;

-- Configuración óptima
SET GLOBAL innodb_buffer_pool_size = 1073741824; -- 1GB
SET GLOBAL innodb_log_file_size = 268435456;    -- 256MB
SET GLOBAL max_connections = 200;
```

## Despliegue del Backend

### 1. Preparación del Código
```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/betcontrol.git
cd betcontrol

# Crear entorno virtual
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configuración de Variables de Entorno
Crear archivo `.env`:
```env
# Base de Datos
DB_HOST=localhost
DB_PORT=3306
DB_USER=betcontrol
DB_PASSWORD=secure_password_here
DB_NAME=betcontrol

# Seguridad
SECRET_KEY=your-super-secret-key-here-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=["https://tudominio.com", "https://www.tudominio.com"]

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Redis (opcional)
REDIS_URL=redis://localhost:6379/0

# Email (opcional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=tu-email@gmail.com
SMTP_PASSWORD=tu-contraseña-app
```

### 3. Inicialización de Base de Datos
```bash
# Crear tablas
python scripts/init_db.py

# Verificar conexión
python -c "from app.db.session import get_db; next(get_db())"
```

### 4. Configuración de Supervisor (Linux)
Crear archivo `/etc/supervisor/conf.d/betcontrol.conf`:
```ini
[program:betcontrol]
command=/path/to/betcontrol/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
directory=/path/to/betcontrol
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/betcontrol/app.log
environment=PATH="/path/to/betcontrol/venv/bin",HOME="/home/www-data",USER="www-data"
```

### 5. Servicio de Windows (Windows)
Crear archivo `betcontrol_service.py`:
```python
import win32serviceutil
import win32service
import win32event
import subprocess
import sys

class BetControlService(win32serviceutil.ServiceFramework):
    _svc_name_ = "BetControlService"
    _svc_display_name_ = "Bet Control Service"
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.process = None
    
    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        if self.process:
            self.process.terminate()
    
    def SvcDoRun(self):
        self.process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", "app.main:app",
            "--host", "0.0.0.0", "--port", "8000"
        ])
        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(BetControlService)
```

## Despliegue del Frontend

### 1. Construcción de la Aplicación
```bash
cd frontend

# Instalar dependencias
npm install

# Construir para producción
npm run build
```

### 2. Configuración de Nginx
Crear archivo `/etc/nginx/sites-available/betcontrol`:
```nginx
server {
    listen 80;
    server_name tudominio.com www.tudominio.com;
    
    # Frontend
    location / {
        root /var/www/betcontrol/frontend/build;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
        
        # Cache headers
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # WebSocket (si se usa)
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # Logs
    access_log /var/log/nginx/betcontrol_access.log;
    error_log /var/log/nginx/betcontrol_error.log;
}
```

### 3. SSL/TLS con Let's Encrypt
```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx

# Obtener certificado
sudo certbot --nginx -d tudominio.com -d www.tudominio.com

# Configurar renovación automática
sudo crontab -e
# Agregar: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Configuración de Seguridad

### 1. Firewall
```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# FirewallD (CentOS/RHEL)
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 2. Configuración de MySQL
```bash
# Ejecutar script de seguridad
sudo mysql_secure_installation

# Configuración adicional en /etc/mysql/mysql.conf.d/mysqld.cnf
[mysqld]
bind-address = 127.0.0.1
max_connections = 200
innodb_buffer_pool_size = 1G
query_cache_size = 64M
```

### 3. Variables de Entorno Seguras
```bash
# Crear archivo de entorno seguro
sudo touch /etc/betcontrol/.env
sudo chown www-data:www-data /etc/betcontrol/.env
sudo chmod 600 /etc/betcontrol/.env

# Actualizar configuración de supervisor para usar el archivo
environment=PATH="/path/to/venv/bin",ENV_FILE="/etc/betcontrol/.env"
```

## Monitoreo y Mantenimiento

### 1. Configuración de Monitoreo
```bash
# Instalar herramientas
sudo apt install htop iotop nethogs -y

# Configurar logrotate
sudo nano /etc/logrotate.d/betcontrol
```

### 2. Script de Monitoreo
Crear archivo `monitor.py`:
```python
#!/usr/bin/env python3
import psutil
import requests
import smtplib
from email.mime.text import MIMEText
import datetime

def check_services():
    services = {
        'nginx': 80,
        'backend': 8000,
        'mysql': 3306
    }
    
    results = {}
    for service, port in services.items():
        try:
            # Check if port is listening
            for conn in psutil.net_connections():
                if conn.laddr.port == port and conn.status == 'LISTEN':
                    results[service] = True
                    break
            else:
                results[service] = False
        except Exception as e:
            results[service] = False
            print(f"Error checking {service}: {e}")
    
    return results

def send_alert(message):
    # Configurar email de alerta
    msg = MIMEText(message)
    msg['Subject'] = 'BetControl Alert'
    msg['From'] = 'alert@tudominio.com'
    msg['To'] = 'admin@tudominio.com'
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login('tu-email@gmail.com', 'tu-contraseña')
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print(f"Error sending email: {e}")

if __name__ == "__main__":
    results = check_services()
    
    failed_services = [s for s, status in results.items() if not status]
    
    if failed_services:
        message = f"Services down: {', '.join(failed_services)} at {datetime.datetime.now()}"
        send_alert(message)
        print(message)
    else:
        print("All services running normally")
```

### 3. Backup Automático
Crear script `backup.sh`:
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/betcontrol"

# Crear directorio si no existe
mkdir -p $BACKUP_DIR

# Backup de base de datos
mysqldump -u betcontrol -p'secure_password_here' betcontrol > $BACKUP_DIR/db_backup_$DATE.sql

# Backup de archivos importantes
tar -czf $BACKUP_DIR/files_backup_$DATE.tar.gz /path/to/betcontrol/logs /etc/betcontrol/

# Eliminar backups antiguos (mantener últimos 30 días)
find $BACKUP_DIR -name "*.sql" -type f -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -type f -mtime +30 -delete

# Enviar a almacenamiento externo (opcional)
# aws s3 sync $BACKUP_DIR s3://tu-bucket/backups/
```

## Actualización del Sistema

### 1. Procedimiento de Actualización
```bash
# 1. Backup
./backup.sh

# 2. Detener servicios
sudo supervisorctl stop betcontrol
sudo systemctl stop nginx

# 3. Actualizar código
git pull origin main

# 4. Actualizar dependencias
source venv/bin/activate
pip install -r requirements.txt

# 5. Ejecutar migraciones
python scripts/migrate_db.py

# 6. Reiniciar servicios
sudo supervisorctl start betcontrol
sudo systemctl start nginx

# 7. Verificar funcionamiento
python scripts/health_check.py
```

### 2. Rollback (si es necesario)
```bash
# Restaurar desde backup
mysql -u betcontrol -p betcontrol < /backups/betcontrol/db_backup_latest.sql

# Restaurar código anterior
git checkout previous-stable-tag

# Reiniciar servicios
sudo supervisorctl restart betcontrol
sudo systemctl restart nginx
```

## Solución de Problemas

### Problemas Comunes

**1. Puerto 80 ya está en uso:**
```bash
sudo netstat -tulpn | grep :80
sudo systemctl stop apache2  # o el servicio que esté usando el puerto
```

**2. Error de conexión a MySQL:**
```bash
sudo systemctl status mysql
sudo mysql -u root -p
# Verificar usuario y permisos
SELECT User, Host FROM mysql.user;
```

**3. Problemas de permisos:**
```bash
sudo chown -R www-data:www-data /path/to/betcontrol
sudo chmod -R 755 /path/to/betcontrol
```

**4. Gunicorn no inicia:**
```bash
# Verificar logs
sudo tail -f /var/log/betcontrol/app.log
# Verificar configuración
sudo supervisorctl status betcontrol
```

### Herramientas de Diagnóstico
```bash
# Verificar recursos
htop
df -h
free -m

# Verificar logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/betcontrol/app.log
sudo tail -f /var/log/mysql/error.log

# Verificar conectividad
curl -I http://localhost
curl -I http://localhost:8000/api/health
```

## Verificación Final

Después del despliegue, verificar:

1. **Frontend**: Acceder a https://tudominio.com
2. **Backend**: https://tudominio.com/api/docs (Swagger UI)
3. **Base de datos**: Conexión y consultas básicas
4. **SSL**: Certificado válido y renovación automática
5. **Monitoreo**: Alertas configuradas y funcionando
6. **Backup**: Primer backup creado exitosamente

## Contacto y Soporte

Para problemas técnicos:
- Email: soporte@tudominio.com
- Documentación: https://tudominio.com/docs
- Status Page: https://status.tudominio.com