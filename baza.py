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
    # Konfiguracja okna przeglądarki
    st.set_page_config(page_title="Lokalny Sklepik - Magazyn", layout="wide", page_icon="🛍️")
    
    # --- ZAAWANSOWANY DESIGN (CSS) ---
    st.markdown("""
        <style>
        .main { background-color: #f0f2f6; }
        .stMetric { 
            background-color: #ffffff; 
            border-radius: 10px; 
            padding: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }
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

    # --- BOCZNY PANEL NAWIGACYJNY ---
    with st.sidebar:
        st.markdown("<h1 style='text-align: center;'>🛍️</h1>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center;'>Lokalny Sklepik</h2>", unsafe_allow_html=True)
        st.divider()
        
        menu = ["📈 Panel Analityczny", "📋 Stan Magazynu", "📂 Kategorie", "⚙️ Zarządzanie"]
        choice = st.selectbox("Nawigacja:", menu)
        
        st.divider()
        st.markdown("### 🟢 Status Systemu")
        st.info(f"Ostatnia aktualizacja: {datetime.now().strftime('%H:%M')}")
        st.caption("System Zarządzania v3.0")

    # --- NAGŁÓWEK GŁÓWNY ---
    st.markdown(f"""
        <div class='header-box'>
            <h1 style='margin:0;'>🛍️ LOKALNY SKLEPIK</h1>
            <p style='margin:0; opacity: 0.9;'>System Ewidencji Towarów i Raportowania</p>
        </div>
    """, unsafe_allow_html=True)

    # --- MODUŁY ---
    
    if choice == "📈 Panel Analityczny":
        st.subheader("📊 Statystyki Sprzedażowe i Zapasy")
        try:
            res = supabase.table("produkty").select("*").execute()
            if res.data:
                df = pd.DataFrame(res.data)
                
                # Metryki KPI
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
                        st.success("Wszystkie stany w normie.")

                # Eksport danych
                st.divider()
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Pobierz Pełny Raport CSV",
                    data=csv,
                    file_name=f"raport_lokalny_sklepik_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime='text/csv',
                )
        except Exception as e:
            st.error(f"Błąd ładowania: {e}")

    elif choice == "📋 Stan Magazynu":
        st.subheader("📋 Aktualna lista produktów")
        try:
            res = supabase.table("produkty").select("*").execute()
            st.dataframe(
                res.data, 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "nazwa": "Nazwa Produktu",
                    "cena": st.column_config.NumberColumn("Cena (PLN)", format="%d zł"),
                    "liczba": st.column_config.ProgressColumn("Ilość", min_value=0, max_value=100),
                    "kategoria_id": "Kategoria (ID)"
                }
            )
        except Exception as e:
            st.error(f"Błąd: {e}")

    elif choice == "📂 Kategorie":
        st.subheader("📂 Dostępne Kategorie")
        try:
            res = supabase.table("kategorie").select("*").execute()
            st.table(res.data)
        except Exception as e:
            st.error(f"Błąd: {e}")

    elif choice == "⚙️ Zarządzanie":
        st.subheader("⚙️ Panel Administracyjny")
        t_prod, t_kat = st.tabs(["➕ Dodaj Produkt", "📁 Dodaj Kategorię"])
        
        with t_kat:
            with st.form("f_kat"):
                # Używamy wielkich liter zgodnie z Twoją strukturą bazy dla kategorii
                kn = st.text_input("Nazwa kategorii")
                ko = st.text_area("Opis")
                if st.form_submit_button("Dodaj kategorię"):
                    supabase.table("kategorie").insert({"Nazwa": kn, "Opis": ko}).execute()
                    st.success("Kategoria dodana!")
                    st.rerun()

        with t_prod:
            res_k = supabase.table("kategorie").select("id, Nazwa").execute()
            kat_map = {item['Nazwa']: item['id'] for item in res_k.data} if res_k.data else {}
            
            with st.form("f_prod"):
                f1, f2 = st.columns(2)
                p_n = f1.text_input("Nazwa produktu")
                p_k = f2.selectbox("Kategoria", options=list(kat_map.keys()))
                
                f3, f4 = st.columns(2)
                p_c = f3.number_input("Cena (zł)", min_value=0, step=1)
                p_l = f4.number_input("Liczba sztuk", min_value=0, step=1)
                
                if st.form_submit_button("Dodaj produkt"):
                    if p_n and kat_map:
                        # Produkty - małe litery, Kategorie - wielkie litery
                        data = {
                            "nazwa": p_n,
                            "cena": int(p_c),
                            "liczba": int(p_l),
                            "kategoria_id": kat_map[p_k]
                        }
                        supabase.table("produkty").insert(data).execute()
                        st.balloons()
                        st.success(f"Dodano produkt: {p_n}")
                        st.rerun()

if __name__ == "__main__":
    main()
