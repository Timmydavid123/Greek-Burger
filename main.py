import re
import bcrypt
import sys
import sqlite3
import csv
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QDialog, QTextEdit, QApplication, QMainWindow, QStackedWidget
from PyQt5.uic import loadUi
from PyQt5.QtGui import QFont
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from receipt_dialog import ReceiptDialog  
from main_window import Ui_MainWindow

# Create a database connection
conn = sqlite3.connect('GreekBurger.db')
cursor = conn.cursor()

conn.commit()
# Create a table to store user data if it doesn't exist
cursor.execute('''CREATE TABLE IF NOT EXISTS users
                  (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   email TEXT NOT NULL,
                   password TEXT NOT NULL
                   )''')


cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        food_item TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        shipping_address TEXT NOT NULL,
        city TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    );
''')    
conn.commit()


class MenuDialog(QDialog):
    def __init__(self, widget, main_window):
        super(MenuDialog, self).__init__()
        self.setGeometry(0, 0, 480, 620)
        loadUi("menu.ui", self)
        self.widget = widget
        self.main_window = main_window
        self.B2.clicked.connect(self.order)
        self.take_order_button.clicked.connect(self.show_payment_dialog)
        self.total_amount = 0  # Initialize the total amount

    def order(self):
        total = 0
        vat_rate = 0.075
        # Define a dictionary to map food items to their prices
        food_prices = {
            "C1": 7000,
            "C2": 7000,
            "C3": 7000,
            "C4": 70000,
            "C5": 1000,
            "C6": 1000,
            "C7": 1000,
            "C8": 1000,
            "C9": 3500,
            "C10": 4000,
            "C11": 3500,
            "C12": 3500,
        }

        # Iterate through the CheckBoxes and calculate the total
        checkboxes = self.findChildren(QtWidgets.QCheckBox)
        for checkbox in checkboxes:
            if checkbox.isChecked():
                food_name = checkbox.objectName()
                price = food_prices[food_name]
                total += price

        # Calculate VAT
        vat = total * vat_rate

        # Calculate the final total including VAT
        total_with_vat = total + vat

        # Set the values in Line Edits
        self.L13.setText(str(total))
        self.L14.setText(str(vat))
        self.L15.setText(str(total_with_vat))
        self.total_amount = str(total_with_vat)  # Update the total amount


    def show_payment_dialog(self):
        payment_dialog = PaymentDialog(self.widget, self.main_window, self)  # Pass self as the parent_widget
        self.widget.addWidget(payment_dialog)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)
        self.hide()  # Hide the MenuDialog

class PaymentDialog(QDialog):
    def __init__(self, widget, main_window, parent_widget):
        super(PaymentDialog, self).__init__(main_window)
        self.widget = widget
        self.parent_widget = parent_widget  # Store the parent widget as an instance variable
        loadUi("payment.ui", self)
        self.pay_now.clicked.connect(self.process_payment)

    def process_payment(self):
        # Get the credit card details
        credit_card_number = self.credit_card_number_line_edit.text()
        cvv = self.cvv_line_edit.text()
        expiry_date = self.expiry_date_line_edit.text()

        shipping_address = self.shipping_address_line_edit.text()
        city = self.city_line_edit.text()
        state = self.state_province_line_edit.text()
        zipcode = self.zip_code.text()

        # Credit Card Number Validation
        if not re.match(r'^\d{16,19}$', credit_card_number):
            self.display_error_message("Invalid credit card number format")
            return

        # CVV Validation
        if not re.match(r'^\d{3,4}$', cvv):
            self.display_error_message("Invalid CVV format")
            return

        # Expiry Date Validation
        try:
            month, year = map(int, expiry_date.split('/'))
            current_year = datetime.now().year % 100
            if year < current_year or month < 1 or month > 12:
                self.display_error_message("Invalid expiry date")
                return
        except ValueError:
            self.display_error_message("Invalid expiry date format (use MM/YY)")
            return

        # Shipping Address Validation
        if not re.match(r'^\d+\s[\w\s]+$', shipping_address):
            self.display_error_message("Invalid shipping address format")
            return

        # City Validation
        if not re.match(r'^[A-Za-z\s]+$', city):
            self.display_error_message("Invalid city format")
            return

        # State Validation
        if not re.match(r'^[A-Za-z\s]+$', state):
            self.display_error_message("Invalid state format")
            return

        # ZIP Code Validation
        if not re.match(r'^\d{6}$', zipcode):
            self.display_error_message("Invalid ZIP code format")
            return

        # If all validations pass, you can proceed with your payment processing logic here

        # Display a payment successful message
        QtWidgets.QMessageBox.information(self, "Payment Successful", "Payment was successful!")


        # Create and show the ReceiptDialog
        receipt_dialog = ReceiptDialog(self.widget, self.parent_widget.total_amount, shipping_address, city, state)
        receipt_dialog.exec_()
        
        # Hide the PaymentDialog
        self.hide()
        
        self.insert_order_data(self.parent_widget.total_amount, shipping_address, city)
    
        thanks_dialog = ThanksDialog(self.parent_widget, self.parent_widget.total_amount, shipping_address)
        # Set a central widget for the main_window
        self.parent_widget.main_window.setCentralWidget(thanks_dialog)

        # Show the ThanksDialog
        thanks_dialog.show()


    def display_error_message(self, message):
        error_label = self.findChild(QtWidgets.QLabel, "error_label")

        font = QtGui.QFont()
        font.setPointSize(12)
        error_label.setFont(font)

        error_label.setText(message)
        error_label.setAlignment(QtCore.Qt.AlignCenter)
        error_label.setStyleSheet("color: red")

        # Optionally clear the LineEdit fields if needed
        self.credit_card_number_line_edit.clear()
        self.cvv_line_edit.clear()
        self.expiry_date_line_edit.clear()
        self.shipping_address_line_edit.clear()
        self.city_line_edit.clear()
        self.state_province_line_edit.clear()
        self.zip_code.clear()
        
    def insert_order_data(self, total_amount, shipping_address, city):
        # Get the user's ID using their email
        email = "email"  # You should replace this with the user's email
        cursor.execute("SELECT id FROM users WHERE email=?", (email,))
        result = cursor.fetchone()
        
        if result is not None:
            user_id = result[0]

            # Iterate through the selected food items and insert orders
            checkboxes = self.parent_widget.findChildren(QtWidgets.QCheckBox)
            for checkbox in checkboxes:
                if checkbox.isChecked():
                    food_name = checkbox.objectName()
                    food_item = food_name

                    # Set a fixed quantity (you can adjust this as needed)
                    quantity = 1  # Set a fixed quantity or calculate it as needed

                    # Insert the order into the database
                    cursor.execute(
                        "INSERT INTO orders (user_id, food_item, quantity, shipping_address, city) VALUES (?, ?, ?, ?, ?)",
                        (user_id, food_item, quantity, shipping_address, city)
                    )
                    conn.commit()
                
        else:
            # Handle the case where the user is not found by email
            print("User not found with email:", email)

class ThanksDialog(QDialog):
    def __init__(self, widget, total_amount, shipping_address):
        super(ThanksDialog, self).__init__()
        self.setGeometry(0, 0, 480, 620)
        loadUi("thanks.ui", self)
        self.widget = widget
        self.total_amount = total_amount
        self.shipping_address = shipping_address

        # Connect the "Go Back" button to the go_back_to_main function
        self.go_back_button.clicked.connect(self.go_back_to_main)
        print("ThanksDialog initialized.")
        
    def go_back_to_main(self):
        # Go back to the main page
        self.widget.setCurrentIndex(0)

            
            
class Login(QDialog):
    def __init__(self, widget, main_window):
        super(Login, self).__init__()
        self.setGeometry(0, 0, 480, 620)  # Set the geometry of the login dialog
        loadUi("login.ui", self)
        self.loginbutton.clicked.connect(self.login_and_goto_menu)  # Connect both methods
        self.password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.show_password_checkbox.stateChanged.connect(self.toggle_password_visibility)
        self.signupbutton.clicked.connect(self.gotosignup)
        self.widget = widget
        self.main_window = main_window  # Store a reference to the main window

        # Create a QLabel for displaying messages
        self.message_label = QtWidgets.QLabel(self)
        self.message_label.setGeometry(200, 380, 460, 30)
        self.message_label.setAlignment(QtCore.Qt.AlignCenter)

        self.message_label.setStyleSheet("background: transparent; border: none; color: red")

        font = QFont()
        font.setPointSize(12)
        self.message_label.setFont(font)


    def login_and_goto_menu(self):
        self.loginfunction()

        if self.message_label.text().startswith("Login Successful"):
            self.goto_menu()

    def loginfunction(self):
        email = self.email.text()
        password = self.password.text()

        cursor.execute("SELECT email, password FROM users WHERE email=?", (email,))
        user = cursor.fetchone()
        if user:
            stored_password = user[1]
            if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                self.message_label.setText("Login Successful with email: " + email)
                self.main_window.show()
            else:
                self.message_label.setText("Invalid password")
        else:
            self.message_label.setText("User does not exist")
            
    def toggle_password_visibility(self):
        if self.show_password_checkbox.isChecked():
            self.password.setEchoMode(QtWidgets.QLineEdit.Normal)
        else:
            self.password.setEchoMode(QtWidgets.QLineEdit.Password)

    def goto_menu(self):
        menu_dialog = MenuDialog(self.widget, self.main_window)
        self.widget.addWidget(menu_dialog)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)
        self.hide()

    def gotosignup(self):
        signup = Signup(self.widget, self.main_window)
        self.widget.addWidget(signup)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)
        self.hide()

class Signup(QDialog):
    def __init__(self, widget, main_window):
        super(Signup, self).__init__()
        self.setGeometry(0, 0, 480, 20)  # Set the geometry of the signup dialog
        loadUi("signup.ui", self)
        self.signupbutton.clicked.connect(self.signupfunction)
        self.loginbuttons.clicked.connect(self.gotologin)
        self.widget = widget
        self.main_window = main_window  # Store a reference to the main window
        self.password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.confirmpass.setEchoMode(QtWidgets.QLineEdit.Password)

        self.show_password_checkbox.stateChanged.connect(self.toggle_password_visibility)
        self.show_confirmpass_checkbox.stateChanged.connect(self.toggle_confirmpass_visibility)

        # Create a QLabel for displaying messages
        self.message_label = QtWidgets.QLabel(self)
        self.message_label.setGeometry(200, 400, 460, 40)
        self.message_label.setAlignment(QtCore.Qt.AlignCenter)

        # Make the QLabel transparent and borderless
        self.message_label.setStyleSheet("background: transparent; border: none; color: red")

        # Set the background to transparent
        self.message_label.setAutoFillBackground(False)

        font = QFont()
        font.setPointSize(9)
        self.message_label.setFont(font)

    def is_gmail(self, email):
        # Regular expression to match Gmail addresses
        gmail_pattern = r'^[a-zA-Z0-9._%+-]+@gmail\.com$'
        return re.match(gmail_pattern, email)

    def signupfunction(self):
        email = self.email.text()
        password = self.password.text()
        confirmpass = self.confirmpass.text()

        # Check if the user already exists
        cursor.execute("SELECT email FROM users WHERE email=?", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            self.message_label.setText("User with this email already exists. Please log in.")
        else:
            if password == confirmpass:
                if self.is_gmail(email):
                    # Hash the password
                    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                    # Insert user data into the database with hashed password
                    cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)",
                                   (email, hashed_password.decode('utf-8')))
                    conn.commit()
                    self.message_label.setText("Successfully created an account with email: " + email)
                    # Show the main window
                    self.main_window.show()
                else:
                    self.message_label.setText("This is not a Gmail account. Please use a Gmail address to sign up.")
            else:
                self.message_label.setText("Password does not match")

    def gotologin(self):
        login = Login(self.widget, self.main_window)
        self.widget.addWidget(login)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)
        self.hide()

    def toggle_password_visibility(self):
        if self.show_password_checkbox.isChecked():
            self.password.setEchoMode(QtWidgets.QLineEdit.Normal)
        else:
            self.password.setEchoMode(QtWidgets.QLineEdit.Password)

    def toggle_confirmpass_visibility(self):
        if self.show_confirmpass_checkbox.isChecked():
            self.confirmpass.setEchoMode(QtWidgets.QLineEdit.Normal)
        else:
            self.confirmpass.setEchoMode(QtWidgets.QLineEdit.Password)

app = QApplication(sys.argv)
widget = QStackedWidget()
main_window = QMainWindow()
ui = Ui_MainWindow()
ui.setupUi(main_window)

def show_login():
    login = Login(widget, main_window)
    widget.addWidget(login)
    widget.setCurrentIndex(widget.currentIndex() + 1)

ui.order_now_button.clicked.connect(show_login)

widget.addWidget(main_window)
widget.setFixedWidth(851)
widget.setFixedHeight(624)
widget.show()
sys.exit(app.exec_())
