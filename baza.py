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
            res = supabase.table("produkty").select("*").execute()
            if res.data:
                df = pd.DataFrame(res.data)
                col1, col2, col3 = st.columns(3)
                # Obliczenia
                total_val = (df['cena'] * df['liczba']).sum()
                col1.metric("Wartość towarów", f"{total_val:,.2f} zł")
                col2.metric("Suma sztuk", int(df['liczba'].sum()))
                col3.metric("Liczba pozycji", len(df))
                st.bar_chart(df.set_index("nazwa")["liczba"])
            else:
                st.info("Brak danych.")
        except Exception as e:
            st.error(f"Błąd dashboardu: {e}")

    # --- 3. PODGLĄD ---
    elif choice == "🛒 Produkty":
        res = supabase.table("produkty").select("*").execute()
        st.dataframe(res.data, use_container_width=True)

    elif choice == "📂 Kategorie":
        res = supabase.table("kategorie").select("*").execute()
        st.dataframe(res.data, use_container_width=True)

    # --- 4. DODAWANIE ---
    elif choice == "➕ Dodaj Nowy":
        tab1, tab2 = st.tabs(["Produkt", "Kategorię"])
        
        with tab2:
            with st.form("form_kat"):
                k_nazwa = st.text_input("Nazwa kategorii")
                k_opis = st.text_area("Opis")
                if st.form_submit_button("Zapisz kategorię"):
                    try:
                        supabase.table("kategorie").insert({"Nazwa": k_nazwa, "Opis": k_opis}).execute()
                        st.success("Dodano!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Błąd: {e}")

        with tab1:
            try:
                # Pobieramy kategorie
                res_k = supabase.table("kategorie").select("id, Nazwa").execute()
                kat_dict = {item['Nazwa']: item['id'] for item in res_k.data} if res_k.data else {}
                
                with st.form("form_prod"):
                    p_nazwa = st.text_input("Nazwa produktu")
                    # Ustawiamy step=1, aby sugerować liczby całkowite
                    p_cena = st.number_input("Cena (tylko liczby całkowite)", min_value=0, step=1)
                    p_liczba = st.number_input("Liczba", min_value=0, step=1)
                    p_kat = st.selectbox("Kategoria", options=list(kat_dict.keys()))
                    
                    if st.form_submit_button("Dodaj produkt"):
                        try:
                            # KLUCZOWA POPRAWKA: int() zamienia 3.0 na 3
                            new_prod = {
                                "nazwa": p_nazwa,
                                "cena": int(p_cena), 
                                "liczba": int(p_liczba),
                                "kategoria_id": kat_dict[p_kat]
                            }
                            supabase.table("produkty").insert(new_prod).execute()
                            st.success("Dodano produkt!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Błąd zapisu: {e}")
            except Exception as e:
                st.error(f"Błąd formularza: {e}")

if __name__ == "__main__":
    main()
