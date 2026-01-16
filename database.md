┌──(venv)(daniel㉿kali)-[~/Documents/python-pig-management-system]
└─$ rm instance/database.db 

┌──(venv)(daniel㉿kali)-[~/Documents/python-pig-management-system]
└─$ ls instance

┌──(venv)(daniel㉿kali)-[~/Documents/python-pig-management-system]
└─$ rm -rf migrations

┌──(venv)(daniel㉿kali)-[~/Documents/python-pig-management-system]
└─$ flask db init

┌──(venv)(daniel㉿kali)-[~/Documents/python-pig-management-system]
└─$ flask db migrate -m "Initial"

┌──(venv)(daniel㉿kali)-[~/Documents/python-pig-management-system]
└─$ flask db upgrade