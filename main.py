from send_email import send_email

import sys
from PyQt5 import QtWidgets,QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QBrush,QColor,QIcon,QIntValidator, QRegExpValidator
from PyQt5.uic import loadUi
from PyQt5.QtCore import Qt, QRegExp

from connection import db_connection
import datetime
import bcrypt

session_user = ""

class Login(QDialog):
    def __init__(self):
        super(Login,self).__init__()
        loadUi("login.ui",self)
        self.c = db_connection()
        self.curs = self.c.get_cursor()
        self.LoginButton.clicked.connect(self.login_func)

    def login_func(self):  
        username=self.Username.text()
        password=self.Password.text()
        if self.check_credentials(username,password):
            self.Username.clear()
            self.Password.clear()
            w_stack.setFixedSize(800,600)
            w_stack.setCurrentIndex(w_stack.currentIndex()+1)
        else:   
            QMessageBox.critical(w_stack,"Fail","Wrong username or password")

    def check_credentials(self, username, password):
        # Poizvedba za pridobitev uporabniškega imena in gesla iz baze
        self.curs.execute("SELECT username, hashed FROM employees NATURAL JOIN passwords WHERE employees.username = ?",(username,)
        )
        result = self.curs.fetchone()

        # če uporabniško ime ne obstaja, vrni False
        if not result:
            QMessageBox.critical(w_stack,"Fail","User doesn't exist")
            return False

        db_username, db_hashed_password = result
        print(db_username, str(db_hashed_password))
        # Pretvori geslo v bajtno obliko
        password_bytes = password.encode("utf-8")

        # Preveri geslo z bcrypt
        if bcrypt.checkpw(password_bytes, db_hashed_password) and db_username == username:
            global session_user
            session_user = db_username
            return True

        return False
    
class Medicine(QDialog):
    def __init__(self):
        super(Medicine,self).__init__()
        loadUi("medicine.ui",self)
        self.c = db_connection()
        self.Search.clicked.connect(self.search_func)
        self.reset_table.clicked.connect(self.reset)
        self.Medicine.clicked.connect(self.go_to_medicine)
        self.Orders.clicked.connect(self.go_to_orders)
        self.Shipments.clicked.connect(self.go_to_shipments)
        self.add_employee.clicked.connect(self.add_employee_func) 
        self.logout.clicked.connect(self.log_out_func)    
        self.profile.clicked.connect(self.view_profile)   
        
        self.Table.setColumnWidth(4,90)
        self.Table.setColumnWidth(1,60)
        self.loaddata()
        
        self.name.setValidator(QRegExpValidator(QRegExp("[a-zA-Z]*")))

    def view_profile(self):
        global session_user
        self.prof = Profil(session_user)
        self.prof.setWindowIcon(QIcon('cross.jpg'))
        self.prof.show()

    def go_to_medicine(self):
        w_stack.setCurrentIndex(w_stack.currentIndex())
        self.loaddata()

    def go_to_orders(self):
        w_stack.setCurrentIndex(2)

    def go_to_shipments(self):
        w_stack.setCurrentIndex(3)

    def log_out_func(self):
        w_stack.setCurrentIndex(0)
        w_stack.setFixedSize(554,600)

    def add_employee_func(self):
        global session_user
        self.curs = self.c.get_cursor()
        self.curs.execute("SELECT admin FROM employees WHERE username=?",session_user)
        result = self.curs.fetchone()
        admin_status = result[0]
        if admin_status == 1:
            self.new = New_employee(self)
            self.new.show()
        else:
            QMessageBox.critical(w_stack,"WARNING","You do not have admin privileges!")

    def reset(self):
        self.name.clear()
        self.dose.clear()
        self.loc.clear()
        self.code.clear()
        self.quantity.setValue(0)
        self.loaddata()

    def loaddata(self):
        self.curs = self.c.get_cursor()
        
        self.Table.clear()
        headers = ["Name", "Dose", "Warehouse loc", "Code", "Quantity"]
        for i, header in enumerate(headers):
            self.Table.setHorizontalHeaderItem(i, QtWidgets.QTableWidgetItem(header))

        self.curs.execute("SELECT COUNT(name) FROM medicine")
        self.Table.setRowCount((int(self.curs.fetchone()[0])))
        
        self.curs.execute("SELECT * FROM medicine")
        row = self.curs.fetchone()
        row_i =0
        while row:
            self.Table.setItem(row_i,0,QtWidgets.QTableWidgetItem(row[0]))
            self.Table.setItem(row_i,1,QtWidgets.QTableWidgetItem(str(row[6])+"mg"))
            self.Table.setItem(row_i,2,QtWidgets.QTableWidgetItem(row[2]))
            self.Table.setItem(row_i,3,QtWidgets.QTableWidgetItem(row[1]))
            self.Table.setItem(row_i,4,QtWidgets.QTableWidgetItem(str(row[5])))
            row = self.curs.fetchone()
            row_i+=1
        self.curs.close()

    def search_func(self):
        name = self.name.text()
        dose = self.dose.text()
        loc = self.loc.text()
        code = self.code.text()
        quantity = self.quantity.text()

        if all(field == '' for field in [name, dose, loc, code]) and quantity == '0':
            QMessageBox.critical(w_stack, "Fail", "Enter search parameters")
            return

        quantity = int(quantity) if quantity else 0
        if quantity != 0 and not any([self.more.isChecked(), self.less.isChecked(), self.Equal.isChecked()]):
            QMessageBox.critical(w_stack, "Fail", "Check the correct quantity box")
            return

        self.curs = self.c.get_cursor()
        operator = ''
        if self.more.isChecked():
            operator = '>'
        elif self.less.isChecked():
            operator = '<'
        elif self.Equal.isChecked():
            operator = '='

        filters = ["name LIKE ?", "warehouse_location LIKE ?", "code LIKE ?"]
        params = [f"%{name}%", f"%{loc}%", f"%{code}%"]

        if dose:
            filters.append("dose = ?")
            params.append(dose)
        if operator:
            filters.append(f"quantity {operator} ?")
            params.append(quantity)

        where_clause = " AND ".join(filters)
        count_query = f"SELECT COUNT(*) FROM medicine WHERE {where_clause}"
        data_query = f"SELECT * FROM medicine WHERE {where_clause}"

        self.Table.clear()
        headers = ["Name", "Dose", "Warehouse loc", "Code", "Quantity"]
        for i, header in enumerate(headers):
            self.Table.setHorizontalHeaderItem(i, QtWidgets.QTableWidgetItem(header))

        self.curs.execute(count_query, params)
        self.Table.setRowCount(int(self.curs.fetchone()[0]))

        self.curs.execute(data_query, params)
        for row_i, row in enumerate(self.curs.fetchall()):
            self.Table.setItem(row_i, 0, QtWidgets.QTableWidgetItem(row[0]))
            self.Table.setItem(row_i, 1, QtWidgets.QTableWidgetItem(f"{row[6]}mg"))
            self.Table.setItem(row_i, 2, QtWidgets.QTableWidgetItem(row[2]))
            self.Table.setItem(row_i, 3, QtWidgets.QTableWidgetItem(row[1]))
            self.Table.setItem(row_i, 4, QtWidgets.QTableWidgetItem(str(row[5])))

        self.curs.close()

class Orders(QDialog):
    def __init__(self):
        super(Orders,self).__init__()
        loadUi("orders.ui",self)
        self.c = db_connection()
        self.Medicine.clicked.connect(self.go_to_medicine)
        self.Orders.clicked.connect(self.go_to_orders)
        self.Shipments.clicked.connect(self.go_to_shipments)
        self.add_employee.clicked.connect(self.add_employee_func)
        self.Create_dispatch.clicked.connect(self.create_dispatch)
        self.Complete_dispatch.clicked.connect(self.complete_dispatch)
        self.logout.clicked.connect(self.log_out_func)  
        self.profile.clicked.connect(self.view_profile) 
        
        self.Table_orders.setColumnWidth(2,140)
        self.Table_orders.setColumnWidth(4,110)
        self.Table_orders.setColumnWidth(5,80)

        self.Table_dispatched.setColumnWidth(3,120)
        self.Table_dispatched.setColumnWidth(0,80)

        self.Table_orders.selectionModel().selectionChanged.connect(self.selected_item_orders)
        self.Table_dispatched.selectionModel().selectionChanged.connect(self.selected_item_dispatched)

        self.selected_order_id = None
        self.selected_dispatch_id = None

        self.load_data_orders()
        self.load_data_dispatch()

    def view_profile(self):
        global session_user
        self.prof = Profil(session_user)
        self.prof.setWindowIcon(QIcon('cross.jpg'))
        self.prof.show()

    def go_to_shipments(self):
        w_stack.setCurrentIndex(3)

    def go_to_medicine(self):
        w_stack.setCurrentIndex(1)
        medicine.loaddata()
    
    def log_out_func(self):
        w_stack.setCurrentIndex(0)
        w_stack.setFixedSize(554,600)

    def go_to_orders(self):
        w_stack.setCurrentIndex(w_stack.currentIndex())
        self.load_data_dispatch()
        self.load_data_orders()

    def add_employee_func(self):
        global session_user
        self.curs = self.c.get_cursor()
        self.curs.execute("SELECT admin FROM employees WHERE username=?",session_user)
        result = self.curs.fetchone()
        admin_status = result[0]
        if admin_status == 1:
            self.new = New_employee(self)
            self.new.show()
        else:
            QMessageBox.critical(w_stack,"WARNING","You do not have admin privileges!")

    def load_data_orders(self):
        self.Table_orders.clear()

        self.Table_orders.setHorizontalHeaderItem(0, QtWidgets.QTableWidgetItem("OrderID"))
        self.Table_orders.setHorizontalHeaderItem(1, QtWidgets.QTableWidgetItem("Customer"))
        self.Table_orders.setHorizontalHeaderItem(2, QtWidgets.QTableWidgetItem("Address"))
        self.Table_orders.setHorizontalHeaderItem(3, QtWidgets.QTableWidgetItem("Order date"))
        self.Table_orders.setHorizontalHeaderItem(4, QtWidgets.QTableWidgetItem("Ordered medicine"))
        self.Table_orders.setHorizontalHeaderItem(5, QtWidgets.QTableWidgetItem("Quantity"))
        self.Table_orders.setHorizontalHeaderItem(6, QtWidgets.QTableWidgetItem("Status"))

        self.curs = self.c.get_cursor()

        self.curs.execute("SELECT COUNT(order_id) FROM orders")
        self.Table_orders.setRowCount((int(self.curs.fetchone()[0])))

        self.curs.execute("SELECT order_id,customer_name,delivery_address,order_date,name,ordered_medicine_quantity,order_status FROM orders JOIN medicine ON orders.ordered_medicine_code=medicine.code")
        row = self.curs.fetchone()
        row_i =0
        while row:
            self.Table_orders.setItem(row_i,0,QtWidgets.QTableWidgetItem(str(row[0])))
            self.Table_orders.setItem(row_i,1,QtWidgets.QTableWidgetItem(row[1]))
            self.Table_orders.setItem(row_i,2,QtWidgets.QTableWidgetItem(row[2]))
            self.Table_orders.setItem(row_i,3,QtWidgets.QTableWidgetItem(str(row[3])))
            self.Table_orders.setItem(row_i,4,QtWidgets.QTableWidgetItem(row[4]))
            self.Table_orders.setItem(row_i,5,QtWidgets.QTableWidgetItem(str(row[5])))
            self.Table_orders.setItem(row_i,6,QtWidgets.QTableWidgetItem(row[6]))
            row = self.curs.fetchone()
            row_i+=1
        self.curs.close()

    def selected_item_orders(self,selected,deselected):    
        for i in selected.indexes():
            if i.column() == 0:
                self.selected_row = i.row()
                self.selected_column = i.column()
                self.selected_order_id = int(self.Table_orders.item(self.selected_row,self.selected_column).text())
            else:
                self.selected_order_id = None
    
    def selected_item_dispatched(self,selected,deselected):
        for i in selected.indexes():
            print("selected row: {0}, column {1}".format(i.row(),i.column( )))
            if i.column() == 0:
                self.selected_row = i.row()
                self.selected_column = i.column()
                self.selected_dispatch_id = int(self.Table_dispatched.item(self.selected_row,self.selected_column).text())
                print(self.selected_dispatch_id)
            else:
                self.selected_dispatch_id = None

    def create_dispatch(self):
        if self.selected_order_id:
            self.curs = self.c.get_cursor()
            self.curs.execute("SELECT * FROM orders WHERE order_id="+str(self.selected_order_id))
            item = self.curs.fetchone()

            x = datetime.datetime.now()
            date= (x.strftime("%Y")+"-"+x.strftime("%m")+"-"+x.strftime("%d"))
            
            self.curs.execute("INSERT INTO dispatches(medicine_code,receiving_party,destination,dispatched_quantity,dispatch_date,dispatch_status) values(?,?,?,?,?,?)",item[4],item[1],item[2],item[5],date,'Shipped')
            self.curs.execute("DELETE FROM orders WHERE order_id="+str(self.selected_order_id))
            self.curs.execute("UPDATE medicine SET medicine.quantity=medicine.quantity-? WHERE medicine.code=?",(item[5],item[4]))
            self.load_data_orders()
            self.load_data_dispatch()
        else:
            QMessageBox.critical(w_stack,"Fail","Select order ID in orders table")

    def complete_dispatch(self):
        if self.selected_dispatch_id:
            self.curs = self.c.get_cursor()
            self.curs.execute("UPDATE dispatches SET dispatch_status='Completed' WHERE dispatch_id="+str(self.selected_dispatch_id))
            self.load_data_orders()
            self.load_data_dispatch()
        else:
            QMessageBox.critical(w_stack,"Fail","Select dispatch ID in dispatch table")

    def load_data_dispatch(self):
        self.Table_dispatched.clear()

        self.Table_dispatched.setHorizontalHeaderItem(0, QtWidgets.QTableWidgetItem("Id"))
        self.Table_dispatched.setHorizontalHeaderItem(1, QtWidgets.QTableWidgetItem("Customer"))
        self.Table_dispatched.setHorizontalHeaderItem(2, QtWidgets.QTableWidgetItem("Dispatch date"))
        self.Table_dispatched.setHorizontalHeaderItem(3, QtWidgets.QTableWidgetItem("Dispatched medicine"))
        self.Table_dispatched.setHorizontalHeaderItem(4, QtWidgets.QTableWidgetItem("Quantity"))
        self.Table_dispatched.setHorizontalHeaderItem(5, QtWidgets.QTableWidgetItem("Status"))

        self.curs = self.c.get_cursor()

        self.curs.execute("SELECT COUNT(dispatch_id) FROM dispatches")
        self.Table_dispatched.setRowCount((int(self.curs.fetchone()[0])))

        self.curs.execute("SELECT dispatch_id,receiving_party,dispatch_date,name,dispatched_quantity,dispatch_status FROM dispatches JOIN medicine ON dispatches.medicine_code=medicine.code")
        row = self.curs.fetchone()
        row_i =0
        while row:
            
            self.Table_dispatched.setItem(row_i,0,QtWidgets.QTableWidgetItem(str(row[0])))
            self.Table_dispatched.setItem(row_i,1,QtWidgets.QTableWidgetItem(row[1]))
            self.Table_dispatched.setItem(row_i,2,QtWidgets.QTableWidgetItem(str(row[2])))
            self.Table_dispatched.setItem(row_i,3,QtWidgets.QTableWidgetItem(row[3]))
            self.Table_dispatched.setItem(row_i,4,QtWidgets.QTableWidgetItem(str(row[4])))
            if row[5]=="Completed":
                item = QtWidgets.QTableWidgetItem(row[5])
                item.setForeground(QBrush(QColor(56, 184, 2)))
                self.Table_dispatched.setItem(row_i,5,item)
            else:
                self.Table_dispatched.setItem(row_i,5,QtWidgets.QTableWidgetItem(row[5]))
            row = self.curs.fetchone()
            row_i+=1
        self.curs.close()

        self.Table_dispatched.sortItems(5,Qt.DescendingOrder)

class Shipments(QDialog):
    def __init__(self):
        super(Shipments,self).__init__()
        loadUi("shipments.ui",self)
        self.c = db_connection()

        self.Medicine.clicked.connect(self.go_to_medicine)
        self.Orders.clicked.connect(self.go_to_orders)
        self.Shipments.clicked.connect(self.go_to_shipments)
        self.Receive_shipment.clicked.connect(self.receive_shipment)
        self.Order_new.clicked.connect(self.order)
        self.add_employee.clicked.connect(self.add_employee_func)
        self.logout.clicked.connect(self.log_out_func)  
        self.profile.clicked.connect(self.view_profile) 

        self.selected_shipment_id = None
        self.Table_shipments.selectionModel().selectionChanged.connect(self.selected_item_shipments)

        self.Table_shipments.setColumnWidth(2,160)
        self.Table_shipments.setColumnWidth(0,80)

        self.loaddata()

    def view_profile(self):
        global session_user
        self.prof = Profil(session_user)
        self.prof.setWindowIcon(QIcon('cross.jpg'))
        self.prof.show()

    def go_to_shipments(self):
        w_stack.setCurrentIndex(w_stack.currentIndex())
        self.loaddata()

    def go_to_medicine(self):
        w_stack.setCurrentIndex(1)
        medicine.loaddata()

    def log_out_func(self):
        w_stack.setCurrentIndex(0)
        w_stack.setFixedSize(554,600)

    def go_to_orders(self):
        w_stack.setCurrentIndex(2)

    def loaddata(self):
        self.Table_shipments.clear()

        self.Table_shipments.setHorizontalHeaderItem(0, QtWidgets.QTableWidgetItem("ShipmentID"))
        self.Table_shipments.setHorizontalHeaderItem(1, QtWidgets.QTableWidgetItem("Medicine"))
        self.Table_shipments.setHorizontalHeaderItem(2, QtWidgets.QTableWidgetItem("Supplier"))
        self.Table_shipments.setHorizontalHeaderItem(3, QtWidgets.QTableWidgetItem("Quantity"))
        self.Table_shipments.setHorizontalHeaderItem(4, QtWidgets.QTableWidgetItem("Shipment date"))
        self.Table_shipments.setHorizontalHeaderItem(5, QtWidgets.QTableWidgetItem("Status"))
        self.Table_shipments.setHorizontalHeaderItem(6, QtWidgets.QTableWidgetItem("Receive date"))
        
        self.curs = self.c.get_cursor()

        self.curs.execute("SELECT COUNT(shipment_id) FROM shipments")
        self.Table_shipments.setRowCount((int(self.curs.fetchone()[0])))

        self.curs.execute("SELECT shipment_id,name,supplier,quantity_received,shipment_date,shipment_status,receive_date FROM shipments JOIN medicine ON shipments.medicine_code=medicine.code ")
        row = self.curs.fetchone()
        row_i =0
        while row:
            self.Table_shipments.setItem(row_i,0,QtWidgets.QTableWidgetItem(str(row[0])))
            self.Table_shipments.setItem(row_i,1,QtWidgets.QTableWidgetItem(row[1]))
            self.Table_shipments.setItem(row_i,2,QtWidgets.QTableWidgetItem(row[2]))
            self.Table_shipments.setItem(row_i,3,QtWidgets.QTableWidgetItem(str(row[3])))
            self.Table_shipments.setItem(row_i,4,QtWidgets.QTableWidgetItem(str(row[4])))
            if row[5]=="Received":
                item = QtWidgets.QTableWidgetItem(row[5])
                item.setForeground(QBrush(QColor(56, 184, 2)))
                self.Table_shipments.setItem(row_i,5,item)
            else:
                self.Table_shipments.setItem(row_i,5,QtWidgets.QTableWidgetItem(row[5]))
            self.Table_shipments.setItem(row_i,6,QtWidgets.QTableWidgetItem(str(row[6])))
            row = self.curs.fetchone()
            row_i+=1
        self.curs.close()

        self.Table_shipments.sortItems(5,Qt.AscendingOrder)

    def selected_item_shipments(self,selected,deselected):    
        for i in selected.indexes():
            print("selected row: {0}, column {1}".format(i.row(),i.column( )))
            if i.column() == 0:
                self.selected_row = i.row()
                self.selected_column = i.column()
                self.selected_shipment_id = int(self.Table_shipments.item(self.selected_row,self.selected_column).text())
                print(self.selected_shipment_id)
            else:
                self.selected_shipment_id = None
    
    def receive_shipment(self):
        self.curs = self.c.get_cursor()
        self.curs.execute("SELECT shipment_status FROM shipments WHERE shipment_id="+str(self.selected_shipment_id))
        status = self.curs.fetchone()
        if status[0] != 'Received':
            if self.selected_shipment_id:
                self.curs = self.c.get_cursor()
                self.curs.execute("UPDATE shipments SET shipment_status='Received' WHERE shipment_id="+str(self.selected_shipment_id))

                x = datetime.datetime.now()
                date= (x.strftime("%Y")+"-"+x.strftime("%m")+"-"+x.strftime("%d"))

                self.curs.execute("UPDATE shipments SET receive_date=? WHERE shipment_id="+str(self.selected_shipment_id),date)

                self.curs.execute("SELECT quantity_received,medicine_code FROM shipments WHERE shipment_id="+str(self.selected_shipment_id))
                x=self.curs.fetchone()
                print(x[0])

                self.curs.execute("UPDATE medicine SET medicine.quantity=medicine.quantity+? WHERE medicine.code=?",(x[0],x[1]))

                self.loaddata()
            else:
                QMessageBox.critical(w_stack,"Fail","Select shipment ID in shipment table")
        else:
            QMessageBox.critical(w_stack,"Fail","Shipment has already been received")

    def order(self):
        self.dialog = New_order()
        self.dialog.show()

    def add_employee_func(self):
        global session_user
        self.curs = self.c.get_cursor()
        self.curs.execute("SELECT admin FROM employees WHERE username=?",session_user)
        result = self.curs.fetchone()
        admin_status = result[0]
        if admin_status == 1:
            self.new = New_employee(self)
            self.new.show()
        else:
            QMessageBox.critical(w_stack,"WARNING","You do not have admin privileges!")

class New_order(QDialog):
    def __init__(self):
        super().__init__()
        self.conn = db_connection()
        self.c = self.conn.get_cursor()
        loadUi("new_order.ui",self)                    

        self.setWindowIcon(QIcon("cross.jpg"))
        self.setWindowTitle("Order more")

        okBtn = self.buttonBox.button(QDialogButtonBox.Ok) 
        okBtn.clicked.connect(self.confirm)

        cancelBtn = self.buttonBox.button(QDialogButtonBox.Cancel)
        cancelBtn.clicked.connect(self.quit) 

        resetBtn = self.buttonBox.button(QDialogButtonBox.Reset)
        resetBtn.clicked.connect(self.reset)


        self.c.execute("SELECT count(name) FROM medicine")
        i = self.c.fetchone()
        index = i[0]
        medicine_names = []
        self.c.execute("SELECT name FROM medicine")
        for i in range(index):
            item = self.c.fetchone()
            medicine_names.append(item[0])
    
        print(medicine_names)
        self.medicine_name.addItems(medicine_names)

        firms = [
            "NeuroGenix",
            "MedicaNova",
            "BioSyn",
            "AegisPharm",
            "VitaCure",
            "ZenithMeds",
            "OmniHealth",
            "NexGenPharma",
            "CelestiCare",
            "VeritasPharm"
        ]

        self.supplier.addItems(firms)

        self.medicine_name.activated.connect(self.update_medicine_code)

        self.medicine_name.setCurrentIndex(-1)
        self.supplier.setCurrentIndex(-1)

    def update_medicine_code(self):       
        self.c.execute("SELECT medicine.code FROM medicine WHERE medicine.name=?",self.medicine_name.currentText())
        code = self.c.fetchone()
        self.medicine_code.clear()
        self.medicine_code.insert(str(code[0]))

    def confirm(self):
        print("ok")
        print(self.medicine_name.currentText())
        print(self.supplier.currentText())
        print(self.quantity.value())

        if self.medicine_name.currentText() == "" or self.supplier.currentText() == "" or self.quantity.value() == 0:
            QMessageBox.critical(w_stack,"Fail","Please fill all fields")
            return

        x = datetime.datetime.now()
        date= (x.strftime("%Y")+"-"+x.strftime("%m")+"-"+x.strftime("%d"))

        self.c.execute("INSERT INTO shipments(medicine_code,supplier,quantity_received,shipment_date,shipment_status) values (?,?,?,?,?)",(self.medicine_code.text(),self.supplier.currentText(),self.quantity.value(),date,'Incoming'))
        shipments.loaddata()
        QMessageBox.information(w_stack,"INFO","New order added succsessfully!")

    def quit(self):
        pass

    def reset(self):
        self.medicine_name.setCurrentIndex(-1)
        self.supplier.setCurrentIndex(-1)
        self.medicine_code.clear()

class New_employee(QDialog):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setWindowIcon(QIcon("cross.jpg"))
        self.conn = db_connection()
        self.c = self.conn.get_cursor()
        loadUi("new_employee.ui",self)

        okBtn = self.buttonBox.button(QDialogButtonBox.Ok) 
        okBtn.clicked.connect(self.confirm)

        cancelBtn = self.buttonBox.button(QDialogButtonBox.Cancel)
        cancelBtn.clicked.connect(self.quit) 

        resetBtn = self.buttonBox.button(QDialogButtonBox.Reset)
        resetBtn.clicked.connect(self.reset)
        
        warehouse_jobs = [
            "Inventory Clerk",
            "Forklift Operator",
            "Warehouse Manager",
            "Picker/Packer",
            "Shipping and Receiving Associate"
        ]
        self.position.addItems(warehouse_jobs)
        self.position.setCurrentIndex(-1)

    def quit(self):
        pass

    def reset(self):
        self.first_name.clear()
        self.last_name.clear()
        self.tel_num.clear()
        self.email.clear()
        self.position.setCurrentIndex(-1)

    def confirm(self):
        if self.first_name.text() == "" or self.last_name.text() == "" or self.tel_num.text() == "" or self.email.text() == "" or self.position.currentText() == "":
            QMessageBox.critical(w_stack,"Fail","Please fill all fields")
            return
        self.f_name = (self.first_name.text()).capitalize()
        self.l_name = (self.last_name.text()).capitalize()
        self.tel_num = self.tel_num.text()
        self.em = self.email.text()
        self.position = self.position.currentText()
        self.username = self.f_name[0]+self.l_name
        self.username_b = self.username.encode("utf-8")
        
        self.c.execute("INSERT INTO employees (first_name, last_name, telephone, email, position, username,admin) VALUES (?,?,?,?,?,?,?)",(self.f_name,self.l_name,self.tel_num,self.em,self.position,self.username,0))

        self.c.execute("SELECT employee_code FROM employees WHERE email=? ",self.em)
        code = self.c.fetchone()
        
        send_email(self.username,self.username,self.em)

        user_password = bcrypt.hashpw(self.username_b, bcrypt.gensalt())
        self.c.execute("INSERT INTO passwords (employee_code,hashed) VALUES (?,?)",(code[0],user_password))

        QMessageBox.information(w_stack,"INFO","New employee added succsessfully!")

class Profil(QDialog):
    def __init__(self,session_user):
        username=""
        super(Profil,self).__init__()
        loadUi("profile.ui",self)
        self.c = db_connection()
        self.curs = self.c.get_cursor()
        self.curs.execute("SELECT * FROM employees WHERE username=?",session_user)
        result = self.curs.fetchone()
        name = result[1]+result[2]
        telephone= result[3]
        e_mail = result[4]
        position = result[5]
        self.username = result[6]
        self.Name.setText(name)
        self.e_mail.setText(e_mail)
        self.telephone.setText(telephone)
        self.position.setText(position)
        self.username_label.setText(self.username)

        self.changePassword.clicked.connect(self.change_pass)

    def change_pass(self):
        self.c = Change_pass(self.username)
        self.c.setWindowIcon(QIcon('cross.jpg'))
        self.c.show()

class Change_pass(QDialog):
    def __init__(self,username):
        super().__init__()
        loadUi("change_pass.ui",self)  

        self.conn = db_connection()
        self.curs = self.conn.get_cursor()

        self.curs.execute("SELECT employee_code,hashed FROM employees NATURAL JOIN passwords WHERE username=?",username)
        self.user_cred = self.curs.fetchone()

        okBtn = self.buttonBox.button(QDialogButtonBox.Ok) 
        okBtn.clicked.connect(self.confirm)

        cancelBtn = self.buttonBox.button(QDialogButtonBox.Cancel)
        cancelBtn.clicked.connect(self.quit) 

        resetBtn = self.buttonBox.button(QDialogButtonBox.Reset)
        resetBtn.clicked.connect(self.reset)

    def quit(self):
        pass

    def reset(self):
        self.old_pass.clear()
        self.new_pass.clear()
        self.new_pass_rep.clear()

    def confirm(self):
        old_pass = self.old_pass.text()
        new_pass = self.new_pass.text()
        new_pass_rep = self.new_pass_rep.text()

        if not old_pass or not new_pass or not new_pass_rep:
            QMessageBox.warning(w_stack,"Error","Please fill all fields")
            return

        if new_pass != new_pass_rep:
            QMessageBox.warning(w_stack,"Error","New password and repeated password do not match")
            return

        if bcrypt.checkpw(old_pass.encode('utf-8'),self.user_cred[1]):
            hashed = bcrypt.hashpw(new_pass.encode('utf-8'),bcrypt.gensalt())
            self.curs.execute("UPDATE passwords SET hashed=? WHERE employee_code=?",hashed,self.user_cred[0])
            print(self.user_cred[0])
            QMessageBox.information(w_stack,"Success","Password changed successfully")
            self.close()
        else:
            QMessageBox.warning(w_stack,"Error","Old password is incorrect")

class StackedWidget(QStackedWidget):
    def __init__(self):
        super(StackedWidget,self).__init__()

    def closeEvent(self, event):
        # Ask for confirmation before closing
        confirmation = QMessageBox.question(self, "Confirmation", "Are you sure you want to close the application?", QMessageBox.Yes | QMessageBox.No)

        if confirmation == QMessageBox.Yes:
            event.accept()  # Close the app
        else:
            event.ignore()  # Don't close the app
    

app=QApplication(sys.argv)
login=Login()
medicine = Medicine()
orders = Orders()
shipments = Shipments()
w_stack = StackedWidget()
w_stack.setWindowIcon(QIcon('cross.jpg'))
w_stack.setWindowTitle("Lekarniški center Otočec")
w_stack.addWidget(login)
w_stack.addWidget(medicine)
w_stack.addWidget(orders)
w_stack.addWidget(shipments)
w_stack.setFixedSize(554,600)
w_stack.show()   
app.exec_()
