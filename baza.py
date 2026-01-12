import streamlit as st
from supabase import create_client, Client

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
                res_p = supabase.table("Produkty").select("*").execute()
                st.dataframe(res_p.data if res_p.data else "Brak danych")
            except Exception as e:
                st.error(f"Błąd tabeli 'Produkty': {e}")

        with t2:
            try:
                res_k = supabase.table("kategorie").select("*").execute()
                st.dataframe(res_k.data if res_k.data else "Brak danych")
            except Exception as e:
                st.error(f"Błąd tabeli 'kategorie': {e}")

    # --- SEKCJA: DODAWANIE KATEGORII ---
    elif choice == "Dodaj Kategorię":
        st.header("Dodaj nową kategorię")
        with st.form("form_kat", clear_on_submit=True):
            val_nazwa = st.text_input("Nazwa kategorii")
            val_opis = st.text_area("Opis")
            if st.form_submit_button("Zapisz kategorię"):
                if val_nazwa:
                    try:
                        # Zmieniono na 'Nazwa' i 'Opis' (duże litery)
                        supabase.table("kategorie").insert({
                            "Nazwa": val_nazwa, 
                            "Opis": val_opis
                        }).execute()
                        st.success(f"Dodano kategorię: {val_nazwa}")
                    except Exception as e:
                        st.error(f"Błąd zapisu: {e}")
                else:
                    st.warning("Nazwa jest wymagana.")

    # --- SEKCJA: DODAWANIE PRODUKTU ---
    elif choice == "Dodaj Produkt":
        st.header("Dodaj nowy produkt")
        
        kategorie_opcje = {}
        try:
            # Poprawione na "id, Nazwa"
            res_kat = supabase.table("kategorie").select("id, Nazwa").execute()
            if res_kat.data:
                kategorie_opcje = {item['Nazwa']: item['id'] for item in res_kat.data}
        except Exception as e:
            st.error(f"Błąd pobierania kategorii: {e}")

        with st.form("form_prod", clear_on_submit=True):
            p_nazwa = st.text_input("Nazwa produktu")
            p_cena = st.number_input("Cena", min_value=0.0, format="%.2f")
            p_ilosc = st.number_input("Ilość", min_value=0, step=1)
            wybrana_kat = st.selectbox("Kategoria", list(kategorie_opcje.keys()) if kategorie_opcje else ["Brak"])
            
            if st.form_submit_button("Dodaj produkt"):
                if p_nazwa and kategorie_opcje:
                    try:
                        # Tutaj również używamy dużych liter dla kolumn
                        data = {
                            "Nazwa": p_nazwa,
                            "Cena": p_cena,
                            "Ilość": p_ilosc,
                            "Kategoria_id": kategorie_opcje[wybrana_kat]
                        }
                        supabase.table("Produkty").insert(data).execute()
                        st.success(f"Dodano produkt: {p_nazwa}")
                    except Exception as e:
                        st.error(f"Błąd podczas dodawania: {e}")

if __name__ == "__main__":
    main()
