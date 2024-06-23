# pyqt-assistant-v2-example
OpenAI Assistant V2 Manager created with PyQt (focused on File Search functionality)

This is the first app that using PyQt6 as a main widget toolkit :) After all i need to adapt into the trend. 

## Detail Description
In V1, the Assistant mainly consisted of a single assistant with multiple threads, and each thread had its own run.

In V2, there was a significant update in the File Search functionality among the various tools of the Assistant. An Assistant with the File Search tool is utilized as a chatbot that interprets the contents of files provided by the user and explains them.

An assistant with the file search feature can have one or more Vector Stores, and each Vector Store can contain one or more files.

Moreover, Assistant V2 now offers streaming! I have applied streaming to this application, so you can see how the streaming works.

Note: By default, it provides edgar/brka-10k.txt, edgar/goog-10k.pdf, and edgar/aapl-10k.pdf in the OpenAI documentation.

Using SQLite as a database, for saving conversation history.

## How to Use CUI
If you find it cumbersome to use the desktop software with GUI, there is also a way to use CUI.

Simply copy script.py and uncomment the examples provided in the comments to test in various ways 🙂

## Requirements
* PyQt6
* openai
* requests
* sqlalchemy

## How to Run
1. pip clone ~
2. pip install -r requirements.txt
3. python main.py

## Preview

https://github.com/yjg30737/pyqt-assistant-v2-example/assets/55078043/f24dfa1c-d074-4624-b3cd-baaad9ea5744
