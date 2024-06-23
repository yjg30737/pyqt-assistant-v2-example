from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QFrame, QPushButton, QHBoxLayout, QWidget, \
    QLineEdit, QTextEdit, QFormLayout


class VectorStoreInputDialog(QDialog):
    def __init__(self, title, attributes_list, parent=None):
        super().__init__(parent)
        self.__initVal(attributes_list)
        self.__initUi(title)

    def __initVal(self, attributes_list):
        self.__input_attr = attributes_list
        self.__output_attr = {}

    def __initUi(self, title):
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint)

        self.__nameWidget = QLineEdit()
        self.__nameWidget.textChanged.connect(self.okEnabled)

        lay = QFormLayout()
        lay.addRow('Name:', self.__nameWidget)

        mainWidget = QWidget()
        mainWidget.setLayout(lay)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)

        self.__okBtn = QPushButton('OK')
        self.__okBtn.clicked.connect(self.__setAccept)

        cancelBtn = QPushButton('Cancel')
        cancelBtn.clicked.connect(self.close)

        lay = QHBoxLayout()
        lay.addWidget(self.__okBtn)
        lay.addWidget(cancelBtn)
        lay.setAlignment(Qt.AlignmentFlag.AlignRight)
        lay.setContentsMargins(0, 0, 0, 0)

        okCancelWidget = QWidget()
        okCancelWidget.setLayout(lay)

        lay = QVBoxLayout()
        lay.addWidget(mainWidget)
        lay.addWidget(sep)
        lay.addWidget(okCancelWidget)

        self.setLayout(lay)

        self.__okBtn.setEnabled(False)

    def getAttribute(self):
        return self.__output_attr

    def __setAccept(self):
        self.__name = self.__nameWidget.text()
        self.__output_attr = {
            'name': self.__name,
        }
        self.accept()

    def okEnabled(self):
        self.__okBtn.setEnabled(bool(self.__nameWidget.text()))
