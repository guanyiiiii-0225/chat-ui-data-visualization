
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="View Conversation",
    page_icon="💬",
    layout="wide",
)

load_dotenv(override=True)
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
DATABASE_NAME = os.getenv("DATABASE_NAME")
uri = "mongodb+srv://"+USERNAME+":"+PASSWORD+"@chatui.63yozgy.mongodb.net/?retryWrites=true&w=majority&appName=ChatUI"

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
    # Set index before merge
    conversation_df["index"] = conversation_df.index

    # Merge feedback and conversation data
    merge_df = pd.merge(conversation_df, feedback_df, left_on=["conversation_id", "message_id"], right_on=["conversation_id", "message_id"], how=merge_type, suffixes=('_x', '')).sort_values(by="index")
    merge_df = merge_df[remaining_columns]

    return merge_df

# -----------------------------get data------------------------------ #
client = connect_to_mongodb(uri)
database = client.get_database(DATABASE_NAME)

remaining_columns = ['conversation_id', 'title', 'message_id', 'from', 'message_content', 'score', 'model', 'created_at', 'feedback_id', 'feedback', 'custom_comment']
merge_df = get_merge_df(merge_type='left', remaining_columns=remaining_columns)

# ----------------------------page layout---------------------------- #
st.title("💬 View a Conversation")

selected_conversation_id = st.selectbox("Select conversation id", merge_df['conversation_id'].unique())
selected_conversation_df = merge_df[merge_df['conversation_id'] == selected_conversation_id]

# Display the title of the conversation
st.subheader(selected_conversation_df.iloc[0]['title'])

# Display the conversation
for i in range(len(selected_conversation_df)):
    if selected_conversation_df.iloc[i]['from'] != 'user' and selected_conversation_df.iloc[i]['from'] != 'assistant':
        continue
    with st.chat_message(selected_conversation_df.iloc[i]['from']):
        st.write(selected_conversation_df.iloc[i]['message_content'])
        st.write(f"`Created At: {selected_conversation_df.iloc[i]['created_at'].strftime('%Y-%m-%d %H:%M:%S')} / Message ID: {selected_conversation_df.iloc[i]['message_id']}`")

        # Display feedback if exists
        if not pd.isna(selected_conversation_df.iloc[i]['score']):
            score = int(selected_conversation_df.iloc[i]['score'])

            feedback_string = ""
            feedback_color = "grey-background"
            if len(selected_conversation_df.iloc[i]['feedback']) > 0:
                for feedback in selected_conversation_df.iloc[i]['feedback']:
                    feedback_string += f" :{feedback_color}[{feedback}]"
            if len(selected_conversation_df.iloc[i]['custom_comment']) > 0:
                feedback_string += f" :{feedback_color}[{selected_conversation_df.iloc[i]['custom_comment']}]"
            
            if score > 0:
                st.write(f""":blue-background[👏 This message gain positive feedback:]{feedback_string}""")
            elif score < 0:
                st.write(f""":red-background[😿 This message gain negative feedback:]{feedback_string}""")

# ----------------------------sidebar button---------------------------- #
# Add a button to sidebar and clear the cache when clicked(refresh the database)
with st.sidebar:
    if st.button("Refresh Database", help="Refresh the database to get the latest data"):
        st.cache_data.clear()
        st.cache_resource.clear()

        merge_df = get_merge_df(merge_type='left', remaining_columns=remaining_columns)
        st.toast('Refresh database success!', icon="🎉")