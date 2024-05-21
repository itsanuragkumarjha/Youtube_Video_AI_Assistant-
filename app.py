import gradio as gr
import os

from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.document_loaders import YoutubeLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.chains import LLMChain
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

def create_db_from_video_url(video_url, api_key):
    """
    Creates an Embedding of the Video and performs 
    """
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=api_key)

    loader = YoutubeLoader.from_youtube_url(video_url)
    transcripts = loader.load()
    # cannot provide this directly to the model so we are splitting the transcripts into small chunks

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    docs = text_splitter.split_documents(transcripts)

    db = FAISS.from_documents(docs, embedding=embeddings)
    return db

def get_response(video, request):
    """
    Usind Gemini Pro to get the response. It can handle upto 32k tokens.
    """
    API_KEY = os.environ.get("API_Key")
    db = create_db_from_video_url(video, API_KEY)
    docs = db.similarity_search(query=request, k=5)
    docs_content = " ".join([doc.page_content for doc in docs])

    chat = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=API_KEY, convert_system_message_to_human=True)

    # creating a template for request
    template = """
    You are an assistant that can answer questions about youtube videos based on
    video transcripts: {docs}
    Only use factual information from the transcript to answer the question.
    If you don't have enough information to answer the question, say "I don't know".
    Your Answers should be detailed.
    """

    system_msg_prompt = SystemMessagePromptTemplate.from_template(template)

    # human prompt
    human_template = "Answer the following questions: {question}"
    human_msg_prompt = HumanMessagePromptTemplate.from_template(human_template)

    chat_prompt = ChatPromptTemplate.from_messages(
        [system_msg_prompt, human_msg_prompt]
    )

    chain = LLMChain(llm=chat, prompt=chat_prompt)

    response = chain.run(question=request, docs=docs_content)

    return response

# creating title, description for the web app
title = "YouTube🔴 Video🤳  AI Assistant 🤖"
description = "Answers to the Questions asked by the user on the specified YouTube video."


# building the app
youtube_video_assistant = gr.Interface(
    fn=get_response,
    inputs=[gr.Text(label="Enter the Youtube Video URL:", placeholder="Example: https://www.youtube.com/watch?v=MnDudvCyWpc"),
            gr.Text(label="Enter your Question", placeholder="Example: What's the video is about?")],
    outputs=gr.TextArea(label="Answers using....some secret llm 🤫😉:"),
    title=title,
    description=description
)

# launching the web app
youtube_video_assistant.launch(share=True)
