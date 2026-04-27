import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Programmatic Scraper", layout="wide")

st.title("🚀 Programmatic Sellers.json Expert")
st.write("Вставте URL, щоб розділити файл на Direct Publishers та Intermediaries.")

@st.cache_data(ttl=3600)
def fetch_data(url):
    try:
        response = requests.get(url.strip(), timeout=20)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data.get('sellers', []))
        return df
    except Exception as e:
        st.error(f"Помилка завантаження: {e}")
        return None

# --- UI ---
url_input = st.text_input("Вставте URL (наприклад, https://admixer.com/sellers.json)")
keyword_search = st.text_input("Пошук по ключу (залиште порожнім, щоб завантажити все)")

if st.button("Обробити файл"):
    if url_input:
        with st.spinner('Магія парсингу...'):
            df = fetch_data(url_input)
            
            if df is not None:
                # Якщо введено ключове слово — фільтруємо
                if keyword_search:
                    df['search'] = df['name'].astype(str).lower() + " " + df['domain'].astype(str).lower()
                    df = df[df['search'].str.contains(keyword_search.lower(), na=False)]
                
                # Розділяємо на два типи
                pubs = df[df['seller_type'].str.upper() == 'PUBLISHER']
                ints = df[df['seller_type'].str.upper() == 'INTERMEDIARY']
                
                st.success(f"Готово! Знайдено {len(pubs)} паблішерів та {len(ints)} посередників.")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📁 Direct Publishers")
                    st.dataframe(pubs[['seller_id', 'name', 'domain']].head(100)) # Прев'ю
                    csv_p = pubs[['seller_id', 'name', 'domain']].to_csv(index=False).encode('utf-8')
                    st.download_button("Завантажити PUBLISHERS.csv", csv_p, "publishers.csv", "text/csv")
                
                with col2:
                    st.subheader("📂 Intermediaries")
                    st.dataframe(ints[['seller_id', 'name', 'domain']].head(100)) # Прев'ю
                    csv_i = ints[['seller_id', 'name', 'domain']].to_csv(index=False).encode('utf-8')
                    st.download_button("Завантажити INTERMEDIARIES.csv", csv_i, "intermediaries.csv", "text/csv")
    else:
        st.warning("Будь ласка, вкажіть URL.")
