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
    # Konfiguracja strony
    st.set_page_config(page_title="Magazyn U Sąsiada", layout="wide", page_icon="🏪")
    
    # --- CUSTOM STYLING (FANCY LOOK) ---
    st.markdown("""
        <style>
        /* Styl dla całego tła */
        .main { background-color: #f8f9fa; }
        
        /* Stylizacja nagłówka */
        .main-title {
            color: #1E3A8A;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-weight: bold;
            text-align: center;
            padding: 20px;
            background: white;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        
        /* Stylizacja kart metryk */
        div[data-testid="stMetricValue"] { font-size: 24px; color: #1E3A8A; }
        div[data-testid="metric-container"] {
            background-color: white;
            padding: 15px;
            border-radius: 12px;
            border-left: 5px solid #1E3A8A;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        </style>
    """, unsafe_allow_html=True)

    if not supabase:
        st.stop()

    # --- 2. ROZBUDOWANY PASEK BOCZNY ---
    with st.sidebar:
        st.markdown("<h1 style='text-align: center;'>🏪</h1>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center;'>U Sąsiada</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray;'>System Zarządzania Magazynem</p>", unsafe_allow_html=True)
        st.divider()
        
        menu = ["📊 Panel Analityczny", "🛒 Spis Produktów", "📂 Kategorie", "➕ Zarządzanie Bzą"]
        choice = st.selectbox("Wybierz moduł:", menu)
        
        st.divider()
        # Dodatki w pasku bocznym
        st.subheader("Status Systemu")
        st.success("✅ Serwer: Połączono")
        st.info(f"🕒 Sesja: {datetime.now().strftime('%H:%M:%S')}")
        
        with st.expander("ℹ️ Pomoc i Wsparcie"):
            st.write("W razie problemów skontaktuj się z administratorem sieci.")
            st.write("Wersja: 2.1.0-stable")

    # Nagłówek główny
    st.markdown("<div class='main-title'>🏪 System Zarządzania Magazynem Sklepu Osiedlowego 'U SĄSIADA'</div>", unsafe_allow_html=True)

    # --- 3. MODUŁY ---
    if choice == "📊 Panel Analityczny":
        try:
            res = supabase.table("produkty").select("*").execute()
            if res.data:
                df = pd.DataFrame(res.data)
                
                # Metryki
                c1, c2, c3, c4 = st.columns(4)
                total_val = (df['cena'] * df['liczba']).sum()
                c1.metric("Wartość towaru", f"{total_val:,.2f} zł")
                c2.metric("Suma sztuk", f"{int(df['liczba'].sum())}")
                c3.metric("Rodzaje towarów", len(df))
                
                low_stock = df[df['liczba'] < 5]
                c4.metric("Braki ( <5 )", len(low_stock), delta_color="inverse")

                st.divider()
                
                col_left, col_right = st.columns([2, 1])
                with col_left:
                    st.subheader("📈 Wykres Stanów")
                    st.bar_chart(df.set_index("nazwa")["liczba"])
                
                with col_right:
                    st.subheader("⚠️ Raport Braków")
                    if not low_stock.empty:
                        st.error("Uzupełnij te produkty!")
                        st.dataframe(low_stock[['nazwa', 'liczba']], hide_index=True)
                    else:
                        st.success("Wszystkie stany OK!")

                st.divider()
                st.subheader("📥 Eksport Raportu")
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("Pobierz raport do Excela (CSV)", csv, "raport_sklep.csv", "text/csv")
            else:
                st.info("Brak danych w systemie.")
        except Exception as e:
            st.error(f"Błąd dashboardu: {e}")

    elif choice == "🛒 Spis Produktów":
        st.subheader("🛒 Aktualna Lista Produktów")
        try:
            res = supabase.table("produkty").select("*").execute()
            # Używamy st.dataframe z dodatkowymi parametrami stylizacji
            st.dataframe(
                res.data, 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "cena": st.column_config.NumberColumn("Cena (zł)", format="%.2f PLN"),
                    "liczba": st.column_config.ProgressColumn("Stan Magazynowy", min_value=0, max_value=100)
                }
            )
        except Exception as e:
            st.error(f"Błąd: {e}")

    elif choice == "📂 Kategorie":
        st.subheader("📂 Zdefiniowane Kategorie Towarów")
        res = supabase.table("kategorie").select("*").execute()
        st.table(res.data)

    elif choice == "➕ Zarządzanie Bzą":
        t1, t2 = st.tabs(["Dodaj Produkt", "Dodaj Kategorię"])
        
        with t2:
            with st.form("f_kat"):
                n_kat = st.text_input("Nazwa nowej kategorii")
                o_kat = st.text_area("Opis")
                if st.form_submit_button("Zatwierdź kategorię"):
                    supabase.table("kategorie").insert({"Nazwa": n_kat, "Opis": o_kat}).execute()
                    st.success("Kategoria została utworzona!")
                    st.rerun()

        with t1:
            res_k = supabase.table("kategorie").select("id, Nazwa").execute()
            kat_dict = {item['Nazwa']: item['id'] for item in res_k.data} if res_k.data else {}
            
            with st.form("f_prod"):
                c1, c2 = st.columns(2)
                p_nazwa = c1.text_input("Nazwa towaru")
                p_kat = c2.selectbox("Kategoria", options=list(kat_dict.keys()))
                
                c3, c4 = st.columns(2)
                p_cena = c3.number_input("Cena zakupu", min_value=0, step=1)
                p_liczba = c4.number_input("Ilość dostarczona", min_value=0, step=1)
                
                if st.form_submit_button("✅ Zaksięguj Produkt"):
                    if p_nazwa:
                        new_data = {
                            "nazwa": p_nazwa,
                            "cena": int(p_cena),
                            "liczba": int(p_liczba),
                            "kategoria_id": kat_dict[p_kat]
                        }
                        supabase.table("produkty").insert(new_data).execute()
                        st.balloons()
                        st.success(f"Produkt {p_nazwa} został dodany do bazy!")
                    else:
                        st.error("Błąd: Nazwa produktu nie może być pusta!")

if __name__ == "__main__":
    main()
