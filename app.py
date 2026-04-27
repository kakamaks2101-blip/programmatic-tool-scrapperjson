import streamlit as st
import pandas as pd
import requests
import concurrent.futures

st.set_page_config(page_title="Programmatic Bulk Tool", layout="wide")

st.title("🚀 Multi-SSP Sellers.json Scraper")
st.write("Введіть список URL та ключові слова. Скрипт перевірить всі SSP одночасно.")

# Функція для паралельного завантаження
def fetch_one_ssp(url):
    try:
        response = requests.get(url.strip(), timeout=10)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data.get('sellers', []))
        df['ssp_source'] = url.strip() # Додаємо назву джерела
        return df
    except:
        return pd.DataFrame()

# --- UI Side ---
with st.sidebar:
    st.header("Налаштування")
    ssp_urls_input = st.text_area(
        "Список URL sellers.json (по одному в рядок)", 
        "https://openx.com/sellers.json\nhttps://www.rubiconproject.com/sellers.json"
    )
    keywords_input = st.text_area("Ключові слова (назви/домени)", "Mail\nWeather\nCNN")

if st.button("🔥 Запустити масовий пошук"):
    urls = [u.strip() for u in ssp_urls_input.split('\n') if u.strip()]
    keywords = [k.strip().lower() for k in keywords_input.split('\n') if k.strip()]
    
    if urls and keywords:
        with st.spinner(f'Скануємо {len(urls)} SSP...'):
            # Використовуємо паралельні запити для швидкості
            with concurrent.futures.ThreadPoolExecutor() as executor:
                results_list = list(executor.map(fetch_one_ssp, urls))
            
            all_data = pd.concat(results_list, ignore_index=True)
            
            if not all_data.empty:
                # Пошук
                all_data['search_field'] = all_data['name'].astype(str).str.lower() + " " + all_data['domain'].astype(str).str.lower()
                pattern = '|'.join(keywords)
                filtered = all_data[all_data['search_field'].str.contains(pattern, na=False)].copy()
                
                if not filtered.empty:
                    st.success(f"Знайдено {len(filtered)} збігів у всіх джерелах!")
                    
                    # Вивід таблиці
                    st.dataframe(filtered[['seller_id', 'name', 'domain', 'seller_type', 'ssp_source']], use_container_width=True)
                    
                    # Кнопки скачування
                    col1, col2 = st.columns(2)
                    with col1:
                        pub_only = filtered[filtered['seller_type'].str.upper() == 'PUBLISHER']
                        st.download_button("Download PUBLISHERS (CSV)", pub_only.to_csv(index=False).encode('utf-8'), "publishers.csv")
                    with col2:
                        st.download_button("Download ALL (CSV)", filtered.to_csv(index=False).encode('utf-8'), "all_sellers.csv")
                else:
                    st.warning("Нічого не знайдено.")
    else:
        st.error("Додайте посилання та ключові слова.")