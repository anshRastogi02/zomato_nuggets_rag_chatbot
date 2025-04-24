import os
import faiss
import torch
from sentence_transformers import SentenceTransformer
from transformers import pipeline, AutoTokenizer
import google.generativeai as genai
import streamlit as st

# Configure your API key for Gemini
genai.configure(api_key="AIzaSyB_QYAPahTDJb0w7DB17Docfw87AAM6tRE")

# Load Gemini model
model = genai.GenerativeModel("gemini-2.0-flash")

# Load embedding model
embedder = SentenceTransformer('all-MiniLM-L6-v2')

# Function to load text blobs
def load_text_blobs(folder_path: str):
    text_chunks = []
    for file in os.listdir(folder_path):
        if file.endswith("_blobs.txt"):
            with open(os.path.join(folder_path, file), 'r', encoding='utf-8') as f:
                chunks = f.read().split("="*80)
                for chunk in chunks:
                    chunk = chunk.strip()
                    if chunk:
                        text_chunks.append(chunk)
    return text_chunks

print("🔍 Loading text blobs...")
text_blobs = load_text_blobs("text_blobs")
print(f"✅ Loaded {len(text_blobs)} chunks.")

# Create embeddings and FAISS index
embeddings = embedder.encode(text_blobs, convert_to_tensor=True)
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings.cpu().detach().numpy())
print(f"📦 Indexed {len(text_blobs)} blobs.")

# Load model & tokenizer for GPT-2
qa_pipeline = pipeline("text-generation", model="gpt2")
tokenizer = AutoTokenizer.from_pretrained("gpt2")

MAX_INPUT_TOKENS = 1024

def truncate_prompt(prompt, max_tokens=MAX_INPUT_TOKENS):
    input_ids = tokenizer.encode(prompt, truncation=True, max_length=max_tokens)
    return tokenizer.decode(input_ids, skip_special_tokens=True)

# Function for RAG-based answering
def rag_ask(query: str, top_k: int = 5):
    query_embedding = embedder.encode([query])
    _, top_indices = index.search(query_embedding, top_k)

    context = "\n\n".join([text_blobs[i] for i in top_indices[0]])
    prompt = f"""Answer the question below using the provided context.

Context:
{context}

Question: {query}
Answer:"""

    print("🤖 Generating response with Gemini...")
    response = model.generate_content(prompt)
    return response.text.strip()

# Streamlit Interface
st.title("Gemini RAG Chatbot")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Capture user input and respond
if prompt := st.chat_input("Ask me anything about the food items or type 'exit' to quit"):
    if prompt.lower() == 'exit':
        st.stop()
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        answer = rag_ask(prompt)
        st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
