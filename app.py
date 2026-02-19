# app.py
import streamlit as st
import os
import requests
import json
import PyPDF2
from docx import Document
from typing import List, Dict
import hashlib
import time

# 页面配置
st.set_page_config(
    page_title="DeepSeek RAG智能助手",
    page_icon="🤖",
    layout="wide"
)

# 自定义CSS
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .main-container {
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    .header {
        text-align: center;
        color: white;
        padding: 2rem;
        margin-bottom: 1rem;
    }
    .header h1 {
        font-size: 3rem;
        margin-bottom: 0.5rem;
    }
    .api-status {
        background-color: #f0f2f6;
        padding: 0.5rem 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #28a745;
    }
    .warning-box {
        background-color: #fff3cd;
        color: #856404;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #ffc107;
    }
</style>
""", unsafe_allow_html=True)

# 标题
st.markdown("""
<div class="header">
    <h1>🤖 DeepSeek RAG智能助手</h1>
    <p>上传文档，AI智能问答 - 基于DeepSeek大模型</p>
</div>
""", unsafe_allow_html=True)

# 主容器
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# 初始化session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'documents' not in st.session_state:
    st.session_state.documents = {}
if 'api_key_valid' not in st.session_state:
    st.session_state.api_key_valid = False

# 侧边栏 - API设置
with st.sidebar:
    st.markdown("### 🔑 DeepSeek API设置")

    # API密钥输入
    api_key = st.text_input(
        "输入你的DeepSeek API密钥",
        type="password",
        help="在 https://platform.deepseek.com/ 获取",
        placeholder="sk-..."
    )

    if api_key:
        # 验证API密钥
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            test_data = {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 5
            }
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                json=test_data,
                timeout=5
            )
            if response.status_code == 200:
                st.session_state.api_key_valid = True
                st.session_state.api_key = api_key
                st.markdown("""
                <div class="success-box">
                    ✅ API密钥验证成功
                </div>
                """, unsafe_allow_html=True)
            else:
                st.session_state.api_key_valid = False
                st.markdown("""
                <div class="warning-box">
                    ❌ API密钥无效
                </div>
                """, unsafe_allow_html=True)
        except:
            st.session_state.api_key_valid = False
            st.markdown("""
            <div class="warning-box">
                ❌ 无法连接到DeepSeek API
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📁 文档管理")

    # 文件上传
    uploaded_files = st.file_uploader(
        "选择文件（可多选）",
        type=['txt', 'pdf', 'docx', 'md', 'py', 'js', 'html', 'css', 'cpp', 'java', 'json', 'csv'],
        accept_multiple_files=True,
        help="支持多种格式：文本、PDF、Word、代码文件等"
    )

    if uploaded_files:
        for file in uploaded_files:
            if file.name not in st.session_state.documents:
                try:
                    with st.spinner(f"正在处理 {file.name}..."):
                        # 读取文件内容
                        if file.name.endswith('.pdf'):
                            pdf_reader = PyPDF2.PdfReader(file)
                            content = ""
                            for page in pdf_reader.pages:
                                content += page.extract_text() + "\n"
                        elif file.name.endswith('.docx'):
                            doc = Document(file)
                            content = "\n".join([p.text for p in doc.paragraphs])
                        else:
                            content = file.getvalue().decode('utf-8', errors='ignore')

                        # 分块处理（按段落）
                        chunks = [c.strip() for c in content.split('\n\n') if len(c.strip()) > 50]

                        st.session_state.documents[file.name] = {
                            'content': content,
                            'chunks': chunks,
                            'type': file.name.split('.')[-1],
                            'size': len(content)
                        }
                        st.success(f"✅ 已加载: {file.name} ({len(chunks)}个段落)")
                except Exception as e:
                    st.error(f"❌ 读取失败 {file.name}: {str(e)}")

    # 已加载文档列表
    if st.session_state.documents:
        st.markdown("### 📋 已加载文档")
        for name in list(st.session_state.documents.keys()):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.caption(f"📄 {name[:30]}...")
            with col2:
                if st.button("❌", key=f"del_{name}"):
                    del st.session_state.documents[name]
                    st.rerun()

    # 清空所有
    if st.session_state.documents and st.button("🗑️ 清空所有文档", use_container_width=True):
        st.session_state.documents = {}
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.markdown("### ℹ️ 使用说明")
    st.info("""
    1. 输入DeepSeek API密钥
    2. 上传文档（支持多选）
    3. 在下方提问
    4. AI会基于文档内容回答
    """)

# 主界面
col1, col2 = st.columns([2, 1])

with col2:
    if st.session_state.documents:
        st.markdown("### 📊 文档统计")
        total_docs = len(st.session_state.documents)
        total_chunks = sum(len(info['chunks']) for info in st.session_state.documents.values())

        st.metric("文档数量", total_docs)
        st.metric("文本段落", total_chunks)

        # 文档列表
        with st.expander("📑 文档详情"):
            for name, info in st.session_state.documents.items():
                st.text(f"• {name} ({len(info['chunks'])}段)")

with col1:
    st.markdown("### 💬 智能问答")

    # 显示聊天历史
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 输入问题
    if prompt := st.chat_input("请输入您的问题..."):
        # 检查API密钥
        if not st.session_state.get('api_key_valid', False):
            st.warning("⚠️ 请在左侧输入有效的DeepSeek API密钥")
        else:
            # 添加用户消息
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # 生成回答
            with st.chat_message("assistant"):
                with st.spinner("🤔 DeepSeek正在思考..."):
                    try:
                        # 1. 检索相关文档内容
                        relevant_chunks = []
                        if st.session_state.documents:
                            prompt_words = set(prompt.lower().split())
                            for name, info in st.session_state.documents.items():
                                for chunk in info['chunks']:
                                    chunk_words = set(chunk.lower().split())
                                    overlap = len(prompt_words & chunk_words)
                                    if overlap > 0:
                                        relevant_chunks.append({
                                            'file': name,
                                            'content': chunk,
                                            'relevance': overlap
                                        })

                            # 按相关性排序
                            relevant_chunks.sort(key=lambda x: x['relevance'], reverse=True)
                            context = "\n\n".join([f"[来自 {c['file']}]:\n{c['content']}"
                                                   for c in relevant_chunks[:5]])
                        else:
                            context = "没有上传任何文档"

                        # 2. 构建提示词
                        system_prompt = """你是一个专业的文档问答助手。请基于提供的文档内容回答问题。
如果文档中没有相关信息，请明确告知用户"根据当前文档，我无法回答这个问题"。
回答要准确、简洁、有条理。"""

                        user_prompt = f"""文档内容：
{context}

问题：{prompt}

请基于以上文档内容回答问题："""

                        # 3. 调用DeepSeek API
                        headers = {
                            "Authorization": f"Bearer {st.session_state.api_key}",
                            "Content-Type": "application/json"
                        }

                        data = {
                            "model": "deepseek-chat",
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt}
                            ],
                            "temperature": 0.3,
                            "max_tokens": 2000,
                            "stream": False
                        }

                        response = requests.post(
                            "https://api.deepseek.com/v1/chat/completions",
                            headers=headers,
                            json=data
                        )

                        if response.status_code == 200:
                            result = response.json()
                            answer = result['choices'][0]['message']['content']

                            # 添加引用来源
                            if relevant_chunks:
                                answer += "\n\n---\n📖 **参考来源**\n"
                                for i, chunk in enumerate(relevant_chunks[:2], 1):
                                    preview = chunk['content'][:100] + "..."
                                    answer += f"{i}. {chunk['file']}: {preview}\n"

                            st.markdown(answer)
                            st.session_state.messages.append({"role": "assistant", "content": answer})
                        else:
                            error_msg = f"API调用失败: {response.status_code}"
                            st.error(error_msg)
                            st.session_state.messages.append({"role": "assistant", "content": error_msg})

                    except Exception as e:
                        error_msg = f"发生错误: {str(e)}"
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})

st.markdown('</div>', unsafe_allow_html=True)

# 底部
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: white; padding: 1rem;'>
    基于 DeepSeek API + Streamlit 构建 | 需要有效的API密钥
</div>
""", unsafe_allow_html=True)