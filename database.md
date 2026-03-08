rm instance/database.db 
ls instance
rm -rf migrations
flask db init
flask db migrate -m "Initial"
flask db upgrade