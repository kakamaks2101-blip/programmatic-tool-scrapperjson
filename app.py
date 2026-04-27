import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Programmatic Scraper", layout="wide")

st.title("🚀 Programmatic Sellers.json Expert")
st.write("Вставте URL та ключові слова (через кому або рядок).")

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
url_input = st.text_input("Вставте URL", "https://admixer.com/sellers.json")
keywords_area = st.text_area("Ключові слова (назви або домени)", help="Можна вводити по одному в рядок або через кому")

if st.button("Обробити файл"):
    if url_input:
        with st.spinner('Магія парсингу...'):
            df = fetch_data(url_input)
            
            if df is not None and not df.empty:
                # Виправляємо помилку Attribute Error (додаємо .str)
                df['name'] = df['name'].fillna('').astype(str)
                df['domain'] = df['domain'].fillna('').astype(str)
                df['seller_type'] = df['seller_type'].fillna('').astype(str).str.upper()
                
                # Пошук за декількома ключами
                if keywords_area:
                    # Розбиваємо введені дані на список чистих ключів
                    search_keys = [k.strip().lower() for k in keywords_area.replace(',', '\n').split('\n') if k.strip()]
                    
                    if search_keys:
                        # Створюємо поле для пошуку
                        search_content = df['name'].str.lower() + " " + df['domain'].str.lower()
                        # Фільтруємо: хоча б один ключ має бути в рядку
                        pattern = '|'.join(search_keys)
                        df = df[search_content.str.contains(pattern, na=False)]
                
                # Розділяємо на типи
                pubs = df[df['seller_type'] == 'PUBLISHER']
                ints = df[df['seller_type'] == 'INTERMEDIARY']
                
                st.success(f"Знайдено: {len(pubs)} паблішерів та {len(ints)} посередників.")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📁 Direct Publishers")
                    st.dataframe(pubs[['seller_id', 'name', 'domain']].head(100), use_container_width=True)
                    if not pubs.empty:
                        csv_p = pubs[['seller_id', 'name', 'domain']].to_csv(index=False).encode('utf-8')
                        st.download_button("Завантажити PUBLISHERS.csv", csv_p, "publishers.csv", "text/csv")
                
                with col2:
                    st.subheader("📂 Intermediaries")
                    st.dataframe(ints[['seller_id', 'name', 'domain']].head(100), use_container_width=True)
                    if not ints.empty:
                        csv_i = ints[['seller_id', 'name', 'domain']].to_csv(index=False).encode('utf-8')
                        st.download_button("Завантажити INTERMEDIARIES.csv", csv_i, "intermediaries.csv", "text/csv")
            elif df is not None and df.empty:
                st.warning("Файл порожній або не містить селлерів.")
    else:
        st.warning("Будь ласка, вкажіть URL.")
