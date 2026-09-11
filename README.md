# 📄 whatsapp-rag

Send a PDF to a WhatsApp number. Ask it questions. Get answers back — from the PDF, not from thin air.

---

## Demo & Architecture

<p align="center">
  <img src="https://github.com/user-attachments/assets/83b0be05-92f7-4f92-865e-a38cd7f4c06f" width="45%" alt="Architecture Overview" />
</p>
#----------------------------------------------------------------------------------------------------------------------------------------
&nbsp;

<p align="center">
  <img src="https://github.com/user-attachments/assets/d0f7a28f-18d0-4a8b-8e77-67e5bec9baa9" width="45%" alt="WhatsApp Chat Demo 1" />
</p>

#----------------------------------------------------------------------------------------------------------------------------------------
&nbsp;

<p align="center">
  <img src="https://github.com/user-attachments/assets/b7eb6378-1377-4318-b584-28ba1a6cec80" width="45%" alt="WhatsApp Chat Demo 2" />
</p>

---

## What it does

1. WhatsApp a PDF to the bot
2. Bot chunks it and stores embeddings in a vector database
3. You ask a question
4. Bot retrieves relevant chunks, sends them to an LLM
5. You get an answer back in chat

---

## Built with

- **Flask** — webhook
- **Twilio** — WhatsApp integration
- **Groq** (`llama-3.1-8b-instant`) — LLM
- **Pinecone** — vector search
- **pdfplumber / PyPDF2** — PDF parsing

---

## Setup

```bash
git clone https://github.com/mohitkumawat5797/whatsapp-rag.git
cd whatsapp-rag
uv sync            # or: pip install -r requirements.txt
```

`.env`:

```env
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
GROQ_API_KEY=...
PINECONE_API_KEY=...
PINECONE_INDEX_NAME=...
```

Run:

```bash
python bot.py
ngrok http 5000
```

Set Twilio WhatsApp sandbox webhook to:

```
https://your-tunnel-url/webhook
```

---

## Notes

- Embedding step is a deterministic placeholder (hashes text into a pseudo-random vector), not a real embedding model — swap it out for better retrieval.
- No Pinecone sync = state resets on restart.

---

## License

MIT — see [LICENSE](LICENSE).
