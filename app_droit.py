import streamlit as st
import google.generativeai as genai
import os
import glob

# --- CONFIGURATION ---
st.set_page_config(page_title="Tuteur Droit Admin", page_icon="⚖️")
st.title("⚖️ Assistant Droit Administratif")

# --- RÉCUPÉRATION DE LA CLÉ API SECRÈTE ---
# Elle sera configurée dans l'étape suivante sur le site de Streamlit
api_key = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=api_key)

# --- PROMPT SYSTÈME (VOTRE VERSION V2) ---
SYSTEM_PROMPT = """
CONTEXTE ET RÔLE :
Tu es l'assistant pédagogique virtuel expert en Droit Administratif du Professeur Coulibaly.
Ta base de connaissances est STRICTEMENT limitée aux documents fournis en contexte ("le cours du professeur Coulibaly").

RÈGLES ABSOLUES :
1. SOURCE UNIQUE : Tes réponses doivent provenir EXCLUSIVEMENT du cours fourni. N'utilise jamais tes connaissances externes pour combler un vide.
2. HONNÊTETÉ : Si la réponse n'est pas dans le cours, dis : "Cette précision ne figure pas dans le cours du Pr. Coulibaly." Ne tente pas d'inventer.
3. PRÉCISION : Cite toujours les arrêts (ex: **CE, 1933, Benjamin**) tels qu'ils apparaissent dans le document.

STYLE ET FORMAT :
- Ton : Professionnel, pédagogique, encourageant.
- Oralité : Fais des phrases courtes et claires.
- Structure : Utilise des titres, des listes à puces et du gras pour les mots-clés.
"""

# --- FONCTION DE CHARGEMENT DES COURS ---
@st.cache_resource
def load_and_process_pdfs():
    """Charge tous les PDF du dossier et les envoie à Gemini une seule fois."""
    pdf_files = glob.glob("*.pdf")
    
    if not pdf_files:
        st.error("Aucun fichier PDF trouvé dans le dossier !")
        return None

    uploaded_files_refs = []
    status_text = st.empty()
    status_text.text(f"Chargement de {len(pdf_files)} chapitres de cours...")

    for pdf in pdf_files:
        # Envoi du fichier aux serveurs Google
        uploaded_file = genai.upload_file(pdf, mime_type="application/pdf")
        uploaded_files_refs.append(uploaded_file)
    
    status_text.empty() # On efface le message
    return uploaded_files_refs

# --- DÉMARRAGE DE LA SESSION ---
if "chat_session" not in st.session_state:
    try:
        # On charge les docs
        docs = load_and_process_pdfs()
        
        if docs:
            # On configure le modèle avec les docs et le prompt
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=SYSTEM_PROMPT
            )
            # On lance le chat avec les documents en historique "caché"
            st.session_state.chat_session = model.start_chat(
                history=[
                    {"role": "user", "parts": docs},
                    {"role": "model", "parts": ["Bien reçu. Je suis prêt."]}
                ]
            )
            st.session_state.messages = []
            st.success("✅ Le cours est chargé. Posez votre question !")
            
    except Exception as e:
        st.error(f"Erreur de connexion : {e}")

# --- INTERFACE DE CHAT ---
# Afficher l'historique
if "messages" in st.session_state:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Zone de saisie
if prompt := st.chat_input("Votre question sur le cours..."):
    # Affichage utilisateur
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Réponse IA
    if st.session_state.chat_session:
        with st.chat_message("assistant"):
            with st.spinner("Recherche dans le cours..."):
                response = st.session_state.chat_session.send_message(prompt)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
