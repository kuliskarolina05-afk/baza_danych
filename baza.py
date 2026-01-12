import streamlit as st
from supabase import create_client, Client

# --- KONFIGURACJA POŁĄCZENIA ---
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"❌ Problem z secrets.toml: {e}")
        return None

supabase = init_connection()

def main():
    st.set_page_config(page_title="Magazyn Supabase", layout="wide")
    st.title("📦 Zarządzanie Magazynem")

    if not supabase:
        st.stop()

    menu = ["Podgląd Bazy", "Dodaj Produkt", "Dodaj Kategorię"]
    choice = st.sidebar.selectbox("Menu", menu)

    # --- SEKCJA: PODGLĄD BAZY ---
    if choice == "Podgląd Bazy":
        st.header("Aktualny stan magazynowy")
        t1, t2 = st.tabs(["🛒 Produkty", "📂 Kategorie"])
        
        with t1:
            try:
                # Tabela z DUŻEJ litery
                res_p = supabase.table("Produkty").select("*").execute()
                st.dataframe(res_p.data if res_p.data else "Brak danych w tabeli Produkty")
            except Exception as e:
                st.error(f"Błąd tabeli 'Produkty': {e}")

        with t2:
            try:
                # Tabela z MAŁEJ litery
                res_k = supabase.table("kategorie").select("*").execute()
                st.dataframe(res_k.data if res_k.data else "Brak danych w tabeli kategorie")
            except Exception as e:
                st.error(f"Błąd tabeli 'kategorie': {e}")

    # --- SEKCJA: DODAWANIE KATEGORII ---
    elif choice == "Dodaj Kategorię":
        st.header("Dodaj nową kategorię")
        with st.form("form_kat", clear_on_submit=True):
            nazwa_kat = st.text_input("Nazwa kategorii")
            opis_kat = st.text_area("Opis")
            if st.form_submit_button("Zapisz kategorię"):
                if nazwa_kat:
                    # Używamy małej litery 'kategorie'
                    supabase.table("kategorie").insert({"nazwa": nazwa_kat, "opis": opis_kat}).execute()
                    st.success(f"Dodano kategorię: {nazwa_kat}")
                else:
                    st.warning("Nazwa jest wymagana.")

    # --- SEKCJA: DODAWANIE PRODUKTU ---
    elif choice == "Dodaj Produkt":
        st.header("Dodaj nowy produkt")
        
        # Pobieranie kategorii (mała litera)
        kategorie_opcje = {}
        try:
            res_kat = supabase.table("kategorie").select("id, nazwa").execute()
            kategorie_opcje = {item['nazwa']: item['id'] for item in res_kat.data} if res_kat.data else {}
        except Exception as e:
            st.error(f"Nie udało się pobrać kategorii: {e}")

        with st.form("form_prod", clear_on_submit=True):
            nazwa_prod = st.text_input("Nazwa produktu")
            cena = st.number_input("Cena", min_value=0.0, format="%.2f")
            ilosc = st.number_input("Ilość", min_value=0, step=1)
            wybrana_kat = st.selectbox("Kategoria", list(kategorie_opcje.keys()) if kategorie_opcje else ["Brak"])
            
            if st.form_submit_button("Dodaj produkt"):
                if nazwa_prod and kategorie_opcje:
                    try:
                        # Używamy dużej litery 'Produkty'
                        data = {
                            "nazwa": nazwa_prod,
                            "cena": cena,
                            "ilosc": ilosc,
                            "kategoria_id": kategorie_opcje[wybrana_kat]
                        }
                        supabase.table("Produkty").insert(data).execute()
                        st.success(f"Dodano produkt: {nazwa_prod}")
                    except Exception as e:
                        st.error(f"Błąd podczas dodawania: {e}")

if __name__ == "__main__":
    main()
