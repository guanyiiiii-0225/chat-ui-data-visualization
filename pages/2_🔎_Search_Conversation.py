
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Search Conversation",
    page_icon="🔎",
    layout="wide",
)

load_dotenv(override=True)
URI = os.getenv("URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")

@st.cache_resource
def connect_to_mongodb(uri):
    # Create a new client and connect to the server
    client = MongoClient(uri, server_api=ServerApi('1'))

    # Send a ping to confirm a successful connection
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)
    return client

# Fetch data from the database according to the collection name
@st.cache_data
def fetch_data(_database, collection_name):
    collection = _database[collection_name]
    items = list(collection.find())
    return items

def flatten_message(message):
    return {
        'message_id': message['id'],
        'from': message['from'],
        'message_content': message['content'],
        'created_at': message['createdAt'],
        'updated_at': message['updatedAt'],
        'ancestors': message['ancestors'],
        'children': message['children'],
        'interrupted': message.get('interrupted', False),
        'score': message.get('score', None),
        'updates': message.get('updates', [])
    }

@st.cache_data
def create_conversation_dataframe(_conversation_data):
    flat_data = []
    for item in _conversation_data:
        for message in item['messages']:
            flat_message = flatten_message(message)
            flat_message.update({
                'conversation_id': str(item['_id']),
                'title': item['title'],
                'root_message_id': item.get('rootMessageId', None),
                'model': item.get('model', None),
                'preprompt': item.get('preprompt', None),
                'assistant_id': item.get('assistantId', None),
                'created_at_session': item.get('createdAt', None),
                'updated_at_session': item.get('updatedAt', None),
                'user_agent': item.get('userAgent', None),
                'embedding_model': item.get('embeddingModel', None),
                'sessionId': item.get('sessionId', None)
            })
            flat_data.append(flat_message)

    conversation_df = pd.DataFrame(flat_data)
    conversation_df['created_at'] = pd.to_datetime(conversation_df['created_at'])
    conversation_df['updated_at'] = pd.to_datetime(conversation_df['updated_at'])
    conversation_df['created_at_session'] = pd.to_datetime(conversation_df['created_at_session'])
    conversation_df['updated_at_session'] = pd.to_datetime(conversation_df['updated_at_session'])
    return conversation_df

# -----------------------------get data------------------------------ #
client = connect_to_mongodb(URI)
database = client.get_database(DATABASE_NAME)

conversation_data = fetch_data(database, "conversations")
conversation_df = create_conversation_dataframe(conversation_data)

default_columns = ['conversation_id', 'message_id', 'from', 'message_content', 'score', 'model', 'created_at']
sorted_columns = sorted(conversation_df.columns)

# ----------------------------page layout---------------------------- #
st.title("🔎 Search a Conversation")

selected_columns = st.multiselect("Select columns", sorted_columns, default=default_columns, key="conversation_columns", help="Select the columns you want to display", placeholder="Select the columns you want to display")
selected_conversation_id = st.selectbox("Select conversation id", conversation_df['conversation_id'].unique())
selected_conversation_df = conversation_df[conversation_df['conversation_id'] == selected_conversation_id]

st.write(selected_conversation_df[selected_columns])

# ----------------------------sidebar button---------------------------- #
# Add a button to sidebar and clear the cache when clicked(refresh the database)
with st.sidebar:
    if st.button("Refresh Database", help="Refresh the database to get the latest data"):
        st.cache_data.clear()
        st.cache_resource.clear()

        conversation_data = fetch_data(database, "conversations")
        conversation_df = create_conversation_dataframe(conversation_data)
        sorted_columns = sorted(conversation_df.columns)

        st.toast('Refresh database success!', icon="🎉")