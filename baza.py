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
        st.error(f"❌ Krytyczny błąd połączenia: {e}")
        return None

supabase = init_connection()

def main():
    # Konfiguracja strony
    st.set_page_config(page_title="Lokalny Sklepik - Magazyn", layout="wide", page_icon="🛍️")
    
    # --- DESIGN CSS (JEDNOLITE TŁO, BRAK RAMEK) ---
    st.markdown("""
        <style>
        /* Tło aplikacji i metryk */
        .stApp, .main, div[data-testid="metric-container"] {
            background-color: #f0f2f6 !important;
        }
        /* Usunięcie obramowań i cieni z metryk */
        div[data-testid="metric-container"] {
            border: none !important;
            box-shadow: none !important;
        }
        /* Nagłówek główny */
        .header-box {
            background: linear-gradient(90deg, #2E7D32 0%, #4CAF50 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 15px;
            text-align: center;
            margin-bottom: 2rem;
        }
        </style>
    """, unsafe_allow_html=True)

    if not supabase:
        st.stop()

    # --- 2. PASEK BOCZNY ---
    with st.sidebar:
        st.markdown("<h1 style='text-align: center;'>🛍️</h1>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center;'>Lokalny Sklepik</h2>", unsafe_allow_html=True)
        st.divider()
        menu = ["📈 Panel Analityczny", "📋 Stan Magazynu", "📂 Kategorie", "⚙️ Zarządzanie"]
        choice = st.selectbox("Nawigacja:", menu)
        st.divider()
        st.info(f"Aktualizacja: {datetime.now().strftime('%H:%M')}")
        st.caption("System Zarządzania v4.0")

    # Nagłówek na stronie głównej
    st.markdown(f"<div class='header-box'><h1 style='margin:0;'>🛍️ LOKALNY SKLEPIK</h1><p style='margin:0; opacity: 0.9;'>Ewidencja Towarów i Zarządzanie Dostawami</p></div>", unsafe_allow_html=True)

    # --- 3. MODUŁY ---

    # --- MODUŁ: PANEL ANALITYCZNY ---
    if choice == "📈 Panel Analityczny":
        try:
            res_p = supabase.table("produkty").select("*").execute()
            res_k = supabase.table("kategorie").select("*").execute()
            
            if res_p.data:
                df = pd.DataFrame(res_p.data)
                df['wartosc_total'] = df['cena'] * df['liczba']
                
                # METRYKI
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Wartość towaru", f"{df['wartosc_total'].sum():,.2f} zł")
                m2.metric("Suma jednostek", f"{int(df['liczba'].sum())} szt.")
                m3.metric("Liczba pozycji", len(df))
                
                low_stock = df[df['liczba'] < 5]
                m4.metric("Krytyczne braki", len(low_stock), delta="- Uzupełnij!" if len(low_stock) > 0 else "OK")

                st.divider()

                # WYKRESY
                c1, c2 = st.columns(2)
                with c1:
                    st.write("### 📦 Ilość sztuk produktów")
                    st.bar_chart(df.set_index("nazwa")["liczba"])
                
                with c2:
                    st.write("### 📊 Udział wartościowy (PLN)")
                    st.area_chart(df.set_index("nazwa")["wartosc_total"])

                st.divider()
                st.write("### 📊 Dodatkowe statystyki")
                col_a, col_b = st.columns([2, 1])
                with col_a:
                    if res_k.data:
                        df_kat = pd.DataFrame(res_k.data)
                        df_merged = df.merge(df_kat, left_on='kategoria_id', right_on='id')
                        st.write("**Liczba produktów w kategoriach:**")
                        st.line_chart(df_merged['Nazwa'].value_counts())
                
                with col_b:
                    st.info("💡 **Najcenniejszy towar:**")
                    top_prod = df.sort_values(by='wartosc_total', ascending=False).iloc[0]
                    st.write(f"**{top_prod['nazwa']}**")
                    st.write(f"Łączna wartość: {top_prod['wartosc_total']:.2f} zł")

                st.divider()
                st.write("### ⚠️ Raport krytyczny (Braki)")
                if not low_stock.empty:
                    st.dataframe(low_stock[['nazwa', 'liczba']], use_container_width=True, hide_index=True)
                else:
                    st.success("Wszystkie stany magazynowe są w normie!")
            else:
                st.warning("Baza danych jest pusta. Dodaj produkty w zakładce Zarządzanie.")
        except Exception as e:
            st.error(f"Błąd analizy: {e}")

    # --- MODUŁ: STAN MAGAZYNU ---
    elif choice == "📋 Stan Magazynu":
        st.subheader("📋 Aktualna lista produktów")
        try:
            res = supabase.table("produkty").select("*").execute()
            # hide_index=True usuwa szarą kolumnę z lewej
            st.dataframe(res.data, use_container_width=True, hide_index=True, column_config={
                "id": "ID",
                "nazwa": "Nazwa Produktu", 
                "cena": st.column_config.NumberColumn("Cena (zł)", format="%d zł"),
                "liczba": st.column_config.ProgressColumn("Ilość w magazynie", min_value=0, max_value=100),
                "kategoria_id": "Kategoria ID"
            })
        except Exception as e:
            st.error(f"Błąd: {e}")

    # --- MODUŁ: KATEGORIE ---
    elif choice == "📂 Kategorie":
        st.subheader("📂 Kategorie Towarów")
        try:
            res = supabase.table("kategorie").select("*").execute()
            # hide_index=True usuwa szarą kolumnę z lewej
            st.dataframe(res.data, use_container_width=True, hide_index=True, column_config={
                "id": "ID Kategorii",
                "Nazwa": "Nazwa Sekcji",
                "Opis": "Opis asortymentu"
            })
        except Exception as e:
            st.error(f"Błąd: {e}")

    # --- MODUŁ: ZARZĄDZANIE ---
    elif choice == "⚙️ Zarządzanie":
        st.subheader("⚙️ Operacje Magazynowe")
        t_dostawa, t_prod, t_kat = st.tabs(["🚚 Przyjmij Dostawę", "➕ Nowy Produkt", "📁 Nowa Kategoria"])
        
        # Przyjęcie dostawy
        with t_dostawa:
            res_p = supabase.table("produkty").select("id, nazwa, liczba").execute()
            if res_p.data:
                prod_list = {item['nazwa']: (item['id'], item['liczba']) for item in res_p.data}
                with st.form("form_dostawa", clear_on_submit=True):
                    wybrany_p = st.selectbox("Wybierz produkt z dostawy", options=list(prod_list.keys()))
                    ilosc_nowa = st.number_input("Ile sztuk dowieziono?", min_value=1, step=1)
                    if st.form_submit_button("Zaksięguj dostawę"):
                        p_id, stara_liczba = prod_list[wybrany_p]
                        supabase.table("produkty").update({"liczba": stara_liczba + ilosc_nowa}).eq("id", p_id).execute()
                        st.success(f"🚚 Zaktualizowano stan dla: {wybrany_p}")
                        st.rerun()

        # Dodawanie nowej kategorii
        with t_kat:
            with st.form("f_kat"):
                kn = st.text_input("Nazwa (np. Nabiał, Pieczywo)")
                ko = st.text_area("Opis (np. Sery, jogurty, mleka lub Świeże bułki i chleby)")
                if st.form_submit_button("Dodaj kategorię"):
                    if kn:
                        supabase.table("kategorie").insert({"Nazwa": kn, "Opis": ko}).execute()
                        st.success("Kategoria dodana!")
                        st.rerun()

        # Dodawanie nowego produktu
        with t_prod:
            res_k = supabase.table("kategorie").select("id, Nazwa").execute()
            kat_map = {item['Nazwa']: item['id'] for item in res_k.data} if res_k.data else {}
            with st.form("f_prod"):
                c1, c2 = st.columns(2)
                p_n = c1.text_input("Nazwa produktu")
                p_k = c2.selectbox("Wybierz kategorię", options=list(kat_map.keys()))
                c3, c4 = st.columns(2)
                p_c = c3.number_input("Cena jednostkowa", min_value=0, step=1)
                p_l = c4.number_input("Ilość początkowa", min_value=0, step=1)
                
                if st.form_submit_button("Zapisz produkt"):
                    if p_n and kat_map:
                        supabase.table("produkty").insert({
                            "nazwa": p_n, 
                            "cena": int(p_c), 
                            "liczba": int(p_l), 
                            "kategoria_id": kat_map[p_k]
                        }).execute()
                        st.balloons()
                        st.success(f"Dodano: {p_n}")
                        st.rerun()

if __name__ == "__main__":
    main()
