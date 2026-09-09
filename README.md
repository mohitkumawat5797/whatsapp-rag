# 📄 whatsapp-rag

Send a PDF to a WhatsApp number. Ask it questions. Get answers back — from the PDF, not from thin air.

That's it. That's the bot.

## ✨ What it does

1. You WhatsApp a PDF to the bot 📎
2. The bot reads it, chops it into bite-sized chunks, and stashes them in a vector database
3. You ask a question 🤔
4. The bot digs up the relevant chunks and asks a (very fast, very free) LLM to answer using only that content
5. You get a reply, right there in the chat 🎉

No app to install. No dashboard. Just WhatsApp.

## Built with

- **Flask** — the webhook that catches your messages
- **Twilio** — the WhatsApp plumbing
- **Groq** (`llama-3.1-8b-instant`) — the brain, and it's fast
- **Pinecone** — the memory (vector search)
- **pdfplumber / PyPDF2** — the PDF whisperer

## 🚀 Get it running

```bash
git clone https://github.com/mohitkumawat5797/whatsapp-rag.git
cd whatsapp-rag
uv sync            # or: pip install -r requirements.txt
```

Drop your keys in a `.env` file:

```env
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
GROQ_API_KEY=...
PINECONE_API_KEY=...
PINECONE_INDEX_NAME=...
```

Fire it up:

```bash
python bot.py
```

Then poke a hole to the internet (ngrok is your friend) and point your Twilio WhatsApp sandbox webhook at:

```
https://your-tunnel-url/webhook
```

Send it a PDF. Ask it something. Watch it work. 🪄

## Heads up

The embedding step is currently a deterministic placeholder (hashes text into a pseudo-random vector) rather than a real semantic embedding model — it works, but swap it out for something like a proper embedding model if you want smarter retrieval. Also, anything not synced to Pinecone lives in memory and vanishes on restart.

