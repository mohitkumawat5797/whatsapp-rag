import os
from flask import Flask, request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from groq import Groq
from pinecone import Pinecone
import requests
from io import BytesIO
from dotenv import load_dotenv
import hashlib
import numpy as np

load_dotenv()

# Initialize
app = Flask(__name__)
# Separate environment variables
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Groq
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
groq_client = Groq(api_key=GROQ_API_KEY)

# Pinecone with error handling
try:
    pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
    index = pc.Index(os.getenv('PINECONE_INDEX_NAME'))
    pinecone_enabled = True
except Exception as e:
    pinecone_enabled = False
    print(f"⚠️ Pinecone disabled: {e}")

# In-memory storage
pdf_storage = {}

def get_embedding(text):
    """Create embedding"""
    hash_val = hashlib.md5(text.encode()).digest()
    seed = int.from_bytes(hash_val[:4], 'big')
    np.random.seed(seed)
    return np.random.rand(1024).tolist()

def extract_pdf_text(pdf_content):
    """Extract text from PDF - with multiple fallbacks"""
    text = ""
    
    try:
        # Try pdfplumber first (more robust)
        import pdfplumber
        pdf_file = BytesIO(pdf_content)
        with pdfplumber.open(pdf_file) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text += f"\n--- Page {page_num + 1} ---\n"
                text += page.extract_text() or ""
        return text
    except Exception as e1:
        print(f"[PDF] pdfplumber failed: {e1}, trying PyPDF2...")
        
        try:
            # Fallback to PyPDF2
            import PyPDF2
            pdf_file = BytesIO(pdf_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            for page_num, page in enumerate(pdf_reader.pages):
                text += f"\n--- Page {page_num + 1} ---\n"
                text += page.extract_text() or ""
            return text
        except Exception as e2:
            print(f"[PDF] PyPDF2 failed: {e2}, using raw text extraction...")
            
            # Last resort - try to extract any readable text
            try:
                return pdf_content.decode('utf-8', errors='ignore')
            except:
                return ""

@app.route('/webhook', methods=['POST'])
def webhook():
    """Receive WhatsApp messages"""
    incoming_msg = request.values.get('Body', '').strip()
    sender = request.values.get('From', '')
    media_url = request.values.get('MediaUrl0', '')
    
    response = MessagingResponse()
    
    try:
        if media_url:
            msg = process_pdf(media_url, sender)
            response.message(msg)
        elif incoming_msg:
            answer = answer_question(incoming_msg, sender)
            response.message(answer)
        else:
            response.message("📄 Send a PDF or 💬 Ask a question!")
    
    except Exception as e:
        print(f"[ERROR] {e}")
        response.message(f"❌ Error: {str(e)[:100]}")
    
    return str(response)

def process_pdf(pdf_url, user_id):
    """Download and process PDF"""
    try:
        print(f"[PDF] Starting download from {pdf_url}")
        
        # Download
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        pdf_response = requests.get(
            pdf_url, 
            auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
            timeout=30)
        pdf_content = pdf_response.content
        
        print(f"[PDF] Downloaded {len(pdf_content)} bytes")
        
        # Extract text
        full_text = extract_pdf_text(pdf_content)
        
        if not full_text.strip():
            return "❌ Couldn't extract text from PDF. Try another file."
        
        print(f"[PDF] Extracted {len(full_text)} characters")
        
        # Split chunks
        chunks = [full_text[i:i+600] for i in range(0, len(full_text), 600)]
        chunks = [c.strip() for c in chunks if c.strip()]
        
        print(f"[PDF] Created {len(chunks)} chunks")
        
        # Store
        if user_id not in pdf_storage:
            pdf_storage[user_id] = []
        pdf_storage[user_id].extend(chunks)
        
        # To Pinecone
        vectors = []
        for i, chunk in enumerate(chunks):
            embedding = get_embedding(chunk)
            vectors.append((
                f"{user_id}_chunk_{len(pdf_storage[user_id]) - len(chunks) + i}",
                embedding,
                {"text": chunk[:300], "user": user_id}
            ))
        
        if vectors:
            try:
                index.upsert(vectors=vectors)
                print(f"[PDF] Stored {len(vectors)} in Pinecone")
            except Exception as e:
                print(f"[PDF] Pinecone store failed (ok, using memory): {e}")
        
        return f"✅ PDF processed! {len(chunks)} chunks indexed.\n\n📝 Now ask me questions about it!"
    
    except Exception as e:
        print(f"[PDF ERROR] {str(e)}")
        return f"❌ Error: {str(e)[:80]}"

def answer_question(question, user_id):
    """Answer using RAG with Groq"""
    try:
        print(f"[Q] {user_id}: {question}")
        
        if user_id not in pdf_storage or not pdf_storage[user_id]:
            return "❌ No PDF yet. Send one first! 📄"
        
        # Get embedding
        q_embedding = get_embedding(question)
        
        # Search Pinecone
        context = ""
        try:
            results = index.query(
                vector=q_embedding,
                top_k=3,
                filter={"user": user_id}
            )
            if results.matches:
                context = "\n---\n".join([
                    m.metadata.get('text', '') 
                    for m in results.matches
                ])
        except:
            pass
        
        # Fallback to memory
        if not context:
            context = "\n---\n".join(pdf_storage[user_id][:3])
        
        if not context.strip():
            return "❌ No relevant content found."
        
        # Ask Groq (FREE!)
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "user",
                    "content": f"""Answer based ONLY on this content. Be concise.

{context}

Question: {question}"""
                }
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        print(f"[Q ERROR] {e}")
        return f"❌ Error: {str(e)[:80]}"

@app.route('/', methods=['GET'])
def home():
    return "✅ WhatsApp RAG Bot Running with Groq (FREE!)"

if __name__ == '__main__':
    print("🚀 Bot starting with Groq...")
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )