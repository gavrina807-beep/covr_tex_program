from flask import Flask, render_template
import requests
from datetime import datetime

app = Flask(__name__)

# Ссылка на API Московской Биржи для государственных облигаций (ОФЗ) в режиме торгов TQOB
MOEX_BONDS_URL = "https://iss.moex.com/iss/engines/stock/markets/bonds/boards/TQOB/securities.json?iss.meta=off"

@app.route('/')
def index():
    try:
        # Запрашиваем данные по облигациям у Мосбиржи
        response = requests.get(MOEX_BONDS_URL, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        securities_data = data.get("securities", {})
        marketdata_data = data.get("marketdata", {})
        
        sec_columns = securities_data.get("columns", [])
        sec_rows = securities_data.get("data", [])
        
        market_columns = marketdata_data.get("columns", [])
        market_rows = marketdata_data.get("data", [])
        
        # Индексы колонок базовой информации об облигациях
        secid_idx = sec_columns.index("SECID")
        name_idx = sec_columns.index("SHORTNAME")
        facevalue_idx = sec_columns.index("FACEVALUE") # Номинал облигации
        
        # Индексы колонок текущих рыночных данных
        m_secid_idx = market_columns.index("SECID")
        last_idx = market_columns.index("LAST")        # Цена в % от номинала
        change_idx = market_columns.index("CHANGE")    # Изменение цены за день в %
        yield_idx = market_columns.index("YIELD")      # Доходность к погашению, %
        
        # Создаем карту базовых свойств облигации по её тикеру (SECID)
        sec_map = {row[secid_idx]: {"name": row[name_idx], "face": row[facevalue_idx]} for row in sec_rows}
        
        # Выбираем популярные выпуски ОФЗ с фиксированным купоном для дашборда
        target_bonds = [
            'SU26238RMFS4',  # ОФЗ 26238
            'SU26240RMFS0',  # ОФЗ 26240
            'SU26241RMFS8',  # ОФЗ 26241
            'SU26242RMFS6',  # ОФЗ 26242
            'SU26243RMFS4',  # ОФЗ 26243
            'SU26244RMFS2'   # ОФЗ 26244
        ]
        
        processed_bonds = []
        
        for row in market_rows:
            secid = row[m_secid_idx]
            if secid in target_bonds:
                price_percent = row[last_idx]
                change = row[change_idx] if row[change_idx] is not None else 0.0
                bond_yield = row[yield_idx]
                
                # Если текущих сделок еще нет, цена и доходность могут быть пустыми
                if price_percent is None:
                    price_percent = 100.0  # Условно базовый процент
                
                processed_bonds.append({
                    "ticker": secid,
                    "name": sec_map[secid]["name"],
                    "face_value": sec_map[secid]["face"],
                    "price_percent": round(price_percent, 2),
                    "change": round(change, 2),
                    "yield": round(bond_yield, 2) if bond_yield else "—"
                })
        
        # Сортируем облигации по названию выпуска
        processed_bonds.sort(key=lambda x: x['name'])
        
        current_date = datetime.now().strftime("%d.%m.%Y в %H:%M")
        return render_template('index.html', bonds=processed_bonds, date=current_date)
        
    except Exception as e:
        return render_template('index.html', error=f"Ошибка загрузки данных долгового рынка: {e}")

if __name__ == '__main__':
    app.run(debug=True)