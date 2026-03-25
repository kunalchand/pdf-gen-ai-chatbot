# FILE: src/app/ui.py
import streamlit as st
from streamlit_chat import message
from typing import Optional

from src.service.pdf_service import PDFService
from src.service.embeddings_service import EmbeddingsService
from src.service.pinecone_service import PineconeService
from src.service.chat_service import ChatService
from src.config import settings
from src.util import constants


def _inject_styles() -> None:
    st.markdown(
        """
    <style>
        a { color: #60B4FF !important; }
        a:hover { color: #90CFFF !important; text-decoration: underline; }
    </style>
    """,
        unsafe_allow_html=True,
    )


def sidebar_ui(
    pdf_service: PDFService,
    embeddings_service: EmbeddingsService,
    pinecone_service: PineconeService,
) -> Optional[list]:
    """
    Renders the sidebar UI for PDF upload and processing.

    Args:
        pdf_service (PDFService): PDF processing service.
        embeddings_service (EmbeddingsService): Embedding service.
        pinecone_service (PineconeService): Pinecone vector service.

    Returns:
        Optional[list]: List of uploaded PDFs.
    """
    with st.sidebar:
        st.title("Storage Information")

        vector_count = pinecone_service.get_vector_count()
        pct = min(vector_count / settings.PINECONE_MAX_VECTORS, 1.0)

        bar_col, btn_col = st.columns([3, 1])
        with bar_col:
            st.progress(
                pct, text=f"{vector_count} / {settings.PINECONE_MAX_VECTORS} vectors"
            )
        with btn_col:
            if st.button("🗑️", help="Clear all vectors", disabled=(vector_count == 0)):
                with st.spinner("Clearing..."):
                    pinecone_service.delete_all_vectors()
                st.rerun()

        st.divider()

        if "uploader_key" not in st.session_state:
            st.session_state.uploader_key = 0

        pdf_docs = st.file_uploader(
            "Upload PDF Documents",
            type="pdf",
            accept_multiple_files=True,
            key=f"pdf_uploader_{st.session_state.uploader_key}",
        )
        if st.button("Send to Pinecone", use_container_width=True):
            with st.spinner("Processing..."):
                raw_text = pdf_service.get_pdf_text(pdf_docs)
                chunks = pdf_service.get_text_chunks(raw_text)
                embeddings = embeddings_service.embed_texts(chunks)
                pinecone_service.delete_all_vectors()
                pinecone_service.upsert_vectors(chunks, embeddings)
            st.session_state.uploader_key += 1
            st.success("Documents processed and uploaded!")
            st.rerun()


    return pdf_docs


def chat_ui(
    chat_service: ChatService,
    embeddings_service: EmbeddingsService,
    pinecone_service: PineconeService,
) -> None:
    """
    Renders the chat UI and manages chat interactions.

    Args:
        chat_service (ChatService): Handles conversation and LLM queries.
        embeddings_service (EmbeddingsService): Embedding service.
        pinecone_service (PineconeService): Pinecone vector service.
    """
    _inject_styles()

    st.markdown(
        f'<h1><a href="{constants.PDF_GEN_AI_CHATBOT_GITHUB_URL}" target="_blank" style="text-decoration: none; color: inherit;">PDF Gen AI Chatbot</a></h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
        <div style="display: flex; flex-wrap: wrap; gap: 6px; align-items: center;">
            <img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white" height="22"/>
            <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=flat-square&logo=streamlit&logoColor=white" height="22"/>
            <img src="https://img.shields.io/badge/LangChain-1C3C3C?style=flat-square&logo=langchain&logoColor=white" height="22"/>
            <img src="https://img.shields.io/badge/Groq-F55036?style=flat-square&logo=groq&logoColor=white" height="22"/>
            <img src="https://img.shields.io/badge/Pinecone-000000?style=flat-square&logo=pinecone&logoColor=white" height="22"/>
            <img src="https://img.shields.io/badge/HuggingFace-FFD21E?style=flat-square&logo=huggingface&logoColor=black" height="22"/>
        </div>
        <div style="white-space: nowrap;">
            Built by <a href="{constants.AUTHOR_LINKEDIN_URL}" target="_blank">Kunal Chand</a>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.divider()

    response_container = st.container()

    with st.container():
        with st.form("chat_form", clear_on_submit=True):
            col1, col2 = st.columns([9, 1])
            with col1:
                query = st.text_input(
                    "message",
                    label_visibility="collapsed",
                    placeholder="Ask something about your PDFs...",
                )
            with col2:
                send_clicked = st.form_submit_button("Send ➤", use_container_width=True)

        _, clear_col = st.columns([9, 1])
        with clear_col:
            if st.button("🗑️ Clear", use_container_width=True, help="Clear chat history"):
                if "chat_service" in st.session_state:
                    st.session_state.chat_service.requests = []
                    st.session_state.chat_service.responses = [constants.DEFAULT_BOT_MESSAGE]
                st.rerun()

    if send_clicked and query:
        with st.spinner("🤔 Thinking..."):
            conversation_str = chat_service.get_conversation_string()
            refined_query = chat_service.query_refiner(conversation_str, query)
            vector = embeddings_service.embed_query(refined_query)
            result = pinecone_service.query_vectors(vector)

            if len(result["matches"]) < 2:
                context = "Sorry, not enough info in uploaded PDFs."
            else:
                context = (
                    result["matches"][0]["metadata"]["text"]
                    + "\n"
                    + result["matches"][1]["metadata"]["text"]
                )

            response = chat_service.chain.invoke(
                {
                    "input": f"Context:\n{context}\n\nQuery:\n{query}",
                    "history": [],
                }
            ).content

        chat_service.add_interaction(query, response)

    with response_container:
        for i in range(len(chat_service.responses)):
            message(chat_service.responses[i], key=str(i))
            if i < len(chat_service.requests):
                message(chat_service.requests[i], is_user=True, key=f"{i}_user")
