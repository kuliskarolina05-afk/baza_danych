import streamlit as st
from supabase import create_client, Client

# --- KONFIGURACJA ---
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"Problem z konfiguracją kluczy: {e}")
    st.stop()

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
                    # Używamy dokładnie takiej nazwy jak na schemacie: Kategorie
                    res = supabase.table("Kategorie").insert({"nazwa": nazwa_kat, "opis": opis_kat}).execute()
                    if res.data:
                        st.success(f"Dodano kategorię: {nazwa_kat}")
                else:
                    st.warning("Nazwa kategorii jest wymagana.")

    # --- SEKCJA: DODAWANIE PRODUKTU ---
    elif choice == "Dodaj Produkt":
        st.header("Dodaj nowy produkt")
        
        # Pobieranie kategorii z obsługą błędów
        kategorie_opcje = {}
        try:
            res_kat = supabase.table("Kategorie").select("id, nazwa").execute()
            if res_kat.data:
                kategorie_opcje = {item['nazwa']: item['id'] for item in res_kat.data}
            else:
                st.info("Baza kategorii jest pusta. Dodaj pierwszą kategorię w menu bocznym.")
        except Exception as e:
            st.error(f"Błąd połączenia z tabelą Kategorie: {e}")

        with st.form("form_produkt"):
            nazwa_prod = st.text_input("Nazwa produktu")
            liczba_prod = st.number_input("Liczba", min_value=0, step=1)
            # Numeric w Supabase mapujemy na float
            cena_prod = st.number_input("Cena", min_value=0.0, format="%.2f")
            
            # Selectbox pojawi się tylko jeśli są kategorie
            wybrana_kat_nazwa = st.selectbox(
                "Kategoria", 
                options=list(kategorie_opcje.keys()) if kategorie_opcje else ["Brak dostępnych kategorii"]
            )
            
            submit_prod = st.form_submit_button("Dodaj produkt")

            if submit_prod:
                if not kategorie_opcje:
                    st.error("Nie można dodać produktu bez wybranej kategorii!")
                elif nazwa_prod:
                    prod_data = {
                        "nazwa": nazwa_prod,
                        "liczba": liczba_prod,
                        "cena": cena_prod,
                        "kategoria_id": kategorie_opcje[wybrana_kat_nazwa]
                    }
                    res = supabase.table("Produkty").insert(prod_data).execute()
                    if res.data:
                        st.success(f"Dodano produkt: {nazwa_prod}")
                else:
                    st.warning("Podaj nazwę produktu.")

    # --- SEKCJA: PODGLĄD ---
    elif choice == "Podgląd Bazy":
        st.header("Aktualny stan bazy")
        
        tab1, tab2 = st.tabs(["Produkty", "Kategorie"])
        
        with tab1:
            res_p = supabase.table("Produkty").select("*").execute()
            if res_p.data:
                st.dataframe(res_p.data)
            else:
                st.write("Brak produktów.")
                
        with tab2:
            res_k = supabase.table("Kategorie").select("*").execute()
            if res_k.data:
                st.dataframe(res_k.data)
            else:
                st.write("Brak kategorii.")

if __name__ == "__main__":
    main()
