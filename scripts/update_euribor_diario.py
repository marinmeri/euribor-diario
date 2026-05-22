import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
from datetime import datetime

CSV_PATH = "euribor_diario_2026.csv"

TENORES = {
    '1m':  'https://www.euribor-rates.eu/en/current-euribor-rates/1/euribor-rate-1-month/',
    '3m':  'https://www.euribor-rates.eu/en/current-euribor-rates/2/euribor-rate-3-months/',
    '6m':  'https://www.euribor-rates.eu/en/current-euribor-rates/3/euribor-rate-6-months/',
    '12m': 'https://www.euribor-rates.eu/en/current-euribor-rates/4/euribor-rate-12-months/',
}

def scrape_tenor(url):
    r = requests.get(url, timeout=20, headers={'User-Agent': 'Mozilla/5.0'})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')
    rows = []
    tables = soup.find_all('table')
    for table in tables:
        for tr in table.find_all('tr')[1:]:
            cols = [td.get_text(strip=True) for td in tr.find_all('td')]
            if len(cols) >= 2:
                try:
                    date_str = cols[0].strip()
                    rate_str = cols[1].replace('%','').replace(',','.').strip()
                    dt = datetime.strptime(date_str, '%m/%d/%Y').strftime('%Y-%m-%d')
                    rate = float(rate_str)
                    rows.append({'date': dt, 'rate': rate})
                except:
                    continue
        if rows:
            break
    return pd.DataFrame(rows)

def main():
    if os.path.exists(CSV_PATH):
        existing = pd.read_csv(CSV_PATH)
        existing['date'] = existing['date'].astype(str)
        print(f"CSV existente: {len(existing)} filas | Ultimo: {existing['date'].max()}")
    else:
        existing = None
        print("Primer run, creando CSV...")

    dfs = {}
    for tenor, url in TENORES.items():
        print(f"  Descargando {tenor}...")
        df = scrape_tenor(url)
        df.columns = ['date', tenor]
        dfs[tenor] = df

    merged = dfs['1m']
