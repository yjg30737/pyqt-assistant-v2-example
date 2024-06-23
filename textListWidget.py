from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QVBoxLayout, QWidget, QTableWidget, \
    QLabel, QSizePolicy, QSpacerItem, QHBoxLayout, QPushButton


# from inputDialog import InputDialog


class AddDelTableWidget(QWidget):
    def __init__(self, lbl):
        super().__init__()
        self.__initUi(lbl)

    def __initUi(self, lbl):
        self.__tableWidget = QTableWidget()

        self.__addRowBtn = QPushButton('Add')
        self.__delRowBtn = QPushButton('Delete')

        self.__addRowBtn.clicked.connect(self.__add)
        self.__delRowBtn.clicked.connect(self.__delete)

        lay = QHBoxLayout()
        lay.addWidget(QLabel(lbl))
        lay.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.Policy.MinimumExpanding))
        lay.addWidget(self.__addRowBtn)
        lay.addWidget(self.__delRowBtn)
        lay.setAlignment(Qt.AlignmentFlag.AlignRight)
        lay.setContentsMargins(0, 0, 0, 0)

        menuWidget = QWidget()
        menuWidget.setLayout(lay)

        lay = QVBoxLayout()
        lay.addWidget(menuWidget)
        lay.addWidget(self.__tableWidget)
        lay.setContentsMargins(0, 0, 0, 0)

        self.setLayout(lay)

    def getTableWidget(self):
        return self.__tableWidget

    def __add(self):
        pass
        # dialog = InputDialog('Add', [('Name', '', True)], self)
        # reply = dialog.exec()
        # if reply == QDialog.Accepted:
        #     text = dialog.getText()
        #     self.__tableWidget.addItem(text)

    def __delete(self):
        try:
            self.__tableWidget.takeItem(self.__tableWidget.row(self.__tableWidget.currentItem()))
        except Exception as e:
            print(e)