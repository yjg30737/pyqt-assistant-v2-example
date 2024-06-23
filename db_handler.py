import datetime

from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, ARRAY
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

Base = declarative_base()


class GenericDBHandler:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def append(self, table, record):
        session = self.Session()
        table_instance = table(**record)
        session.add(table_instance)
        session.commit()
        return table_instance.id

    def update(self, table, record_id, update_fields):
        session = self.Session()
        record = session.query(table).get(record_id)
        for field, value in update_fields.items():
            setattr(record, field, value)
        session.commit()

    def delete(self, table, record_id):
        # If record_id is None, clear all records
        if record_id is None:
            session = self.Session()
            session.query(table).delete()
            session.commit()
            return
        else:
            session = self.Session()
            record = session.query(table).get(record_id)
            session.delete(record)
            session.commit()

    def query_table(self, table, conditions=None):
        session = self.Session()
        query = session.query(table)
        if conditions:
            query = query.filter_by(**conditions)
        results = query.all()
        return results

    def get_conversations(self):
        conversations = self.query_table(Conversation)
        return [{'role': conversation.role, 'content': conversation.content}
        for conversation in conversations]

    def get_assistant(self):
        assistant = self.query_table(Assistant)
        return [{'name': assistant.name, 'instructions': assistant.instructions, 'tools': assistant.tools, 'model': assistant.model}
        for assistant in assistant]


# Conversation table
class Conversation(Base):
    __tablename__ = 'conversation'

    id = Column(Integer, primary_key=True)
    role = Column(String(500))
    content = Column(String(5000))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)


class Assistant(Base):
    __tablename__ = 'assistant'

    id = Column(Integer, primary_key=True)
    assistant_id = Column(String(500))
    name = Column(String(500))
    instructions = Column(String(5000))
    tools = Column(String(500))
    model = Column(String(500))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    threads = relationship("Thread", back_populates="assistant")


class Thread(Base):
    __tablename__ = 'thread'

    id = Column(Integer, primary_key=True)
    thread_id = Column(String(500))
    name = Column(String(500))
    assistant_id = Column(Integer, ForeignKey('assistant.id'))

    assistant = relationship("Assistant", back_populates="threads")

# # ConversationHandler 인스턴스 생성 및 데이터베이스 연결
# # sqlite
# conversation_handler = GenericDBHandler('sqlite:///conv.db')
# #
# # # mysql
# # # conversation_handler = GenericDBHandler('mysql://{id}:{pwd}@{ip}/{db_name}')
# #
# # conversation_handler.add_record(Conversation, {'role': 'user', 'content': "What's the weather like?"})
# # conversation_handler.add_record(Conversation, {'role': 'assistant', 'content': "It's sunny."})
# postgre
# conversation_handler = GenericDBHandler('postgresql://postgres:{pwd}!@{ip}:5432/postgres')
