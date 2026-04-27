import streamlit as st
import pandas as pd
import requests
import concurrent.futures

st.set_page_config(page_title="Programmatic Pro Tool", layout="wide")

st.title("🚀 Multi-SSP Professional Scraper")
st.write("Масовий пошук та фільтрація по декількох sellers.json.")

# Функція для завантаження одного SSP
def fetch_one_ssp(url):
    url = url.strip()
    if not url:
        return pd.DataFrame()
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        sellers = data.get('sellers', [])
        if not sellers:
            return pd.DataFrame()
        
        df = pd.DataFrame(sellers)
        # Додаємо джерело, щоб розуміти звідки дані
        df['ssp_source'] = url.replace('https://', '').replace('/sellers.json', '')
        return df
    except Exception as e:
        # У разі помилки одного лінка, просто ігноруємо його, щоб не зупиняти весь процес
        return pd.DataFrame()

# --- ПАНЕЛЬ НАЛАШТУВАНЬ (Sidebar) ---
with st.sidebar:
    st.header("Вхідні дані")
    urls_input = st.text_area("Список URL sellers.json (по одному в рядок)", 
                              placeholder="https://admixer.com/sellers.json\nhttps://openx.com/sellers.json")
    
    keywords_input = st.text_area("Ключові слова для пошуку", 
                                  placeholder="Amagi, Google, News",
                                  help="Можна через кому або з нового рядка. Залиште порожнім для повного дампу.")

# --- ОСНОВНА ЛОГІКА ---
if st.button("🔥 Запустити масову обробку"):
    urls = [u.strip() for u in urls_input.split('\n') if u.strip()]
    
    if not urls:
        st.warning("Будь ласка, додайте хоча б одне посилання.")
    else:
        with st.spinner(f'Обробляємо {len(urls)} джерел...'):
            # Паралельне завантаження для швидкості
            with concurrent.futures.ThreadPoolExecutor() as executor:
                results_list = list(executor.map(fetch_one_ssp, urls))
            
            # Об'єднуємо всі результати в одну велику таблицю
            if any(not d.empty for d in results_list):
                all_data = pd.concat(results_list, ignore_index=True)
                
                # Очистка та нормалізація даних
                for col in ['name', 'domain', 'seller_type', 'seller_id']:
                    if col in all_data.columns:
                        all_data[col] = all_data[col].fillna('').astype(str)
                
                # Фільтрація за ключами, якщо вони є
                if keywords_input:
                    keys = [k.strip().lower() for k in keywords_input.replace(',', '\n').split('\n') if k.strip()]
                    if keys:
                        search_content = all_data['name'].str.lower() + " " + all_data['domain'].str.lower()
                        pattern = '|'.join(keys)
                        all_data = all_data[search_content.str.contains(pattern, na=False)]

                if not all_data.empty:
                    st.success(f"Знайдено всього записів: {len(all_data)}")
                    
                    # Розподіл на Direct та Intermediary
                    pubs = all_data[all_data['seller_type'].str.upper() == 'PUBLISHER']
                    ints = all_data[all_data['seller_type'].str.upper() == 'INTERMEDIARY']
                    
                    # Вивід результатів
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("📁 Direct Publishers")
                        st.write(f"Знайдено: {len(pubs)}")
                        st.dataframe(pubs[['seller_id', 'name', 'domain', 'ssp_source']].head(100), use_container_width=True)
                        if not pubs.empty:
                            csv_p = pubs.to_csv(index=False).encode('utf-8')
                            st.download_button("Завантажити PUBLISHERS.csv", csv_p, "publishers.csv", "text/csv")
                    
                    with col2:
                        st.subheader("📂 Intermediaries")
                        st.write(f"Знайдено: {len(ints)}")
                        st.dataframe(ints[['seller_id', 'name', 'domain', 'ssp_source']].head(100), use_container_width=True)
                        if not ints.empty:
                            csv_i = ints.to_csv(index=False).encode('utf-8')
                            st.download_button("Завантажити INTERMEDIARIES.csv", csv_i, "intermediaries.csv", "text/csv")
                else:
                    st.info("Нічого не знайдено за вашими ключами.")
            else:
                st.error("Не вдалося отримати дані з вказаних посилань.")
