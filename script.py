import os, requests, datetime

from openai import OpenAI, AssistantEventHandler

from db_handler import GenericDBHandler, Conversation

def timestamp_to_datetime(timestamp):
    return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')



# Code interpreter
# Input
# $0.03 / session

# File Search
# Input
# $0.10 / GB of vector-storage per day (1 GB free)

# Step 1: Create a new Assistant with File Search Enabled


class GPTWrapper:
    def __init__(self, api_key=None, db_url='sqlite:///conv.db'):
        super().__init__()
        self._client = None
        # Initialize OpenAI client
        self._is_available = True if api_key else False
        if api_key and self._is_available:
            self.set_api(api_key)
        self._db_handler = ''
        self.init_db(db_url)

    def is_available(self):
        return self._is_available

    def set_api(self, api_key):
        self._api_key = api_key
        self._client = OpenAI(api_key=api_key)
        os.environ['OPENAI_API_KEY'] = api_key

    def request_and_set_api(self, api_key):
        try:
            response = requests.get('https://api.openai.com/v1/models', headers={'Authorization': f'Bearer {api_key}'})
            self._is_available = response.status_code == 200
            if self._is_available:
                self.set_api(api_key)
            return self._is_available
        except Exception as e:
            print(e)
            return False

    def get_message_obj(self, role, content):
        return {"role": role, "content": content}

    def init_db(self, db_url):
        self._db_handler = GenericDBHandler(db_url)

    def get_conversations(self):
        return self._db_handler.get_conversations()

    def append(self, message):
        self._db_handler.append(message)


class GPTAssistantWrapper(GPTWrapper):
    def __init__(self, api_key=None, db_url='sqlite:///conv.db'):
        super().__init__(api_key=api_key, db_url=db_url)
        self.__assistant_id = None
        self.__thread_id = None
        self.__assistants = []

    def get_assistants(self, order='desc', limit=None):
        if self._client is None:
            return None
        assistants = self._client.beta.assistants.list(order=order, limit=limit)
        assistants = [{
            "assistant_id": assistant.id,
            "name": assistant.name,
            "instructions": assistant.instructions,
            "tools": assistant.tools,
            "model": assistant.model,
            "thread": '',
        } for assistant in assistants]
        self.__assistants = assistants
        return self.__assistants

    def set_current_assistant(self, assistant_id):
        self.__assistant_id = assistant_id
        self.__set_current_thread()

    def __set_current_thread(self):
        if self.__assistant_id is None:
            raise ValueError('Assistant is not initialized yet')
        else:
            # thread = self._db_handler.query_table(Thread, {"name": name, "assistant_id": self.__assistant_id})
            # if thread:
            #     print(f"Thread {name} already exists")
            #     self.__thread_id = thread[0].thread_id
            # else:
            thread = self._client.beta.threads.create()
            self.__thread_id = thread.id
            for assistant in self.__assistants:
                if assistant["assistant_id"] == self.__assistant_id:
                    assistant["thread"] = self.__thread_id
                    break
            # self._db_handler.append(Thread, thread_obj)

    def send_message(self, message_str, instructions=''):
        user_obj = self.get_message_obj("user", message_str)
        self._db_handler.append(Conversation, user_obj)

        self._client.beta.threads.messages.create(
            thread_id=self.__thread_id,
            role="user",
            content=message_str
        )

        run = self._client.beta.threads.runs.create(
            thread_id=self.__thread_id,
            assistant_id=self.__assistant_id,
            instructions=instructions,
        )

        response = self._client.beta.threads.runs.retrieve(
          thread_id=self.__thread_id,
          run_id=run.id
        )

        while response.status == "in_progress" or response.status == "queued":
            response = self._client.beta.threads.runs.retrieve(thread_id=self.__thread_id, run_id=run.id)

        response = self._client.beta.threads.messages.list(thread_id=self.__thread_id)
        response = response.dict()["data"][0]
        response = self.get_message_obj(response['role'], response['content'][0]['text']['value'])
        self._db_handler.append(Conversation, response)
        return response


class GPTAssistantV2Wrapper(GPTAssistantWrapper):
    """
    A wrapper class for managing the OpenAI Assistant V2 with enhanced File Search capabilities.
    """

    def __init__(self, api_key=None, db_url='sqlite:///conv.db'):
        """
        Initializes the GPTAssistantV2Wrapper.

        :param api_key: API key for authentication.
        :param db_url: Database URL for storing conversation data.
        """
        super().__init__(api_key=api_key, db_url=db_url)
        self.__assistant_id = None
        self.__thread_id = None
        self.__assistants = []

    def __form_assistant_obj(self, assistant):
        """
        Forms a dictionary object representing an assistant.

        :param assistant: Assistant object from the API.
        :return: Dictionary representing the assistant.
        """
        obj = {
            "assistant_id": assistant.id,
            "name": assistant.name,
            "instructions": assistant.instructions,
            "tools": assistant.tools,
            "model": assistant.model,
            "created_at": timestamp_to_datetime(assistant.created_at),
        }
        return obj

    def __form_vectorstore_obj(self, vector):
        """
        Forms a dictionary object representing a vector store.

        :param vector: Vector store object from the API.
        :return: Dictionary representing the vector store.
        """
        obj = {
            "vector_store_id": vector.id,
            "name": vector.name,
            "created_at": timestamp_to_datetime(vector.created_at),
            "file_counts": vector.file_counts,
            "last_activate_at": timestamp_to_datetime(vector.last_active_at),
        }
        return obj

    def __form_files_obj(self, file):
        """
        Forms a dictionary object representing a file.

        :param file: File object from the API.
        :return: Dictionary representing the file.
        """
        obj = {
            "file_id": file.id,
            "filename": file.filename,
            "bytes": file.bytes,
            "created_at": timestamp_to_datetime(file.created_at),
        }
        return obj

    def get_assistants(self, order='desc', limit=None):
        """
        Retrieves a list of assistants.

        :param order: Order of retrieval, either 'asc' or 'desc'.
        :param limit: Limit on the number of assistants to retrieve.
        :return: List of assistants.
        """
        if self._client is None:
            return None
        assistants = self._client.beta.assistants.list(order=order, limit=limit)
        assistants = [self.__form_assistant_obj(assistant) for assistant in assistants]
        self.__assistants = assistants
        return self.__assistants

    def create_assistant(self, args):
        """
        Creates a new assistant.

        :param args: Arguments for creating the assistant.
        :return: Dictionary representing the newly created assistant.
        """
        assistant = self._client.beta.assistants.create(
            **args
        )

        self.set_current_assistant(assistant.id)

        assistant = self.__form_assistant_obj(assistant)

        return assistant

    def set_current_assistant(self, assistant_id):
        """
        Sets the current assistant by ID.

        :param assistant_id: ID of the assistant to set as current.
        """
        self.__assistant_id = assistant_id
        self.__set_current_thread()

    def delete_assistant(self, assistant_id):
        """
        Deletes an assistant by ID.

        :param assistant_id: ID of the assistant to delete.
        """
        self._client.beta.assistants.delete(assistant_id=assistant_id)

    def __set_current_thread(self, messages=None):
        """
        Sets the current thread for the assistant.

        :param messages: Optional initial messages for the thread.
        :return: Thread object.
        """
        if messages:
            thread = self._client.beta.threads.create(messages=messages)
        else:
            thread = self._client.beta.threads.create()
        self.__thread_id = thread.id
        for assistant in self.__assistants:
            if assistant["assistant_id"] == self.__assistant_id:
                assistant["thread"] = self.__thread_id
                break
        return thread

    def send_message(self, message_str, instructions='', message_file=None, assistant_id=None, thread_id=None):
        """
        Sends a message to the assistant and handles streaming responses.

        :param message_str: The message content.
        :param instructions: Additional instructions for the assistant.
        :param message_file: Optional file to attach to the message.
        :param assistant_id: ID of the assistant to use.
        :param thread_id: ID of the thread to use.
        :yield: Streamed text responses.
        """
        user_obj = self.get_message_obj("user", message_str)
        self._db_handler.append(Conversation, user_obj)
        args = {
            'thread_id': thread_id if thread_id else self.__thread_id,
            'role': "user",
            'content': message_str
        }

        if message_file:
            args['attachments'] = [
                {"file_id": message_file.id, "tools": [{"type": "file_search"}]}
            ]

        self._client.beta.threads.messages.create(**args)

        response = ''

        with self._client.beta.threads.runs.stream(
                thread_id=thread_id if thread_id else self.__thread_id,
                assistant_id=assistant_id if assistant_id else self.__assistant_id,
                instructions=instructions,
                event_handler=self.EventHandler(self._client),
        ) as stream:
            for text in stream.text_deltas:
                response += text
                yield text

        ai_obj = self.get_message_obj("assistant", response)
        self._db_handler.append(Conversation, ai_obj)

    def create_vector_store(self, args):
        """
        Creates a new vector store.

        :param args: Arguments for creating the vector store.
        :return: Dictionary representing the newly created vector store.
        """
        vector_store = self._client.beta.vector_stores.create(**args)
        vector_store = self.__form_vectorstore_obj(vector_store)
        return vector_store

    def upload_files_to_vector_store(self, vector_store_id, file_paths):
        """
        Uploads local files to the vector store.

        :param vector_store_id: ID of the vector store.
        :param file_paths: List of file paths to upload.
        :return: Dictionary representing the uploaded files.
        """
        file_streams = [open(path, "rb") for path in file_paths]
        file_batch = self._client.beta.vector_stores.file_batches.upload_and_poll(
                vector_store_id=vector_store_id, files=file_streams
        )

        result_obj = self.__form_files_obj(file_batch)

        return result_obj

    def delete_vector_store(self, vector_store_id):
        """
        Deletes a vector store by ID.

        :param vector_store_id: ID of the vector store to delete.
        """
        self._client.beta.vector_stores.delete(vector_store_id=vector_store_id)

    def delete_files_from_vector_store(self, vector_store_id, file_id):
        """
        Deletes a file from the vector store.

        :param vector_store_id: ID of the vector store.
        :param file_id: ID of the file to delete.
        """
        self._client.beta.vector_stores.files.delete(vector_store_id=vector_store_id, file_id=file_id)

    def update_assistant(self, tool_resources, assistant_id=None):
        """
        Updates an assistant's tool resources.

        :param tool_resources: Tool resources to update.
        :param assistant_id: Optional assistant ID.
        :return: Updated assistant object.
        """
        assistant = self._client.beta.assistants.update(
            assistant_id=assistant_id if assistant_id else self.__assistant_id,
            tool_resources=tool_resources
        )
        return assistant

    def delete_file(self, file_id):
        """
        Deletes a file from OpenAI files storage. It deletes the file in every vector store.

        :param file_id: ID of the file to delete.
        """
        self._client.files.delete(file_id=file_id)

    def get_vector_stores(self, assistant_id=None):
        """
        Retrieves vector stores in the assistant.

        :param assistant_id: Optional assistant ID.
        :return: List of vector stores.
        """
        vs_obj_lst = []

        assistant_id = assistant_id if assistant_id else self.__assistant_id

        tool_resources = self._client.beta.assistants.retrieve(assistant_id=assistant_id).dict()['tool_resources']
        if tool_resources:
            file_search = tool_resources['file_search']
            if file_search:
                vs_ids = file_search['vector_store_ids']
                for vs_id in vs_ids:
                    vs_instance = self._client.beta.vector_stores.retrieve(vector_store_id=vs_id)
                    vs_obj_lst.append(self.__form_vectorstore_obj(vs_instance))

        return vs_obj_lst

    def get_vector_store_files(self, vector_store_id):
        """
        Retrieves files in a vector store.

        :param vector_store_id: ID of the vector store.
        :return: List of files in the vector store.
        """
        files_lst = []

        vector_store_files = self._client.beta.vector_stores.files.list(vector_store_id=vector_store_id)
        for file in vector_store_files:
            file = self._client.files.retrieve(file_id=file.id)
            files_lst.append(self.__form_files_obj(file))

        return files_lst

    def clear_messages(self):
        """
        Clears all messages from the conversation database.
        """
        self._db_handler.delete(Conversation, None)

    # Declaration as an inner class
    class EventHandler(AssistantEventHandler):
        """
        Event handler class for handling assistant events.
        """

        def __init__(self, client):
            """
            Initializes the EventHandler.

            :param client: The client instance.
            """
            super().__init__()
            self._client = client

        def on_text_created(self, text) -> None:
            """
            Handles the event when text is created.

            :param text: The created text.
            """
            print(f"\nassistant onTextCreated > ", end="", flush=True)

        def on_text_delta(self, delta, snapshot):
            """
            Handles the event when there is a text delta.

            :param delta: The text delta.
            :param snapshot: The snapshot of the current state.
            """
            print(delta.value, end="", flush=True)

        def on_tool_call_created(self, tool_call):
            """
            Handles the event when a tool call is created.

            :param tool_call: The created tool call.
            """
            print(f"\nassistant onToolCallCreated > {tool_call.type}\n", flush=True)

        def on_tool_call_delta(self, delta, snapshot):
            """
            Handles the event when there is a tool call delta.

            :param delta: The tool call delta.
            :param snapshot: The snapshot of the current state.
            """
            if delta.type == 'code_interpreter':
                pass
            elif delta.type == 'file_search':
                print(f"\nassistant > {delta.type}\n", flush=True)

        def on_message_done(self, message) -> None:
            """
            Handles the event when a message is done.

            :param message: The completed message.
            """
            print('Message done')
            message_content = message.content[0].text
            annotations = message_content.annotations
            citations = []
            for index, annotation in enumerate(annotations):
                message_content.value = message_content.value.replace(
                    annotation.text, f"[{index}]"
                )
                if file_citation := getattr(annotation, "file_citation", None):
                    cited_file = self._client.files.retrieve(file_citation.file_id)
                    citations.append(f"[{index}] {cited_file.filename}")

            print(message_content.value)
            print("\n".join(citations))


# API_KEY = 'sk-...'

# wrapper = GPTAssistantV2Wrapper(api_key=API_KEY)
# #
# assistant = wrapper.create_assistant({"name": "Financial Analyst Assistant", "instructions": "You are an expert financial analyst. Use you knowledge base to answer questions about audited financial statements.", "model": "gpt-4o", "tools": [{"type": "file_search"}]})
# vector_store = wrapper.create_vector_store({"name": "Financial Statements"})
# file_batch = wrapper.upload_files_to_vector_store(vector_store.id, ["edgar/goog-10k.pdf", "edgar/brka-10k.txt"])
# #
# # # You can print the status and the file counts of the batch to see the result of this operation.
# print(file_batch.status)
# print(file_batch.file_counts)
# #
# # # Update the assistant to use the vector store
# wrapper.update_assistant({"file_search": {"vector_store_ids": [vector_store.id]}})
# #
# message_file = wrapper.upload_files_to_vector_store(vector_store.id, ["tiny_example/yjg30737.txt", 'tiny_example/pyqt-openai.txt'])
# #
# print(wrapper.get_vector_stores()[0]['file_counts'].total)
# # message= wrapper.send_message(message_str="How many shares of AAPL were outstanding at the end of of August 2023?",
# # instructions='Please address the user as Jane Doe. The user has a premium account.')
# # print(message)
#
# message = wrapper.send_message(message_str="Who is yjg30737?",
# instructions='You have to be lively as possible.')
#
# print(message)
