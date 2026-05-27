import requests
import pandas as pd
import os
from datetime import datetime, timedelta

CSV_PATH = "euribor_diario_2026.csv"

SERIES = {
    '1m':  'FM.B.U2.EUR.RT.MM.EURIBOR1MD_.HSTA',
    '3m':  'FM.B.U2.EUR.RT.MM.EURIBOR3MD_.HSTA',
    '6m':  'FM.B.U2.EUR.RT.MM.EURIBOR6MD_.HSTA',
    '12m': 'FM.B.U2.EUR.RT.MM.EURIBOR1YD_.HSTA',
}

def descargar_serie(series_key, start_date):
    url = (
        f"https://data-api.ecb.europa.eu/service/data/FM/{series_key.split('.',2)[2]}"
        f"?startPeriod={start_date}&format=csvdata"
    )
    # Usar la API correcta del BCE
    url = f"https://data-api.ecb.europa.eu/service/data/FM/{series_key}?startPeriod={start_date}&format=csvdata"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    from io import StringIO
    df = pd.read_csv(StringIO(r.text))
    # La columna de fecha se llama TIME_PERIOD y el valor OBS_VALUE
    df = df[['TIME_PERIOD', 'OBS_VALUE']].dropna()
    df.columns = ['date', 'value']
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    return df.dropna()

def main():
    if os.path.exists(CSV_PATH):
        existing = pd.read_csv(CSV_PATH)
        existing['date'] = existing['date'].astype(str)
        last_date = existing['date'].max()
        start = (datetime.strptime(last_date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
        print(f"CSV existente: {len(existing)} filas | Ultimo: {last_date} | Descargando desde: {start}")
    else:
        existing = None
        start = '2026-01-01'
        print(f"Primer run. Descargando desde {start}...")

    dfs = {}
    for tenor, series_key in SERIES.items():
        print(f"  Descargando {tenor}...")
        df = descargar_serie(series_key, start)
        df.columns = ['date', tenor]
        dfs[tenor] = df
        print(f"    {len(df)} filas nuevas")

    merged = dfs['1m']
    for t in ['3m', '6m', '12m']:
        merged = merged.merge(dfs[t], on='date', how='outer')

    merged = merged.sort_values('date').reset_index(drop=True)
    print(f"Filas nuevas tras merge: {len(merged)}")

    if existing is not None and len(merged) > 0:
        combined = pd.concat([existing, merged])
        combined = combined.drop_duplicates(subset='date', keep='last')
        combined = combined.sort_values('date').reset_index(drop=True)
    elif existing is not None:
        combined = existing
        print("No hay datos nuevos.")
    else:
        combined = merged

    combined.to_csv(CSV_PATH, index=False, float_format='%.4f')
    print(f"Guardado: {len(combined)} filas | Ultimo: {combined['date'].max()}")

if __name__ == "__main__":
    main()
