import streamlit as st
from supabase import create_client, Client

# --- 1. INICJALIZACJA POŁĄCZENIA ---
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"❌ Brak konfiguracji w secrets.toml: {e}")
        return None

supabase = init_connection()

def main():
    st.set_page_config(page_title="Magazyn Supabase", layout="wide", page_icon="📦")
    st.title("📦 System Zarządzania Magazynem")

    if not supabase:
        st.stop()

    menu = ["Podgląd Bazy", "Dodaj Produkt", "Dodaj Kategorię"]
    choice = st.sidebar.selectbox("Menu", menu)

    # --- 2. SEKCJA: PODGLĄD BAZY ---
    if choice == "Podgląd Bazy":
        st.header("Aktualny stan magazynowy")
        tab1, tab2 = st.tabs(["🛒 Produkty", "📂 Kategorie"])
        
        with tab1:
            try:
                # Tabela Produkty (duża litera)
                res_p = supabase.table("Produkty").select("*").execute()
                if res_p.data:
                    st.dataframe(res_p.data, use_container_width=True)
                else:
                    st.info("Tabela Produkty jest pusta.")
            except Exception as e:
                st.error(f"Błąd tabeli Produkty: {e}")

        with tab2:
            try:
                # Tabela kategorie (mała litera)
                res_k = supabase.table("kategorie").select("*").execute()
                if res_k.data:
                    st.dataframe(res_k.data, use_container_width=True)
                else:
                    st.info("Tabela kategorie jest pusta.")
            except Exception as e:
                st.error(f"Błąd tabeli kategorie: {e}")

    # --- 3. SEKCJA: DODAWANIE KATEGORII ---
    elif choice == "Dodaj Kategorię":
        st.header("Dodaj nową kategorię")
        with st.form("form_kat", clear_on_submit=True):
            # Używamy dużej litery 'Nazwa' i 'Opis' zgodnie z Twoim schematem
            val_nazwa = st.text_input("Nazwa kategorii")
            val_opis = st.text_area("Opis")
            submit_kat = st.form_submit_button("Zapisz kategorię")

            if submit_kat:
                if val_nazwa:
                    try:
                        supabase.table("kategorie").insert({
                            "Nazwa": val_nazwa, 
                            "Opis": val_opis
                        }).execute()
                        st.success(f"Dodano kategorię: {val_nazwa}")
                    except Exception as e:
                        st.error(f"Błąd zapisu kategorii: {e}")
                else:
                    st.warning("Nazwa kategorii jest wymagana.")

    # --- 4. SEKCJA: DODAWANIE PRODUKTU ---
    elif choice == "Dodaj Produkt":
        st.header("Dodaj nowy produkt")
        
        # Pobieranie dostępnych kategorii do listy
        kategorie_opcje = {}
        try:
            res_kat = supabase.table("kategorie").select("id, Nazwa").execute()
            if res_kat.data:
                kategorie_opcje = {item['Nazwa']: item['id'] for item in res_kat.data}
        except Exception as e:
            st.error(f"Nie udało się pobrać kategorii: {e}")

        with st.form("form_prod", clear_on_submit=True):
            p_nazwa = st.text_input("Nazwa produktu")
            p_cena = st.number_input("Cena", min_value=0.0, format="%.2f")
            p_ilosc = st.number_input("Ilość", min_value=0, step=1)
            wybrana_kat = st.selectbox(
                "Wybierz kategorię", 
                options=list(kategorie_opcje.keys()) if kategorie_opcje else ["Brak kategorii"]
            )
            
            submit_prod = st.form_submit_button("Dodaj produkt")

            if submit_prod:
                if not kategorie_opcje:
                    st.error("Błąd: Najpierw musisz dodać kategorię!")
                elif p_nazwa:
                    try:
                        # Mapowanie kolumn (Uwzględniam brak polskich znaków w 'Ilosc')
                        data_to_insert = {
                            "Nazwa": p_nazwa,
                            "Cena": p_cena,
                            "Ilosc": p_ilosc,
                            "kategoria_id": kategorie_opcje[wybrana_kat]
                        }
                        supabase.table("Produkty").insert(data_to_insert).execute()
                        st.success(f"Dodano produkt: {p_nazwa}")
                    except Exception as e:
                        st.error(f"Błąd podczas dodawania produktu: {e}")
                else:
                    st.warning("Podaj nazwę produktu.")

if __name__ == "__main__":
    main()
