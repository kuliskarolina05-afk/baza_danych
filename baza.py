import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

# --- 1. POŁĄCZENIE ---
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"❌ Błąd połączenia: {e}")
        return None

supabase = init_connection()

def main():
    st.set_page_config(page_title="Lokalny Sklepik", layout="wide", page_icon="🛍️")
    
    # CSS dla jednolitego tła
    st.markdown("""
        <style>
        .stApp, .main, div[data-testid="metric-container"] { background-color: #f0f2f6 !important; }
        div[data-testid="metric-container"] { border: none !important; box-shadow: none !important; }
        .header-box { background: linear-gradient(90deg, #2E7D32 0%, #4CAF50 100%); color: white; padding: 1.5rem; border-radius: 15px; text-align: center; margin-bottom: 2rem; }
        </style>
    """, unsafe_allow_html=True)

    if not supabase: st.stop()

    # --- MENU ---
    with st.sidebar:
        st.markdown("<h2 style='text-align: center;'>🛍️ Lokalny Sklepik</h2>", unsafe_allow_html=True)
        choice = st.selectbox("Nawigacja:", ["📈 Panel Analityczny", "📋 Stan Magazynu", "📂 Kategorie", "⚙️ Zarządzanie"])

    st.markdown("<div class='header-box'><h1 style='margin:0;'>🛍️ LOKALNY SKLEPIK</h1></div>", unsafe_allow_html=True)

    # --- MODUŁ KATEGORIE (POPRAWIONY) ---
    if choice == "📂 Kategorie":
        st.subheader("📂 Kategorie Towarów")
        res = supabase.table("kategorie").select("*").execute()
        # hide_index=True usuwa kolumnę 0, 1, 2...
        st.dataframe(res.data, use_container_width=True, hide_index=True)

    # --- MODUŁ STAN MAGAZYNU (POPRAWIONY) ---
    elif choice == "📋 Stan Magazynu":
        st.subheader("📋 Aktualny Stan")
        res = supabase.table("produkty").select("*").execute()
        st.dataframe(res.data, use_container_width=True, hide_index=True)

    # --- MODUŁ ANALITYCZNY ---
    elif choice == "📈 Panel Analityczny":
        res = supabase.table("produkty").select("*").execute()
        if res.data:
            df = pd.DataFrame(res.data)
            m1, m2, m3 = st.columns(3)
            m1.metric("Suma sztuk", int(df['liczba'].sum()))
            m2.metric("Liczba pozycji", len(df))
            m3.metric("Wartość (szacunkowa)", f"{(df['cena']*df['liczba']).sum()} zł")
            st.bar_chart(df.set_index("nazwa")["liczba"])
            st.write("### ⚠️ Niskie stany")
            st.dataframe(df[df['liczba'] < 5], use_container_width=True, hide_index=True)

    # --- ZARZĄDZANIE ---
    elif choice == "⚙️ Zarządzanie":
        t_dostawa, t_prod, t_kat = st.tabs(["🚚 Dostawa", "➕ Produkt", "📁 Kategoria"])
        
        with t_kat:
            with st.form("f_kat"):
                n = st.text_input("Nazwa (np. Nabiał)")
                o = st.text_input("Opis (np. Mleka, sery, jogurty)")
                if st.form_submit_button("Dodaj"):
                    supabase.table("kategorie").insert({"Nazwa": n, "Opis": o}).execute()
                    st.success("Dodano!")
                    st.rerun()
        
        with t_dostawa:
            # Tutaj logika dodawania sztuk (którą już masz)
            st.info("Wybierz produkt i dodaj ilość sztuk.")
            # ... (Twój kod dostawy)

if __name__ == "__main__":
    main()
