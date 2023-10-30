from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import pyqtSlot
from generated_receipt import Ui_ReceiptDialog  # Import the generated UI class

class ReceiptDialog(QDialog):
    def __init__(self,widget, total_amount, shipping_address, city, state):
        super(ReceiptDialog, self).__init__()
        self.ui = Ui_ReceiptDialog()
        self.ui.setupUi(self)

        # Set the labels or widgets in the dialog based on the data
        self.ui.label_2.setText("Total Amount: ₦" + str(total_amount))
        self.ui.label_3.setText("Shipping Address: " + shipping_address)
        self.ui.label_5.setText("City: " + city)
        self.ui.label_6.setText("State: " + state)

        # Store the widget for later use
        self.widget = widget

        # Create and connect the "OK" button to navigate to ThanksDialog
        self.ui.ok_button.clicked.connect(self.navigate_to_thanks)

    @pyqtSlot()
    def navigate_to_thanks(self):
        # Hide the ReceiptDialog
        self.hide()

        # Use the stored widget to set the current index
        index_of_thanks_dialog = 0  # Adjust this index based on your actual stacked widget setup
        self.widget.setCurrentIndex(index_of_thanks_dialog)

