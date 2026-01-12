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
            # Pobieramy dane z tabeli 'produkty' (mała litera wg schematu)
            res = supabase.table("produkty").select("*").execute()
            if res.data:
                df = pd.DataFrame(res.data)
                
                col1, col2, col3 = st.columns(3)
                total_val = (df['cena'] * df['liczba']).sum()
                col1.metric("Wartość towarów", f"{total_val:,.2f} zł")
                col2.metric("Suma sztuk", int(df['liczba'].sum()))
                col3.metric("Liczba pozycji", len(df))

                st.subheader("Stany magazynowe")
                st.bar_chart(df.set_index("nazwa")["liczba"])
            else:
                st.info("Brak danych.")
        except Exception as e:
            st.error(f"Błąd dashboardu: {e}")

    # --- 3. PODGLĄD TABEL ---
    elif choice == "🛒 Produkty":
        st.header("Tabela Produkty")
        res = supabase.table("produkty").select("*").execute()
        st.dataframe(res.data, use_container_width=True)

    elif choice == "📂 Kategorie":
        st.header("Tabela Kategorie")
        res = supabase.table("Kategorie").select("*").execute()
        st.dataframe(res.data, use_container_width=True)

    # --- 4. DODAWANIE (Z MAPOWANIEM KOLUMN ZE ZDJĘCIA) ---
    elif choice == "➕ Dodaj Nowy":
        tab1, tab2 = st.tabs(["Produkt", "Kategorię"])
        
        with tab2:
            with st.form("form_kat"):
                # Tabela 'Kategorie' -> kolumny 'Nazwa', 'Opis' (duże litery wg schematu)
                k_nazwa = st.text_input("Nazwa kategorii")
                k_opis = st.text_area("Opis")
                if st.form_submit_button("Dodaj kategorię"):
                    supabase.table("Kategorie").insert({"Nazwa": k_nazwa, "Opis": k_opis}).execute()
                    st.success("Dodano kategorię!")
                    st.rerun()

        with tab1:
            # Pobranie kategorii do selectboxa
            res_k = supabase.table("Kategorie").select("id, Nazwa").execute()
            kat_dict = {item['Nazwa']: item['id'] for item in res_k.data} if res_k.data else {}
            
            with st.form("form_prod"):
                # Tabela 'produkty' -> kolumny małe: nazwa, cena, liczba, kategoria_id
                p_nazwa = st.text_input("Nazwa produktu")
                p_cena = st.number_input("Cena", min_value=0.0)
                p_liczba = st.number_input("Liczba", min_value=0)
                p_kat = st.selectbox("Wybierz kategorię", options=list(kat_dict.keys()))
                
                if st.form_submit_button("Dodaj produkt"):
                    new_data = {
                        "nazwa": p_nazwa,
                        "cena": p_cena,
                        "liczba": p_liczba,
                        "kategoria_id": kat_dict[p_kat]
                    }
                    supabase.table("produkty").insert(new_data).execute()
                    st.success("Produkt dodany!")
                    st.rerun()

if __name__ == "__main__":
    main()
