import os
import re
import requests
import json
import psutil
import threading
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from newspaper import Article
from rich.console import Console
from rich.markdown import Markdown
import openai

console = Console()

# Load environment variables
load_dotenv()

# FreshRSS API Settings
FRESHRSS_API = "http://localhost:8080/api/greader.php"
FRESHRSS_AUTH_TOKEN = os.getenv("FRESHRSS_AUTH_TOKEN")

# OpenAI API Settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = openai.Client(api_key=OPENAI_API_KEY)

# Ollama API URL
OLLAMA_API_URL = "http://127.0.0.1:11434/api/generate"

# RAM Monitoring
RAM_THRESHOLD = 80  # Terminate script if RAM usage exceeds this percentage
CHECK_INTERVAL = 1  # Check RAM usage every second
terminate_flag = False

# Global user choices
selected_language = "English"
selected_model = None
selected_analyzer = None

# System Prompts (Now Include User Language)
def get_article_prompt():
    return (
        "You are a financial journalist and market analyst. Your job is to analyze news articles, "
        "extract key insights, and summarize content. **You must always complete the analysis** "
        "without disclaimers, refusals, or references to external data.\n\n"
        "## **TASK INSTRUCTIONS (FOR EACH ARTICLE)**\n"
        "**1. Detailed Summary:** Extract key information accurately without omitting insights.\n"
        "   - **Summarize fully and accurately.**\n"
        "   - **DO NOT refuse to analyze the article.**\n"
        "   - **DO NOT include disclaimers about financial advice or copyright.**\n"
        "   - **DO NOT state that content is copyrighted—just summarize in your own words.**\n"
        "   - **If the article cannot be parsed or is inaccessible, skip it.**\n\n"
        "**2. Sentiment Analysis (Per Company/Investment):**\n"
        "   - Identify sentiment toward each mentioned company, stock ticker, or investment.\n"
        "   - If sentiment is mixed, explain why.\n"
        "   - **DO NOT hallucinate financial insights.**\n\n"
        "**3. Identifying Companies, Stocks, and Investments:**\n"
        "   - Extract **all mentioned stock tickers, companies, and investments.**\n"
        "   - **List them exactly as they appear in the article.**\n"
        "   - **DO NOT fabricate stock tickers or company names.**\n\n"
        "**4. Market Implications:**\n"
        "   - Explain how the information in the article **might impact markets or investors.**\n"
        "   - **DO NOT generate financial advice.**\n"
        "   - **DO NOT suggest trades, investments, or speculative market actions.**\n"
        "   - **Only analyze what is explicitly in the article.**\n\n"
        f"**Provide the response in the following language: {selected_language}**"
    )

def get_summary_prompt():
    return (
        "You are a financial journalist tasked with summarizing multiple news analyses. "
        "You must provide a **cohesive final summary** of the articles, highlighting "
        "key trends, sentiment per company, and any major market implications.\n\n"
        "**Instructions:**\n"
        "- Aggregate all mentioned stock tickers, companies, and investments.\n"
        "- Provide **individual sentiment ratings** for each company/investment.\n"
        "- Summarize the market trends **based only on the articles analyzed**.\n"
        "- **Do not introduce additional financial opinions or speculations.**\n"
        "- Format the response in Markdown for structured readability.\n\n"
        f"**Provide the response in the following language: {selected_language}**"
    )

def monitor_ram_usage():
    """Monitor RAM usage and terminate script if it exceeds threshold."""
    global terminate_flag
    while not terminate_flag:
        if psutil.virtual_memory().percent >= RAM_THRESHOLD:
            console.print(f"\n[bold red]Critical: RAM usage exceeded {RAM_THRESHOLD}%. Terminating script.[/bold red]\n")
            os._exit(1)  # Immediate termination of the script
        time.sleep(CHECK_INTERVAL)

ram_monitor_thread = threading.Thread(target=monitor_ram_usage, daemon=True)
ram_monitor_thread.start()

def choose_language():
    """Prompt the user to select a language."""
    global selected_language
    console.print("\n[bold yellow]Type your preferred language (e.g., English, Chinese (Simplified), Spanish):[/bold yellow]")
    selected_language = input("Enter language: ").strip()
    console.print(f"\n[bold green]Language set to: {selected_language}[/bold green]")

def choose_model():
    """Prompt the user to select OpenAI or Ollama, while displaying popular models."""
    global selected_model, selected_analyzer

    console.print("\n[bold yellow]Choose the LLM model source:[/bold yellow]")
    console.print("[1] OpenAI API (Requires API key and sufficient balance)")
    console.print("[2] Ollama (Runs locally, requires pre-installed models)")

    while True:
        choice = input("\nEnter choice (1 for OpenAI, 2 for Ollama): ").strip()
        
        if choice == "1":
            selected_analyzer = analyze_with_openai
            console.print("\n[bold green]Using OpenAI API...[/bold green]")
            console.print(
                "\nPopular OpenAI models:\n"
                "- o1\n"
                "- gpt-4o\n"
                "- gpt-4o-mini\n"
                "- o3-mini"
            )
            selected_model = input("\nEnter OpenAI model name: ").strip()
            return
        
        elif choice == "2":
            selected_analyzer = analyze_with_ollama
            console.print("\n[bold green]Using Ollama local models...[/bold green]")
            console.print(
                "\nPopular Ollama models:\n"
                "- deepseek-r1 (1.5B-671B)\n"
                "- llama3.3\n"
                "- phi4\n"
                "- llama3.2 (1B-3B)\n"
                "\n[italic]For models with multiple parameter sizes, specify as 'model:parameter' (e.g., llama3.2:1b). Not all models support non-English languages.[/italic]"
            )
            selected_model = input("\nEnter Ollama model name: ").strip()
            return
        
        else:
            console.print("[bold red]Invalid choice! Please enter 1 or 2.[/bold red]")

def get_articles_published_today():
    """
    Fetch articles from FreshRSS using the stored Auth token.

    Returns:
        list: A list of articles published today with their title, URL, and timestamp.
    """
    headers = {
        "Authorization": f"GoogleLogin auth={FRESHRSS_AUTH_TOKEN}",
        "Accept": "application/json"
    }

    response = requests.get(f"{FRESHRSS_API}/reader/api/0/stream/contents", headers=headers)

    if response.status_code == 401:
        raise Exception("Unauthorized: Check FreshRSS Auth token in .env.")

    if response.status_code != 200:
        raise Exception(f"Failed to fetch FreshRSS articles: {response.text}")

    articles = []
    today = datetime.now().date()

    for entry in response.json().get("items", []):
        article_date = datetime.fromtimestamp(entry["published"]).date()
        if article_date == today:
            articles.append({
                "title": entry["title"],
                "url": entry["alternate"][0]["href"],
                "timestamp": entry["published"]
            })

    return articles

def get_clean_article_content(article_url):
    """Extract clean article content using newspaper3k."""
    try:
        article = Article(article_url)
        article.download()
        article.parse()
        return article.text
    except Exception:
        return None

def analyze_with_openai(article):
    """Analyze article with OpenAI."""
    article_content = get_clean_article_content(article["url"])
    if not article_content:
        return f"**Skipping article:** *{article['title']}* (Could not extract content)."

    response = openai_client.chat.completions.create(
        model=selected_model,
        messages=[
            {"role": "system", "content": get_article_prompt()},
            {"role": "user", "content": f"**Title:** {article['title']}\n\n**Content:**\n{article_content}"}
        ],
        temperature=0.3
    )

    # Ensure proper Markdown formatting for financial amounts
    return re.sub(r"(\$\s?\d[\d,\.]*)", r"`\1`", response.choices[0].message.content)

def analyze_with_ollama(article):
    """Analyze article with Ollama."""
    article_content = get_clean_article_content(article["url"])
    if not article_content:
        return f"**Skipping article:** *{article['title']}* (Could not extract content)."

    # Use "prompt" instead of "messages"
    prompt = f"{get_article_prompt()}\n\n**Title:** {article['title']}\n\n**Content:**\n{article_content}"

    payload = {
        "model": selected_model,
        "prompt": prompt,  # Ensure prompt is sent directly
        "stream": False
    }

    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(OLLAMA_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        response_json = response.json()

        # Extract response from correct key
        return re.sub(r"(\$\s?\d[\d,\.]*)", r"`\1`", response_json.get("response", "**Error: No response from Ollama**"))

    except requests.RequestException as e:
        return f"**Error:** Failed to connect to Ollama API: {str(e)}"

def generate_consolidated_summary(articles_analysis):
    """Generate final summary using OpenAI or Ollama."""
    user_content = "\n\n".join(articles_analysis)  # Only user-provided input

    if selected_analyzer == analyze_with_openai:
        response = openai_client.chat.completions.create(
            model=selected_model,
            messages=[
                {"role": "system", "content": get_summary_prompt()},  # System prompt here
                {"role": "user", "content": user_content}  # Only user content
            ],
            temperature=0.3
        )
        return response.choices[0].message.content

    # Ollama: System + User Prompt Combined
    payload = {
        "model": selected_model,
        "prompt": f"{get_summary_prompt()}\n\n{user_content}",  # Full prompt for Ollama
        "stream": False
    }

    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(OLLAMA_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        response_json = response.json()
        return response_json.get("response", "**Error: No summary response from Ollama**")

    except requests.RequestException as e:
        return f"**Error:** Failed to connect to Ollama API: {str(e)}"


def display_analysis():
    """Fetch articles and analyze them."""
    articles = get_articles_published_today()
    if not articles:
        console.print("[bold red]No articles published today.[/bold red]")
        return

    if not selected_analyzer:
        console.print("[bold red]Error: No model selected for analysis![/bold red]")
        return

    articles_analysis = []
    for article in articles:
        console.print(Markdown(f"## {article['title']}"))
        analysis = selected_analyzer(article)
        console.print(Markdown(analysis))
        articles_analysis.append(analysis)

    summary = generate_consolidated_summary(articles_analysis)
    console.print(Markdown(summary))

if __name__ == "__main__":
    choose_language()
    choose_model()
    display_analysis()