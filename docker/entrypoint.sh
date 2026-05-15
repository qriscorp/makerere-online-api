#!/bin/bash
set -e

# Update database config from environment variables
if [ -n "$DB_HOST" ]; then
    sed -i "s/'hostname' => '.*'/'hostname' => '${DB_HOST}'/" /var/www/html/application/config/database.php
    sed -i "s/'username' => '.*'/'username' => '${DB_USER}'/" /var/www/html/application/config/database.php
    sed -i "s/'password' => '.*'/'password' => '${DB_PASS}'/" /var/www/html/application/config/database.php
    sed -i "s/'database' => '.*'/'database' => '${DB_NAME}'/" /var/www/html/application/config/database.php
fi

# Mark installer as complete
echo "yes" > /var/www/html/installer/check_install.txt

# Fix permissions
chown -R www-data:www-data /var/www/html/uploads/

# Start Apache
exec apache2-foreground
