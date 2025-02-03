# 📢 FreshRSS Financial News Analyzer

## 📌 Overview
The **FreshRSS Financial News Analyzer** is a powerful Python script designed to:
- 📑 **Fetch news articles** from FreshRSS
- 📰 **Analyze articles** using OpenAI or Ollama LLMs
- 📊 **Perform sentiment analysis** on stock tickers, companies, and investments
- 🏦 **Summarize financial market trends**
- 🔄 **Automatically shut down** if RAM usage exceeds **80%** to prevent system crashes
- 🎯 **Support multiple languages** for analysis and summaries

## 🚀 Features
✅ **Multi-model Support** – Choose between **OpenAI Models** and **Ollama LLMs**  
✅ **Real-time Financial Sentiment Analysis** – Identifies bullish/bearish sentiment  
✅ **Market Trend Summaries** – Consolidates insights from multiple articles  
✅ **RAM Protection** – Monitors RAM usage and terminates if it exceeds 80%  
✅ **Markdown Output** – For clean and structured formatting  

---

## 🔧 Setup Guide

### 📥 1. Install Dependencies
Make sure you have **Python 3.9+** installed, then run:
```sh
pip install -r requirements.txt
```

---

### 🌐 2. Setting Up FreshRSS
1. **Install FreshRSS** on your server: [FreshRSS Installation Guide](https://freshrss.github.io/FreshRSS/en/admins/03_Installation.html)
2. **Enable API Access** in FreshRSS:
   - Log into FreshRSS
   - Go to **Profile > External access via API**
   - Ensure **API access** is enabled
3. **Get Your FreshRSS Auth Token**:
   - Use the following `curl` command, replacing `{username}` and `{password}`:
     ```sh
     curl 'http://localhost:8080/api/greader.php/accounts/ClientLogin?Email={username}&Passwd={password}'
     ```
   - The response will include an authentication token.
4. **Add the token to `.env` file**:
   ```ini
   FRESHRSS_AUTH_TOKEN=your_freshrss_auth_token_here
   ```
5. **Set up your RSS Feeds**

---

### 🔑 3. Get Your OpenAI API Key (Optional)
To use **GPT-4o** or any other OpenAI models, you need an OpenAI API key:
1. Sign up at [OpenAI](https://platform.openai.com/signup/)
2. Go to **API Keys** section
3. Click **Create new secret key**
4. **Enable billing** in OpenAI to access API functionality
5. Copy and **add it to `.env` file**:
   ```ini
   OPENAI_API_KEY=your_openai_api_key_here
   ```

---

### ⚙️ 4. Setting Up Ollama (Optional)
To use **Ollama LLMs**, install Ollama on your local machine:
1. Download and install Ollama from [Ollama.ai](https://ollama.ai/)
2. Run the Ollama server:
   ```sh
   ollama serve
   ```
3. Download a supported model:
   ```sh
   ollama run {model name}
   ```
4. **Verify context length (`num_ctx`) support**:
   - Not all models support `num_ctx=8192`. Check model details using:
     ```sh
     ollama show {model name}
     ```
5. When running the script, select **Ollama** as the model source.

---

## ▶️ Running the Script
To start the script, run:
```sh
python freshrss_ai_summarizer.py
```
Follow the on-screen prompts to choose your **language** and **LLM model**.

---

## ⚠️ Limitations
⚠️ **Manual FreshRSS Refresh** – FreshRSS **does not auto-refresh** feeds. You must manually update it before running the script.  
⚠️ **Ollama Context Limitations** – Some smaller models might struggle with large prompts; `num_ctx=8192` is set, but may need adjustment.  
⚠️ **RAM Intensive** – The script terminates **if RAM exceeds 80%** to prevent crashes.  
⚠️ **GPU Usage with Ollama** – Performance depends on **VRAM availability**; large models may require more memory.  

---

## 🤝 Contributing
Feel free to fork and improve the script! Pull requests are welcome. 🚀

---

## 📜 License
This project is licensed under the **Apache-2.0 license**.
