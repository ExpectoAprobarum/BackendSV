from pony.orm import Database
from src.conf.config import mysql_conf

db = Database()

#Default configuration for sqlite
db.bind('sqlite', 'database.sqlite', create_db=True)

#Configuration for external databases
#db.bind(provider=mysql_conf['provider'], host=mysql_conf['host'], user=mysql_conf['user'], passwd=mysql_conf['passwd'],
#        db=mysql_conf['db'])    