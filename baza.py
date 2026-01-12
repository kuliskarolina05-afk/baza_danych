import streamlit as st
from supabase import create_client, Client
import pandas as pd

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
    st.set_page_config(page_title="Magazyn Supabase", layout="wide", page_icon="📦")
    st.title("📦 System Zarządzania Magazynem")

    if not supabase:
        st.stop()

    menu = ["📊 Dashboard", "🛒 Produkty", "📂 Kategorie", "➕ Dodaj Nowy"]
    choice = st.sidebar.selectbox("Menu", menu)

    # --- 2. DASHBOARD ---
    if choice == "📊 Dashboard":
        st.header("Statystyki magazynu")
        try:
            # Tabela 'produkty' (małe litery)
            res = supabase.table("produkty").select("*").execute()
            if res.data:
                df = pd.DataFrame(res.data)
                
                col1, col2, col3 = st.columns(3)
                # Kolumny 'cena' i 'liczba' (małe litery)
                total_val = (df['cena'] * df['liczba']).sum()
                col1.metric("Wartość towarów", f"{total_val:,.2f} zł")
                col2.metric("Suma sztuk", int(df['liczba'].sum()))
                col3.metric("Liczba pozycji", len(df))

                st.subheader("Stany magazynowe")
                st.bar_chart(df.set_index("nazwa")["liczba"])
            else:
                st.info("Brak danych w tabeli produkty.")
        except Exception as e:
            st.error(f"Błąd dashboardu: {e}")

    # --- 3. PODGLĄD TABEL ---
    elif choice == "🛒 Produkty":
        st.header("Tabela produkty")
        try:
            res = supabase.table("produkty").select("*").execute()
            st.dataframe(res.data, use_container_width=True)
        except Exception as e:
            st.error(f"Błąd tabeli produkty: {e}")

    elif choice == "📂 Kategorie":
        st.header("Tabela kategorie")
        try:
            # Tabela 'kategorie' (małe litery)
            res = supabase.table("kategorie").select("*").execute()
            st.dataframe(res.data, use_container_width=True)
        except Exception as e:
            st.error(f"Błąd tabeli kategorie: {e}")

    # --- 4. DODAWANIE ---
    elif choice == "➕ Dodaj Nowy":
        tab1, tab2 = st.tabs(["Produkt", "Kategorię"])
        
        with tab2:
            st.subheader("Nowa kategoria")
            with st.form("form_kat", clear_on_submit=True):
                # Kolumny 'nazwa' i 'opis' (małe litery)
                k_nazwa = st.text_input("Nazwa kategorii")
                k_opis = st.text_area("Opis")
                if st.form_submit_button("Zapisz kategorię"):
                    if k_nazwa:
                        try:
                            supabase.table("kategorie").insert({
                                "nazwa": k_nazwa, 
                                "opis": k_opis
                            }).execute()
                            st.success("Dodano kategorię!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Błąd zapisu: {e}")
                    else:
                        st.warning("Podaj nazwę kategorii.")

        with tab1:
            st.subheader("Nowy produkt")
            try:
                # Pobranie kategorii - kolumna 'nazwa' (małe litery)
                res_k = supabase.table("kategorie").select("id, nazwa").execute()
                kat_dict = {item['nazwa']: item['id'] for item in res_k.data} if res_k.data else {}
                
                if not kat_dict:
                    st.warning("Najpierw dodaj przynajmniej jedną kategorię!")
                
                with st.form("form_prod", clear_on_submit=True):
                    p_nazwa = st.text_input("Nazwa produktu")
                    p_cena = st.number_input("Cena", min_value=0.0)
                    p_liczba = st.number_input("Liczba", min_value=0)
                    p_kat_name = st.selectbox("Wybierz kategorię", options=list(kat_dict.keys()))
                    
                    if st.form_submit_button("Dodaj produkt"):
                        if p_nazwa and p_kat_name:
                            try:
                                new_data = {
                                    "nazwa": p_nazwa,
                                    "cena": p_cena,
                                    "liczba": p_liczba,
                                    "kategoria_id": kat_dict[p_kat_name]
                                }
                                supabase.table("produkty").insert(new_data).execute()
                                st.success(f"Dodano produkt: {p_nazwa}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Błąd zapisu produktu: {e}")
                        else:
                            st.warning("Wypełnij nazwę produktu.")
            except Exception as e:
                st.error(f"Błąd ładowania formularza: {e}")

if __name__ == "__main__":
    main()
