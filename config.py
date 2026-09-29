DB_HOST     = "172.18.16.6"         # IP or hostname of the MySQL server
DB_PORT     = 3306                  # MySQL port (default 3306)
DB_NAME     = "laboratorio"         # Name of your database
DB_USER     = "Labo"                # MySQL user
DB_PASSWORD = "LABO"                # MySQL password

# Connection pool settings
DB_POOL_SIZE        = 10   # Number of persistent connections kept open
DB_MAX_OVERFLOW     = 20   # Extra connections allowed beyond pool_size
DB_POOL_RECYCLE     = 1800 # Seconds before a connection is recycled (avoids stale connections)
DB_POOL_PRE_PING    = True # Test connection health before using it from the pool

DEBUG = True