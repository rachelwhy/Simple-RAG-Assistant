# 🤖 DeepSeek RAG智能助手

基于DeepSeek大模型的文档智能问答系统，支持多种文档格式，实现RAG（检索增强生成）功能。

## ✨ 功能特点

- ✅ 支持多种文档格式（PDF、Word、TXT、代码文件等）
- ✅ 基于DeepSeek大模型，智能理解文档内容
- ✅ RAG检索增强，答案更准确
- ✅ 实时流式输出
- ✅ 显示答案来源

## 🚀 在线体验

访问：[https://deepseek-rag-assistant.streamlit.app](https://deepseek-rag-assistant.streamlit.app)

## 📖 使用方法

1. 输入你的DeepSeek API密钥
2. 上传文档（支持多选）
3. 在输入框提问
4. AI基于文档内容回答

## 🛠️ 支持的格式

- 文本文件 (.txt)
- PDF文件 (.pdf)
- Word文档 (.docx)
- 代码文件 (.py, .js, .html, .css, .cpp, .java)
- 数据文件 (.json, .csv)
- 标记文件 (.md)

## 🔑 获取API密钥

1. 访问 [DeepSeek Platform](https://platform.deepseek.com/)
2. 注册/登录账号
3. 在API Keys页面创建新的API密钥
4. 复制密钥（格式：sk-xxxxxxxxxx）

## 💻 本地运行

```bash
# 克隆仓库
git clone https://github.com/你的用户名/deepseek-rag-assistant.git

# 安装依赖
pip install -r requirements.txt

# 运行
streamlit run app.py