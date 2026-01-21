# Systemd Service Installation Guide

This guide explains how to install and configure the SMB Image Viewer application as a systemd service for production deployment.

## Prerequisites

- Ubuntu/Debian or other systemd-based Linux distribution
- Root or sudo access
- Python 3.8 or higher installed

## Installation Steps

### 1. Install System Dependencies

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

### 2. Create Application Directory

```bash
sudo mkdir -p /opt/programa-1
sudo chown $USER:$USER /opt/programa-1
```

### 3. Clone or Copy the Application

```bash
cd /opt/programa-1
# If cloning from git
git clone https://github.com/F040204/programa-1.git .
# Or copy your application files to /opt/programa-1
```

### 4. Create Python Virtual Environment

```bash
cd /opt/programa-1
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Create the `.env` file with your configuration:

```bash
sudo cp .env.example /opt/programa-1/.env
sudo nano /opt/programa-1/.env
```

**Important:** Update the following values in `.env`:
- `SECRET_KEY` - Use a strong random key for production
- `SMB_SERVER_IP` - Your SMB server IP address
- `SMB_USERNAME` - SMB username
- `SMB_PASSWORD` - SMB password
- Other SMB configuration as needed

### 6. Create Log Directory

```bash
sudo mkdir -p /var/log/programa-1
sudo chown www-data:www-data /var/log/programa-1
```

### 7. Set Proper Permissions

```bash
sudo chown -R www-data:www-data /opt/programa-1
sudo chmod 640 /opt/programa-1/.env
sudo chmod 755 /opt/programa-1
```

### 8. Install the Systemd Service

```bash
sudo cp /opt/programa-1/programa-1.service /etc/systemd/system/
sudo systemctl daemon-reload
```

### 9. Enable and Start the Service

```bash
# Enable service to start on boot
sudo systemctl enable programa-1

# Start the service
sudo systemctl start programa-1

# Check service status
sudo systemctl status programa-1
```

## Service Management Commands

### Check Service Status
```bash
sudo systemctl status programa-1
```

### Start Service
```bash
sudo systemctl start programa-1
```

### Stop Service
```bash
sudo systemctl stop programa-1
```

### Restart Service
```bash
sudo systemctl restart programa-1
```

### Reload Service (after config changes)
```bash
sudo systemctl reload programa-1
```

### View Logs
```bash
# View systemd journal logs
sudo journalctl -u programa-1 -f

# View access logs
sudo tail -f /var/log/programa-1/access.log

# View error logs
sudo tail -f /var/log/programa-1/error.log
```

### Disable Service
```bash
sudo systemctl disable programa-1
```

## Customization

### Changing the Installation Directory

If you want to install the application in a different directory:

1. Edit the `programa-1.service` file
2. Update all occurrences of `/opt/programa-1` to your desired path
3. Follow the installation steps using your custom path

### Changing the Port

To change the port from 5000 to another port:

1. Edit `/etc/systemd/system/programa-1.service`
2. In the `ExecStart` line, change `--bind 0.0.0.0:5000` to your desired port
3. Reload and restart:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart programa-1
   ```

### Changing the Number of Workers

To adjust the number of gunicorn worker processes:

1. Edit `/etc/systemd/system/programa-1.service`
2. In the `ExecStart` line, change `--workers 4` to your desired number
3. Recommended: 2-4 workers for most setups
4. Reload and restart:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart programa-1
   ```

### Using a Different User

By default, the service runs as `www-data`. To use a different user:

1. Create the user if it doesn't exist:
   ```bash
   sudo useradd -r -s /bin/false programa1
   ```

2. Edit `/etc/systemd/system/programa-1.service`
3. Change `User=www-data` and `Group=www-data` to your user
4. Update permissions:
   ```bash
   sudo chown -R programa1:programa1 /opt/programa-1
   sudo chown -R programa1:programa1 /var/log/programa-1
   ```
5. Reload and restart

## Reverse Proxy Configuration (Optional)

For production, it's recommended to use a reverse proxy like Nginx or Apache.

### Nginx Example

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files (optional)
    location /static {
        alias /opt/programa-1/static;
        expires 30d;
    }
}
```

Install and configure:
```bash
sudo apt install nginx
sudo nano /etc/nginx/sites-available/programa-1
sudo ln -s /etc/nginx/sites-available/programa-1 /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Troubleshooting

### Service Won't Start

1. Check the logs:
   ```bash
   sudo journalctl -u programa-1 -n 50
   ```

2. Verify permissions:
   ```bash
   ls -la /opt/programa-1
   ls -la /opt/programa-1/.env
   ```

3. Test manually:
   ```bash
   cd /opt/programa-1
   source venv/bin/activate
   gunicorn --bind 0.0.0.0:5000 app:app
   ```

### Permission Denied Errors

```bash
sudo chown -R www-data:www-data /opt/programa-1
sudo chmod 640 /opt/programa-1/.env
```

### Database Initialization Fails

```bash
cd /opt/programa-1
source venv/bin/activate
python -c "from app import init_db; init_db()"
```

### SMB Connection Issues

1. Test SMB connectivity:
   ```bash
   cd /opt/programa-1
   source venv/bin/activate
   python test_smb_connection.py
   ```

2. Check `.env` configuration
3. Verify network connectivity to SMB server

## Security Considerations

1. **Never commit `.env` file** - Keep credentials secure
2. **Use strong SECRET_KEY** - Generate with: `python -c 'import secrets; print(secrets.token_hex(32))'`
3. **Change default admin password** - After first login
4. **Use HTTPS in production** - Configure with Let's Encrypt/Certbot
5. **Firewall configuration** - Limit access to necessary ports only
6. **Regular updates** - Keep dependencies updated

## Health Check

The application includes a health check endpoint:

```bash
curl http://localhost:5000/health
```

This can be integrated with monitoring tools like:
- Prometheus
- Nagios
- Zabbix
- Custom monitoring scripts

## Updating the Application

```bash
# Stop the service
sudo systemctl stop programa-1

# Update the code
cd /opt/programa-1
git pull  # or copy new files

# Update dependencies if needed
source venv/bin/activate
pip install -r requirements.txt

# Restart the service
sudo systemctl start programa-1
```

## Support

For issues and questions, refer to the main README.md or contact the development team.
