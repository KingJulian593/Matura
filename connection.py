import pyodbc
class db_connection(object):
    def __init__(self):
        self.conn_str = f'DRIVER={{MySQL ODBC 8.1 Unicode Driver}};SERVER={"88.200.86.10"};PORT={"3306"};DATABASE={"2024_TA_01"};USER={"2024_TA_01"};PASSWORD={"ui8IkKvdN"};Trusted_Connection=yes;Encrypt=no;'

        try:
            self.connection = pyodbc.connect(self.conn_str,autocommit=True)
            print("Connected")
        except pyodbc.Error as e:
            print("Could not connect to the database:", e)

    
    def get_cursor(self):
        return self.connection.cursor()

