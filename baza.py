import streamlit as st
from supabase import create_client, Client

# --- KONFIGURACJA POŁĄCZENIA ---
# Zastąp poniższe dane swoimi poświadczeniami z Supabase Settings -> API
SUPABASE_URL = "TWOJ_URL_SUPABASE"
SUPABASE_KEY = "TWOJ_KEY_ANON_PUBLIC"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def main():
    st.set_page_config(page_title="Zarządzanie Magazynem", layout="centered")
    st.title("📦 System Zarządzania Produktami")

    menu = ["Dodaj Produkt", "Dodaj Kategorię", "Podgląd Bazy"]
    choice = st.sidebar.selectbox("Menu", menu)

    # --- SEKCJA: DODAWANIE KATEGORII ---
    if choice == "Dodaj Kategorię":
        st.header("Dodaj nową kategorię")
        with st.form("form_kategoria"):
            nazwa_kat = st.text_input("Nazwa kategorii")
            opis_kat = st.text_area("Opis")
            submit_kat = st.form_submit_button("Zapisz kategorię")

            if submit_kat:
                if nazwa_kat:
                    data = {"nazwa": nazwa_kat, "opis": opis_kat}
                    try:
                        supabase.table("Kategorie").insert(data).execute()
                        st.success(f"Dodano kategorię: {nazwa_kat}")
                    except Exception as e:
                        st.error(f"Błąd: {e}")
                else:
                    st.warning("Nazwa kategorii jest wymagana.")

    # --- SEKCJA: DODAWANIE PRODUKTU ---
    elif choice == "Dodaj Produkt":
        st.header("Dodaj nowy produkt")
        
        # Pobranie kategorii do selectboxa
        try:
            res_kat = supabase.table("Kategorie").select("id, nazwa").execute()
            kategorie_opcje = {item['nazwa']: item['id'] for item in res_kat.data}
        except Exception:
            kategorie_opcje = {}
            st.error("Nie udało się pobrać kategorii. Dodaj najpierw kategorię!")

        with st.form("form_produkt"):
            nazwa_prod = st.text_input("Nazwa produktu")
            liczba_prod = st.number_input("Liczba", min_value=0, step=1)
            cena_prod = st.number_input("Cena", min_value=0.0, format="%.2f")
            wybrana_kat_nazwa = st.selectbox("Kategoria", list(kategorie_opcje.keys()))
            
            submit_prod = st.form_submit_button("Dodaj produkt")

            if submit_prod:
                if nazwa_prod and wybrana_kat_nazwa:
                    prod_data = {
                        "nazwa": nazwa_prod,
                        "liczba": liczba_prod,
                        "cena": cena_prod,
                        "kategoria_id": kategorie_opcje[wybrana_kat_nazwa]
                    }
                    try:
                        supabase.table("Produkty").insert(prod_data).execute()
                        st.success(f"Dodano produkt: {nazwa_prod}")
                    except Exception as e:
                        st.error(f"Błąd: {e}")
                else:
                    st.warning("Uzupełnij nazwę i wybierz kategorię.")

    # --- SEKCJA: PODGLĄD ---
    elif choice == "Podgląd Bazy":
        st.header("Aktualny stan bazy")
        
        st.subheader("Produkty")
        prod_res = supabase.table("Produkty").select("id, nazwa, liczba, cena, kategoria_id").execute()
        if prod_res.data:
            st.table(prod_res.data)
        
        st.subheader("Kategorie")
        kat_res = supabase.table("Kategorie").select("*").execute()
        if kat_res.data:
            st.table(kat_res.data)

if __name__ == "__main__":
    main()
