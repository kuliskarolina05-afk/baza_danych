import streamlit as st
from supabase import create_client, Client

# --- KONFIGURACJA ---
# Zalecane użycie cache, aby nie tworzyć klienta przy każdym odświeżeniu strony
@st.cache_resource
def get_supabase_client():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Problem z konfiguracją kluczy w secrets.toml: {e}")
        return None

supabase = get_supabase_client()

def main():
    if not supabase:
        st.stop()

    st.set_page_config(page_title="Zarządzanie Magazynem", layout="centered")
    st.title("📦 System Zarządzania Produktami")

    menu = ["Dodaj Produkt", "Dodaj Kategorię", "Podgląd Bazy"]
    choice = st.sidebar.selectbox("Menu", menu)

    # --- SEKCJA: DODAWANIE KATEGORII ---
    if choice == "Dodaj Kategorię":
        st.header("Dodaj nową kategorię")
        with st.form("form_kategoria", clear_on_submit=True):
            nazwa_kat = st.text_input("Nazwa kategorii")
            opis_kat = st.text_area("Opis")
            submit_kat = st.form_submit_button("Zapisz kategorię")

            if submit_kat:
                if nazwa_kat:
                    try:
                        # WAŻNE: Sprawdź czy w Supabase masz "Kategorie" czy "kategorie"
                        res = supabase.table("Kategorie").insert({"nazwa": nazwa_kat, "opis": opis_kat}).execute()
                        st.success(f"Dodano kategorię: {nazwa_kat}")
                    except Exception as e:
                        st.error(f"Błąd zapisu: {e}")
                else:
                    st.warning("Nazwa kategorii jest wymagana.")

    # --- SEKCJA: DODAWANIE PRODUKTU ---
    elif choice == "Dodaj Produkt":
        st.header("Dodaj nowy produkt")
        
        kategorie_opcje = {}
        try:
            # Pobieranie kategorii
            res_kat = supabase.table("Kategorie").select("id, nazwa").execute()
            if res_kat.data:
                kategorie_opcje = {item['nazwa']: item['id'] for item in res_kat.data}
            else:
                st.info("Baza kategorii jest pusta.")
        except Exception as e:
            st.error(f"Błąd połączenia z tabelą Kategorie: {e}. Sprawdź uprawnienia RLS w Supabase!")

        with st.form("form_produkt", clear_on_submit=True):
            nazwa_prod = st.text_input("Nazwa produktu")
            liczba_prod = st.number_input("Liczba", min_value=0, step=1)
            cena_prod = st.number_input("Cena", min_value=0.0, format="%.2f")
            
            wybrana_kat_nazwa = st.selectbox(
                "Kategoria", 
                options=list(kategorie_opcje.keys()) if kategorie_opcje else ["Brak kategorii"]
            )
            
            submit_prod = st.form_submit_button("Dodaj produkt")

            if submit_prod:
                if not kategorie_opcje:
                    st.error("Najpierw dodaj kategorię!")
                elif nazwa_prod:
                    try:
                        prod_data = {
                            "nazwa": nazwa_prod,
                            "liczba": liczba_prod,
                            "cena": cena_prod,
                            "kategoria_id": kategorie_opcje[wybrana_kat_nazwa]
                        }
                        supabase.table("Produkty").insert(prod_data).execute()
                        st.success(f"Dodano produkt: {nazwa_prod}")
                    except Exception as e:
                        st.error(f"Błąd podczas dodawania produktu: {e}")
                else:
                    st.warning("Podaj nazwę produktu.")

    # --- SEKCJA: PODGLĄD ---
    elif choice == "Podgląd Bazy":
        st.header("Aktualny stan bazy")
        tab1, tab2 = st.tabs(["Produkty", "Kategorie"])
        
        with tab1:
            try:
                res_p = supabase.table("Produkty").select("*").execute()
                st.dataframe(res_p.data if res_p.data else "Brak danych")
            except Exception as e:
                st.error(f"Nie można pobrać Produktów: {e}")
                
        with tab2:
            try:
                res_k = supabase.table("Kategorie").select("*").execute()
                st.dataframe(res_k.data if res_k.data else "Brak danych")
            except Exception as e:
                st.error(f"Nie można pobrać Kategorii: {e}")

if __name__ == "__main__":
    main()
