from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QScrollArea, QVBoxLayout, QWidget, QLabel, QHBoxLayout, QTextEdit


class ChatBrowser(QScrollArea):
    def __init__(self):
        super().__init__()
        self.__initUi()

    def __initUi(self):
        lay = QVBoxLayout()
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        widget = QWidget()
        widget.setLayout(lay)
        self.setWidget(widget)
        self.setWidgetResizable(True)

    def setMessages(self, messages):
        for message in messages:
            self.addMessage(message)

    def __setAndGetLabel(self, text):
        chatLbl = QLabel(text)
        chatLbl.setWordWrap(True)
        chatLbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        return chatLbl

    def addChunk(self, chunk):
        """
        For streaming messages (by AI)
        :param chunk:
        :return:
        """
        # For temporary measure to add messages in chunks
        # Currently i don't want to make this application anymore complex
        if self.widget().layout().count() % 2 == 1:
            chatLbl = self.__setAndGetLabel(chunk)
            chatLbl.setStyleSheet('QLabel { background-color: #AAA; padding: 1em }')
            self.widget().layout().addWidget(chatLbl)
        else:
            # The unit is AI
            chatLbl = self.__getLastUnit()
            if chatLbl:
                chatLbl.setText(chatLbl.text() + chunk)

    def __getLastUnit(self) -> QLabel | None:
        item = self.widget().layout().itemAt(self.widget().layout().count() - 1)
        if item:
            return item.widget()
        else:
            return None

    def addMessage(self, message):
        """
        For none-streaming messages (by user)
        :param message:
        :return:
        """
        content = message['content']
        role = message['role']
        chatLbl = self.__setAndGetLabel(content)
        if role == 'user':
            chatLbl.setStyleSheet('QLabel { padding: 1em }')
        else:
            chatLbl.setStyleSheet('QLabel { background-color: #AAA; padding: 1em }')
        self.widget().layout().addWidget(chatLbl)

    def event(self, e):
        if e.type() == 43:
            self.verticalScrollBar().setSliderPosition(self.verticalScrollBar().maximum())
        return super().event(e)

    def getAllText(self):
        all_text_lst = []
        lay = self.widget().layout()
        if lay:
            for i in range(lay.count()):
                if lay.itemAt(i) and lay.itemAt(i).widget():
                    widget = lay.itemAt(i).widget()
                    if isinstance(widget, QLabel):
                        all_text_lst.append(widget.text())

        return '\n'.join(all_text_lst)

    def clearMessages(self):
        lay = self.widget().layout()
        if lay:
            for i in range(lay.count()-1, -1, -1):
                lay.removeWidget(lay.itemAt(i).widget())


class TextEditPrompt(QTextEdit):
    returnPressed = pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__initUi()

    def __initUi(self):
        self.setStyleSheet('QTextEdit { border: 1px solid #AAA; } ')
        self.setAcceptRichText(False)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Return or e.key() == Qt.Key.Key_Enter:
            if e.modifiers() == Qt.KeyboardModifier.ShiftModifier:
                return super().keyPressEvent(e)
            else:
                self.returnPressed.emit(self.toPlainText())
        else:
            return super().keyPressEvent(e)


class PromptWidget(QWidget):
    sendPrompt = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.__initUi()

    def __initUi(self):
        self.__textEdit = TextEditPrompt()
        self.__textEdit.textChanged.connect(self.updateHeight)
        self.__textEdit.returnPressed.connect(self.__sendPrompt)
        lay = QHBoxLayout()
        lay.addWidget(self.__textEdit)
        lay.setContentsMargins(0, 0, 0, 0)
        self.setLayout(lay)
        self.updateHeight()

    def __sendPrompt(self, text):
        self.sendPrompt.emit(text)
        self.__textEdit.clear()

    def updateHeight(self):
        document = self.__textEdit.document()
        height = document.size().height()
        self.setMaximumHeight(int(height + document.documentMargin()))

    def getTextEdit(self):
        return self.__textEdit

