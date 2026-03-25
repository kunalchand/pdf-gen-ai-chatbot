# FILE: src/app/markup.py

GLOBAL_CSS = """
<style>
    a { color: #60B4FF !important; }
    a:hover { color: #90CFFF !important; text-decoration: underline; }
</style>
"""


def header_html(github_url: str) -> str:
    return (
        f'<h1>'
        f'<a href="{github_url}" target="_blank" style="text-decoration: none; color: inherit;">'
        f'PDF Gen AI Chatbot'
        f'</a>'
        f'</h1>'
    )


def badges_html(linkedin_url: str) -> str:
    return f"""
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
        Built by <a href="{linkedin_url}" target="_blank">Kunal Chand</a>
    </div>
</div>
"""
