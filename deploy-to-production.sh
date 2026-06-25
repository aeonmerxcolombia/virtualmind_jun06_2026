#!/bin/bash
# Deploy staging → production
# Uso: sudo ./deploy-to-production.sh
# 1. Asegúrate de tener todo commiteado en staging
# 2. Crea un PR en GitHub: staging → main
# 3. Después del merge, ejecuta este script

set -e

echo "=== 1. Pull latest main from GitHub ==="
cd /var/www/html
git checkout main
git pull origin main

echo "=== 2. Fix permissions ==="
chown -R www-data:www-data /var/www/html/
chmod -R u+rwX,go+rX /var/www/html/

echo "=== 3. Reload Apache ==="
apache2ctl configtest && systemctl reload apache2

echo "=== ✅ Deploy completado ==="
echo "Producción actualizada con los cambios de main."
