import os

from PyQt6.QtCore import QSettings, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import QMainWindow, QApplication, QVBoxLayout, QSplitter, QWidget, QLabel, QSizePolicy, \
    QPushButton, QDialog, QMessageBox, QHBoxLayout, QSpacerItem, QFileDialog

from apiWidget import ApiWidget
from chatBrowser import ChatBrowser, PromptWidget
from script import GPTAssistantV2Wrapper
from tableWidget import TableWidget
from assistantInputDialog import AssistantInputDialog
from vectorstoreInputDialog import VectorStoreInputDialog

QApplication.setFont(QFont('Arial', 12))


class Thread(QThread):
    afterGenerated = pyqtSignal(str)

    def __init__(self, wrapper, text):
        super(Thread, self).__init__()
        self.__wrapper = wrapper
        self.__text = text

    def run(self):
        try:
            for chunk in self.__wrapper.send_message(self.__text):
                self.afterGenerated.emit(chunk)
        except Exception as e:
            raise Exception(e)


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.__initVal()
        self.__initUi()

    def __initVal(self):
        self.__settings_ini = QSettings(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'settings.ini'), QSettings.Format.IniFormat)
        if not self.__settings_ini.contains('API_KEY'):
            self.__settings_ini.setValue('API_KEY', '')
        self.__api_key = self.__settings_ini.value('API_KEY', type=str)

        self.__wrapper = GPTAssistantV2Wrapper(self.__api_key)
        self.__assistant_list = self.__wrapper.get_assistants()

    def __initUi(self):
        self.setWindowTitle('PyQt GPT Assistant V2 Example')

        columns = ['vector_store_id', 'name', 'created_at', 'file_counts', 'last_activate_at']
        self.__vectorStoreTableWidget = TableWidget(columns=columns)
        self.__vectorStoreTableWidget.selectedRecord.connect(self.__vectorStoreSelected)
        self.__vectorStoreTableWidget.setSortingEnabled(True)
        self.__vectorStoreTableWidget.sortByColumn(2, Qt.SortOrder.DescendingOrder)

        columns = ['file_id', 'filename', 'created_at', 'bytes']
        self.__fileTableWidget = TableWidget(columns=columns)
        self.__fileTableWidget.setSortingEnabled(True)
        self.__fileTableWidget.sortByColumn(2, Qt.SortOrder.DescendingOrder)

        # Top
        # API input
        self.__apiWidget = ApiWidget(self.__api_key, wrapper=self.__wrapper, settings=self.__settings_ini)
        self.__apiWidget.apiKeyAccepted.connect(self.__api_key_accepted)

        columns = ['assistant_id', 'name', 'tools', 'model', 'instructions', 'created_at']
        self.__assistantTableWidget = TableWidget(columns=columns)
        self.__assistantTableWidget.setSortingEnabled(True)
        self.__assistantTableWidget.sortByColumn(5, Qt.SortOrder.DescendingOrder)
        if self.__assistant_list:
            for obj in self.__assistant_list:
                self.__assistantTableWidget.addRecord(obj)
        self.__assistantTableWidget.selectedRecord.connect(self.__assistantSelected)

        self.__assistantTableWidgetAddBtn = QPushButton('Add')
        self.__assistantTableWidgetDelBtn = QPushButton('Delete')

        self.__assistantTableWidgetAddBtn.clicked.connect(self.__addAssistant)
        self.__assistantTableWidgetDelBtn.clicked.connect(self.__deleteAssistant)

        lay = QHBoxLayout()
        lay.addWidget(QLabel('Assistants'))
        lay.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.Policy.MinimumExpanding))
        lay.addWidget(self.__assistantTableWidgetAddBtn)
        lay.addWidget(self.__assistantTableWidgetDelBtn)

        assistantMenuWidget = QWidget()
        assistantMenuWidget.setLayout(lay)

        self.__currentAssistantLbl = QLabel(f'Current Assistant:')

        self.__vectorStoreTableWidgetAddBtn = QPushButton('Add')
        self.__vectorStoreTableWidgetDelBtn = QPushButton('Delete')

        self.__vectorStoreTableWidgetAddBtn.clicked.connect(self.__addVectorStores)
        self.__vectorStoreTableWidgetDelBtn.clicked.connect(self.__deleteVectorStores)

        lay = QHBoxLayout()
        lay.addWidget(QLabel('Vector Stores'))
        lay.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.Policy.MinimumExpanding))
        lay.addWidget(self.__vectorStoreTableWidgetAddBtn)
        lay.addWidget(self.__vectorStoreTableWidgetDelBtn)

        vectorStoreMenuWidget = QWidget()
        vectorStoreMenuWidget.setLayout(lay)

        lay = QVBoxLayout()
        lay.addWidget(vectorStoreMenuWidget)
        lay.addWidget(self.__vectorStoreTableWidget)

        vectorStoreWidget = QWidget()
        vectorStoreWidget.setLayout(lay)

        self.__fileTableWidgetAddBtn = QPushButton('Add')
        self.__fileTableWidgetDelBtn = QPushButton('Delete')

        self.__fileTableWidgetAddBtn.clicked.connect(self.__addFile)
        self.__fileTableWidgetDelBtn.clicked.connect(self.__deleteFile)

        lay = QHBoxLayout()
        lay.addWidget(QLabel('Files'))
        lay.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.Policy.MinimumExpanding))
        lay.addWidget(self.__fileTableWidgetAddBtn)
        lay.addWidget(self.__fileTableWidgetDelBtn)

        fileMenuWidget = QWidget()
        fileMenuWidget.setLayout(lay)

        lay = QVBoxLayout()
        lay.addWidget(fileMenuWidget)
        lay.addWidget(self.__fileTableWidget)

        fileWidget = QWidget()
        fileWidget.setLayout(lay)

        vectorStoreFileSplitter = QSplitter()
        vectorStoreFileSplitter.addWidget(vectorStoreWidget)
        vectorStoreFileSplitter.addWidget(fileWidget)
        vectorStoreFileSplitter.setHandleWidth(1)
        vectorStoreFileSplitter.setChildrenCollapsible(False)
        vectorStoreFileSplitter.setSizes([500, 500])
        vectorStoreFileSplitter.setStyleSheet(
            "QSplitterHandle {background-color: lightgray;}")

        # Bottom left
        # Assistants List
        # "Upload files" button
        ## Files list of Assistants
        lay = QVBoxLayout()
        lay.addWidget(assistantMenuWidget)
        lay.addWidget(self.__assistantTableWidget)
        lay.addWidget(self.__currentAssistantLbl)

        assistantWidget = QWidget()
        assistantWidget.setLayout(lay)

        leftSplitter = QSplitter()
        leftSplitter.addWidget(assistantWidget)
        leftSplitter.addWidget(vectorStoreFileSplitter)
        leftSplitter.setHandleWidth(1)
        leftSplitter.setChildrenCollapsible(False)
        leftSplitter.setSizes([500, 500])
        leftSplitter.setOrientation(Qt.Orientation.Vertical)
        leftSplitter.setStyleSheet(
            "QSplitterHandle {background-color: lightgray;}")
        leftSplitter.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)

        clearConvBtn = QPushButton('Clear Conversation')
        clearConvBtn.clicked.connect(self.__clearConversation)

        self.__chatBrowser = ChatBrowser()
        self.__promptWidget = PromptWidget()
        self.__promptWidget.sendPrompt.connect(self.__run)

        messages = self.__wrapper.get_conversations()
        self.__chatBrowser.setMessages(messages)

        lay = QVBoxLayout()
        lay.addWidget(clearConvBtn)
        lay.addWidget(self.__chatBrowser)
        lay.addWidget(self.__promptWidget)

        rightWidget = QWidget()
        rightWidget.setLayout(lay)

        splitter = QSplitter()
        splitter.addWidget(leftSplitter)
        splitter.addWidget(rightWidget)
        splitter.setHandleWidth(1)
        splitter.setChildrenCollapsible(False)
        splitter.setSizes([500, 500])
        splitter.setStyleSheet(
            "QSplitterHandle {background-color: lightgray;}")
        splitter.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Bottom right
        # Chatbot
        lay = QVBoxLayout()
        lay.addWidget(self.__apiWidget)
        lay.addWidget(splitter)

        mainWidget = QWidget()
        mainWidget.setLayout(lay)

        self.setCentralWidget(mainWidget)

        self.__setAiEnabled(self.__wrapper.is_available())

        self.__assistantTableWidget.selectRow(0)

    def __assistantSelected(self, obj):
        self.__currentAssistantLbl.setText(f'Current Assistant: {obj["name"]} ({obj["assistant_id"]})')
        self.__wrapper.set_current_assistant(obj['assistant_id'])
        vector_stores = self.__wrapper.get_vector_stores(obj['assistant_id'])

        # vector_store_and_files = self.__wrapper.get_vector_store_and_files(obj['assistant_id'])
        # if len(vector_store_and_files) == 0:
        #     return
        # files = vector_store_and_files[0]['files']
        # self.__fileListWidget.clear()
        # for file in files:
        #     filename = file.filename
        #     file_created = file.created_at
        #     file_bytes = file.bytes
        #     file_id = file.id
        #     self.__fileListWidget.addItem(file_id)
        self.__vectorStoreTableWidget.clearRecord()
        for vector_store in vector_stores:
            self.__vectorStoreTableWidget.addRecord(vector_store)
        self.__fileTableWidget.clearRecord()
        self.__toggleVectorStoreBtn()
        self.__toggleFileBtn()
        self.__vectorStoreTableWidget.selectRow(0)

    def __vectorStoreSelected(self, obj):
        files = self.__wrapper.get_vector_store_files(obj['vector_store_id'])
        self.__fileTableWidget.clearRecord()
        for file in files:
            self.__fileTableWidget.addRecord(file)
        self.__setAiEnabled(self.__wrapper.is_available())

    def __api_key_accepted(self, api_key, f):
        # Enable AI related features if API key is valid
        self.__setAiEnabled(f)
        self.__assistant_list = self.__wrapper.get_assistants()
        if self.__assistant_list:
            for obj in self.__assistant_list:
                self.__assistantTableWidget.addRecord(obj)

    def __setAiEnabled(self, f):
        # If Files and Vector Stores are not enabled, disable the AI features
        f = f and self.__fileTableWidget.rowCount() > 0
        self.__promptWidget.setEnabled(f)

    def __addAssistant(self):
        dialog = AssistantInputDialog('Add', self)
        reply = dialog.exec()
        if reply == QDialog.DialogCode.Accepted:
            obj = dialog.getAttribute()
            obj = self.__wrapper.create_assistant(obj)
            self.__assistantTableWidget.addRecord(obj)
            self.__toggleVectorStoreBtn()

    def __deleteAssistant(self):
        # Show "Are you sure?" dialog
        dialog = QMessageBox.information(self, 'Delete', 'Are you sure you want to delete?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if dialog == QMessageBox.StandardButton.Yes:
            r_idx = self.__assistantTableWidget.currentRow()
            self.__wrapper.delete_assistant(self.__assistantTableWidget.getRecord(r_idx)['assistant_id'])
            self.__assistantTableWidget.deleteRecord(r_idx)
            self.__toggleVectorStoreBtn()
        else:
            return

    def __addVectorStores(self):
        dialog = VectorStoreInputDialog('Add', self)
        reply = dialog.exec()
        if reply == QDialog.DialogCode.Accepted:
            obj = dialog.getAttribute()
            obj = self.__wrapper.create_vector_store(obj)
            self.__vectorStoreTableWidget.addRecord(obj)
            self.__toggleFileBtn()

    def __deleteVectorStores(self):
        # Show "Are you sure?" dialog
        dialog = QMessageBox.information(self, 'Delete', 'Are you sure you want to delete?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if dialog == QMessageBox.StandardButton.Yes:
            r_idx = self.__vectorStoreTableWidget.currentRow()
            self.__wrapper.delete_vector_store(self.__vectorStoreTableWidget.getRecord(r_idx)['vector_store_id'])
            self.__vectorStoreTableWidget.deleteRecord(r_idx)
            self.__toggleFileBtn()
        else:
            return

    def __addFile(self):
        files, _ = QFileDialog.getOpenFileNames(None, "Select Files", "", "Text Files (*.txt);;PDF Files (*.pdf);;")
        if files:
            current_vector_store_id = self.__vectorStoreTableWidget.getRecord(self.__vectorStoreTableWidget.currentRow())['vector_store_id']
            obj = self.__wrapper.upload_files_to_vector_store(current_vector_store_id, files)
            self.__vectorStoreTableWidget.addRecord(obj)

    def __deleteFile(self):
        # Show "Are you sure?" dialog
        dialog = QMessageBox.information(self, 'Delete', 'Are you sure you want to delete?',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if dialog == QMessageBox.StandardButton.Yes:
            vector_store_id = self.__vectorStoreTableWidget.getRecord(self.__vectorStoreTableWidget.currentRow())['vector_store_id']
            r_idx = self.__fileTableWidget.currentRow()
            file_id = self.__fileTableWidget.getRecord(self.__fileTableWidget.currentRow())['file_id']
            self.__wrapper.delete_files_from_vector_store(vector_store_id, file_id)
            self.__fileTableWidget.deleteRecord(r_idx)
        else:
            return

    def __toggleVectorStoreBtn(self):
        f = self.__assistantTableWidget.rowCount() > 0
        self.__vectorStoreTableWidgetAddBtn.setEnabled(f)
        self.__vectorStoreTableWidgetDelBtn.setEnabled(f)

    def __toggleFileBtn(self):
        f = self.__vectorStoreTableWidget.rowCount() > 0
        self.__fileTableWidgetAddBtn.setEnabled(f)
        self.__fileTableWidgetDelBtn.setEnabled(f)

    def __run(self, text):
        # Add user message
        self.__chatBrowser.addMessage(self.__wrapper.get_message_obj('user', text))

        self.__t = Thread(self.__wrapper, text)
        self.__t.started.connect(self.__started)
        self.__t.afterGenerated.connect(self.__afterGenerated)
        self.__t.finished.connect(self.__finished)
        self.__t.start()

    def __started(self):
        print('started')

    def __afterGenerated(self, chunk):
        # Add assistant message by chunk
        self.__chatBrowser.addChunk(chunk)

    def __finished(self):
        # Put the feature such as DB thingy here
        pass

    def __clearConversation(self):
        self.__chatBrowser.clearMessages()
        self.__wrapper.clear_messages()



if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    QApplication.setWindowIcon(QIcon('logo.png'))
    w = MainWindow()
    w.show()
    sys.exit(app.exec())