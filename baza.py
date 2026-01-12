import streamlit as st
from supabase import create_client, Client

# --- KONFIGURACJA ---
@st.cache_resource
def init_connection():
    try:
        # Upewnij się, że w .streamlit/secrets.toml masz poprawne dane
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Nie znaleziono kluczy w secrets.toml: {e}")
        return None

supabase = init_connection()

def main():
    st.set_page_config(page_title="Magazyn Supabase", layout="wide")
    st.title("📦 Zarządzanie Magazynem")

    if not supabase:
        st.warning("Skonfiguruj połączenie z Supabase w Secrets.")
        st.stop()

    menu = ["Podgląd Bazy", "Dodaj Produkt", "Dodaj Kategorię"]
    choice = st.sidebar.selectbox("Nawigacja", menu)

    # --- SEKCJA: DODAWANIE KATEGORII ---
    if choice == "Dodaj Kategorię":
        st.subheader("Nowa Kategoria")
        with st.form("kat_form"):
            nazwa = st.text_input("Nazwa kategorii")
            opis = st.text_area("Opis")
            if st.form_submit_button("Zapisz"):
                if nazwa:
                    # Używamy małych liter dla pewności (zgodnie ze standardem Postgres)
                    res = supabase.table("kategorie").insert({"nazwa": nazwa, "opis": opis}).execute()
                    st.success(f"Dodano kategorię: {nazwa}")
                else:
                    st.error("Nazwa jest wymagana!")

    # --- SEKCJA: DODAWANIE PRODUKTU ---
    elif choice == "Dodaj Produkt":
        st.subheader("Nowy Produkt")
        
        # Pobieranie kategorii do listy rozwijanej
        try:
            kat_data = supabase.table("kategorie").select("id, nazwa").execute().data
            kategorie_dict = {item['nazwa']: item['id'] for item in kat_data} if kat_data else {}
        except Exception as e:
            st.error(f"Błąd pobierania kategorii: {e}")
            kategorie_dict = {}

        with st.form("prod_form"):
            nazwa_p = st.text_input("Nazwa produktu")
            cena = st.number_input("Cena", min_value=0.0, step=0.01)
            ilosc = st.number_input("Ilość", min_value=0, step=1)
            wybrana_kat = st.selectbox("Wybierz kategorię", list(kategorie_dict.keys()) if kategorie_dict else ["Brak kategorii"])
            
            if st.form_submit_button("Dodaj produkt"):
                if nazwa_p and kategorie_dict:
                    data = {
                        "nazwa": nazwa_p,
                        "cena": cena,
                        "ilosc": ilosc,
                        "kategoria_id": kategorie_dict[wybrana_kat]
                    }
                    supabase.table("produkty").insert(data).execute()
                    st.success(f"Produkt {nazwa_p} został dodany!")

    # --- SEKCJA: PODGLĄD ---
    elif choice == "Podgląd Bazy":
        st.subheader("Stan magazynowy")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("### Produkty")
            try:
                p_res = supabase.table("produkty").select("*").execute()
                st.dataframe(p_res.data)
            except Exception as e:
                st.error(f"Błąd tabeli produkty: {e}")

        with col2:
            st.write("### Kategorie")
            try:
                k_res = supabase.table("kategorie").select("*").execute()
                st.dataframe(k_res.data)
            except Exception as e:
                st.error(f"Błąd tabeli kategorie: {e}")

if __name__ == "__main__":
    main()
