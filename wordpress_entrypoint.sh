#!/bin/bash
# Set ServerName to the environment variable SERVER_NAME, defaulting to localhost if not set
echo "ServerName ${SERVER_NAME:-localhost}" >> /etc/apache2/apache2.conf

# Call the original entrypoint script that comes with the official WordPress image
exec docker-entrypoint.sh apache2-foreground
