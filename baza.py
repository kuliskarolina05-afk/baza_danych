import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

# --- 1. KONFIGURACJA I POŁĄCZENIE ---
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
    st.set_page_config(page_title="Magazyn Pro v2.0", layout="wide", page_icon="🏢")
    
    # Custom CSS dla lepszego wyglądu
    st.markdown("""
        <style>
        .main { background-color: #f5f7f9; }
        .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        </style>
    """, unsafe_allow_html=True)

    if not supabase:
        st.stop()

    # --- 2. PASEK BOCZNY ---
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/warehouse.png", width=80)
        st.title("Magazyn Pro")
        st.markdown("Zalogowano jako: **Administrator**")
        st.divider()
        menu = ["📊 Dashboard", "🛒 Produkty", "📂 Kategorie", "➕ Zarządzanie"]
        choice = st.selectbox("Nawigacja", menu)
        st.divider()
        st.info(f"Data: {datetime.now().strftime('%d.%m.%Y')}")

    # --- 3. DASHBOARD I RAPORTY ---
    if choice == "📊 Dashboard":
        st.title("📊 Dashboard & Raportowanie")
        
        try:
            res = supabase.table("produkty").select("*").execute()
            if res.data:
                df = pd.DataFrame(res.data)
                
                # Karty z wynikami
                c1, c2, c3, c4 = st.columns(4)
                total_val = (df['cena'] * df['liczba']).sum()
                total_qty = df['liczba'].sum()
                low_stock_count = len(df[df['liczba'] < 5])

                c1.metric("Wartość towarów", f"{total_val:,.2f} zł")
                c2.metric("Suma jednostek", f"{int(total_qty)} szt.")
                c3.metric("Pozycje w bazie", len(df))
                c4.metric("Niskie stany ( <5 )", low_stock_count, delta=-low_stock_count, delta_color="inverse")

                # Wykresy i Raporty
                col_left, col_right = st.columns([2, 1])
                
                with col_left:
                    st.subheader("Wizualizacja zapasów")
                    st.bar_chart(df.set_index("nazwa")["liczba"])
                
                with col_right:
                    st.subheader("⚠️ Alert: Niski stan")
                    low_stock_df = df[df['liczba'] < 5][['nazwa', 'liczba']]
                    if not low_stock_df.empty:
                        st.dataframe(low_stock_df, hide_index=True, use_container_width=True)
                        st.error("Wymagane zamówienie towaru!")
                    else:
                        st.success("Wszystkie produkty są dostępne.")

                # Przycisk pobierania raportu
                st.divider()
                st.subheader("📥 Eksport danych")
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Pobierz pełny raport CSV",
                    data=csv,
                    file_name=f"raport_magazynowy_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime='text/csv',
                )
            else:
                st.info("Brak danych do wyświetlenia raportu.")
        except Exception as e:
            st.error(f"Błąd dashboardu: {e}")

    # --- 4. PRODUKTY ---
    elif choice == "🛒 Produkty":
        st.title("🛒 Lista Produktów")
        res = supabase.table("produkty").select("*").execute()
        st.dataframe(res.data, use_container_width=True, hide_index=True)

    # --- 5. KATEGORIE ---
    elif choice == "📂 Kategorie":
        st.title("📂 Kategorie")
        res = supabase.table("kategorie").select("*").execute()
        st.table(res.data)

    # --- 6. ZARZĄDZANIE (DODAWANIE) ---
    elif choice == "➕ Zarządzanie":
        st.title("➕ Dodawanie do bazy")
        tab_p, tab_k = st.tabs(["🆕 Nowy Produkt", "📁 Nowa Kategoria"])
        
        with tab_k:
            with st.form("form_kat", clear_on_submit=True):
                k_nazwa = st.text_input("Nazwa kategorii")
                k_opis = st.text_area("Opis")
                if st.form_submit_button("Zapisz kategorię"):
                    supabase.table("kategorie").insert({"Nazwa": k_nazwa, "Opis": k_opis}).execute()
                    st.success("Kategoria dodana!")
                    st.rerun()

        with tab_p:
            res_k = supabase.table("kategorie").select("id, Nazwa").execute()
            kat_dict = {item['Nazwa']: item['id'] for item in res_k.data} if res_k.data else {}
            
            with st.form("form_prod", clear_on_submit=True):
                c1, c2 = st.columns(2)
                p_nazwa = c1.text_input("Nazwa produktu")
                p_kat = c2.selectbox("Kategoria", options=list(kat_dict.keys()))
                
                c3, c4 = st.columns(2)
                p_cena = c3.number_input("Cena (PLN)", min_value=0, step=1)
                p_liczba = c4.number_input("Początkowa liczba sztuk", min_value=0, step=1)
                
                if st.form_submit_button("🚀 Dodaj produkt do systemu"):
                    if p_nazwa and kat_dict:
                        new_data = {
                            "nazwa": p_nazwa,
                            "cena": int(p_cena),
                            "liczba": int(p_liczba),
                            "kategoria_id": kat_dict[p_kat]
                        }
                        supabase.table("produkty").insert(new_data).execute()
                        st.balloons()
                        st.success("Produkt został pomyślnie wprowadzony!")
                    else:
                        st.warning("Uzupełnij dane.")

if __name__ == "__main__":
    main()
