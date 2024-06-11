
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os
import pandas as pd
import streamlit as st
import time

st.set_page_config(
    page_title="Browse Feedbacks",
    page_icon="📈",
    layout="wide",
)

load_dotenv(override=True)
URI = os.getenv("URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")

@st.cache_resource
def connect_to_mongodb(uri):
    # Create a new client and connect to the server
    client = MongoClient(uri)

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
    for item in items:
        item['_id'] = str(item['_id'])
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
                'conversation_id': item['_id'],
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

def get_merge_df(merge_type, remaining_columns):
    # Get the database
    database = client.get_database(DATABASE_NAME)

    # Fetch data and turn into dataframe
    feedback_data = fetch_data(database, "feedback")
    feedback_df = pd.DataFrame(feedback_data)
    feedback_df.rename(columns={"_id": "feedback_id", "createdBy": "created_by", "conversationId": "conversation_id", "messageId": "message_id", "customComment": "custom_comment"}, inplace=True)
    feedback_df['conversation_id'] = feedback_df['conversation_id'].astype(str)

    conversation_data = fetch_data(database, "conversations")
    conversation_df = create_conversation_dataframe(conversation_data)

    # Merge feedback and conversation data
    merge_df = pd.merge(conversation_df, feedback_df, left_on=["conversation_id", "message_id"], right_on=["conversation_id", "message_id"], how=merge_type, suffixes=('_x', ''))
    merge_df = merge_df[remaining_columns]

    return merge_df

def get_feedback_analytics(_merge_df):
    # go through all the feedbacks and count the number of each feedback
    feedback_count = _merge_df["feedback"].explode().value_counts()
    feedback_count = feedback_count.reset_index()

    return feedback_count

# -----------------------------get data------------------------------ #
client = connect_to_mongodb(URI)
with st.spinner('Loading data...'):
    remaining_columns = ["feedback_id", "score", "feedback", "custom_comment", "message_content", "conversation_id", "message_id", "created_by", "created_at"]
    merge_df = get_merge_df(merge_type='right', remaining_columns=remaining_columns)
with st.spinner('Analyzing feedback...'):
    feedback_count = get_feedback_analytics(merge_df)

# ----------------------------page layout---------------------------- #
st.title("📈 Browse all Feedbacks")

st.markdown('######')
st.bar_chart(feedback_count, x='feedback', y='count')
st.dataframe(merge_df)

# ----------------------------sidebar button---------------------------- #
# Add a button to sidebar and clear the cache when clicked(refresh the database)
with st.sidebar:
    if st.button("Refresh Database", help="Refresh the database to get the latest data"):
        st.cache_data.clear()
        st.cache_resource.clear()

        with st.spinner('Loading data...'):
            remaining_columns = ["feedback_id", "score", "feedback", "custom_comment", "message_content", "conversation_id", "message_id", "created_by", "created_at"]
            merge_df = get_merge_df(merge_type='right', remaining_columns=remaining_columns)
        with st.spinner('Analyzing feedback...'):
            feedback_count = get_feedback_analytics(merge_df)

        st.toast('Refresh database success!', icon="🎉")
