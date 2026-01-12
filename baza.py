import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

# --- 1. POŁĄCZENIE Z BAZĄ ---
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
    st.set_page_config(page_title="Lokalny Sklepik - Magazyn", layout="wide", page_icon="🛍️")
    
    # --- DESIGN CSS ---
    st.markdown("""
        <style>
        .main { background-color: #f0f2f6; }
        .stMetric { background-color: #ffffff; border-radius: 10px; padding: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        .header-box { background: linear-gradient(90deg, #2E7D32 0%, #4CAF50 100%); color: white; padding: 1.5rem; border-radius: 15px; text-align: center; margin-bottom: 2rem; }
        </style>
    """, unsafe_allow_html=True)

    if not supabase:
        st.stop()

    # --- BOCZNY PANEL ---
    with st.sidebar:
        st.markdown("<h1 style='text-align: center;'>🛍️</h1>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center;'>Lokalny Sklepik</h2>", unsafe_allow_html=True)
        st.divider()
        menu = ["📈 Panel Analityczny", "📋 Stan Magazynu", "📂 Kategorie", "⚙️ Zarządzanie"]
        choice = st.selectbox("Nawigacja:", menu)
        st.divider()
        st.info(f"Aktualizacja: {datetime.now().strftime('%H:%M')}")

    st.markdown(f"<div class='header-box'><h1 style='margin:0;'>🛍️ LOKALNY SKLEPIK</h1><p style='margin:0; opacity: 0.9;'>Ewidencja Towarów i Przyjęcia Dostaw</p></div>", unsafe_allow_html=True)

    # --- MODUŁY ---
    if choice == "📈 Panel Analityczny":
        try:
            res = supabase.table("produkty").select("*").execute()
            if res.data:
                df = pd.DataFrame(res.data)
                m1, m2, m3, m4 = st.columns(4)
                total_val = (df['cena'] * df['liczba']).sum()
                low_stock = df[df['liczba'] < 5]
                m1.metric("Wartość towaru", f"{total_val:,.2f} zł")
                m2.metric("Suma jednostek", f"{int(df['liczba'].sum())} szt.")
                m3.metric("Liczba produktów", len(df))
                m4.metric("Braki ( < 5szt )", len(low_stock), delta="- Do zamówienia" if len(low_stock) > 0 else "OK")
                st.divider()
                col_chart, col_low = st.columns([2, 1])
                with col_chart:
                    st.write("### 📦 Dostępność produktów")
                    st.bar_chart(df.set_index("nazwa")["liczba"])
                with col_low:
                    st.write("### ⚠️ Alarmy braków")
                    if not low_stock.empty:
                        st.dataframe(low_stock[['nazwa', 'liczba']], use_container_width=True, hide_index=True)
                    else:
                        st.success("Stany w normie.")
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Pobierz Pełny Raport CSV", csv, f"raport_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
        except Exception as e:
            st.error(f"Błąd ładowania: {e}")

    elif choice == "📋 Stan Magazynu":
        st.subheader("📋 Aktualna lista produktów")
        res = supabase.table("produkty").select("*").execute()
        st.dataframe(res.data, use_container_width=True, hide_index=True, column_config={
            "nazwa": "Nazwa Produktu", "cena": st.column_config.NumberColumn("Cena", format="%d zł"),
            "liczba": st.column_config.ProgressColumn("Ilość", min_value=0, max_value=100)
        })

    elif choice == "📂 Kategorie":
        st.subheader("📂 Kategorie")
        res = supabase.table("kategorie").select("*").execute()
        st.table(res.data)

    elif choice == "⚙️ Zarządzanie":
        st.subheader("⚙️ Operacje Magazynowe")
        t_dostawa, t_prod, t_kat = st.tabs(["🚚 Przyjmij Dostawę", "➕ Nowy Produkt", "📁 Nowa Kategoria"])
        
        # --- NOWA FUNKCJA: DOSTAWA ---
        with t_dostawa:
            st.markdown("### Zwiększ stan magazynowy")
            res_p = supabase.table("produkty").select("id, nazwa, liczba").execute()
            if res_p.data:
                prod_list = {item['nazwa']: (item['id'], item['liczba']) for item in res_p.data}
                with st.form("form_dostawa", clear_on_submit=True):
                    wybrany_p = st.selectbox("Wybierz produkt z dostawy", options=list(prod_list.keys()))
                    ilosc_nowa = st.number_input("Ile sztuk dowieziono?", min_value=1, step=1)
                    
                    if st.form_submit_button("Zaksięguj dostawę"):
                        p_id, stara_liczba = prod_list[wybrany_p]
                        nowa_suma = stara_liczba + ilosc_nowa
                        try:
                            supabase.table("produkty").update({"liczba": nowa_suma}).eq("id", p_id).execute()
                            st.success(f"🚚 Dostawa przyjęta! Obecny stan {wybrany_p}: {nowa_suma} szt.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Błąd dostawy: {e}")
            else:
                st.warning("Brak produktów w bazie.")

        with t_kat:
            with st.form("f_kat"):
                kn, ko = st.text_input("Nazwa kategorii"), st.text_area("Opis")
                if st.form_submit_button("Dodaj kategorię"):
                    supabase.table("kategorie").insert({"Nazwa": kn, "Opis": ko}).execute()
                    st.success("Dodano!")
                    st.rerun()

        with t_prod:
            res_k = supabase.table("kategorie").select("id, Nazwa").execute()
            kat_map = {item['Nazwa']: item['id'] for item in res_k.data} if res_k.data else {}
            with st.form("f_prod"):
                c1, c2 = st.columns(2)
                p_n, p_k = c1.text_input("Nazwa produktu"), c2.selectbox("Kategoria", options=list(kat_map.keys()))
                c3, c4 = st.columns(2)
                p_c, p_l = c3.number_input("Cena", min_value=0, step=1), c4.number_input("Liczba", min_value=0, step=1)
                if st.form_submit_button("Dodaj produkt"):
                    if p_n and kat_map:
                        supabase.table("produkty").insert({"nazwa": p_n, "cena": int(p_c), "liczba": int(p_l), "kategoria_id": kat_map[p_k]}).execute()
                        st.balloons()
                        st.success("Dodano!")
                        st.rerun()

if __name__ == "__main__":
    main()
