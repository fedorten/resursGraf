import os
import datetime
import requests
from flask import Flask, render_template, jsonify
from functools import lru_cache

app = Flask(__name__)

RESOURCES = {
    'oil': {'name': 'Нефть', 'unit': '$/баррель'},
    'gas': {'name': 'Газ', 'unit': '$/MMBtu'},
    'gasoline': {'name': 'Бензин', 'unit': '$/галлон'},
    'diesel': {'name': 'Дизель', 'unit': '$/галлон'},
    'gold': {'name': 'Золото', 'unit': '$/унция'},
    'silver': {'name': 'Серебро', 'unit': '$/унция'},
    'copper': {'name': 'Медь', 'unit': '$/фунт'},
    'steel': {'name': 'Нержавеющая сталь', 'unit': '$/тонна'},
    'rub': {'name': 'Рубль', 'unit': '₽/USD'}
}

SYMBOLS = {
    'oil': 'CL=F',
    'gas': 'NG=F',
    'gasoline': 'RB=F',
    'diesel': 'HO=F',
    'gold': 'GC=F',
    'silver': 'SI=F',
    'copper': 'HG=F'
}

@lru_cache(maxsize=1)
def get_cached_history(symbol):
    try:
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=5y&interval=1wk'
        resp = requests.get(url, timeout=15)
        data = resp.json()
        if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
            result = data['chart']['result'][0]
            timestamps = result.get('timestamp', [])
            close = result.get('indicators', {}).get('quote', [{}])[0].get('close', [])
            history = []
            for i, ts in enumerate(timestamps):
                if close[i] is not None:
                    date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                    history.append({'date': date, 'price': float(close[i])})
            return history
        return []
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return []

@lru_cache(maxsize=1)
def get_rub_history():
    try:
        url = 'https://api.frankfurter.dev/v1/2000-01-01..2026-02-19?base=USD&symbol=RUB'
        resp = requests.get(url, timeout=30)
        data = resp.json()
        if 'rates' in data:
            result = []
            for date, rates in data['rates'].items():
                result.append({'date': date, 'price': float(rates['RUB'])})
            return sorted(result, key=lambda x: x['date'])
        return []
    except Exception as e:
        print(f"Error fetching rub: {e}")
        return []

@app.route('/')
def index():
    return render_template('index.html', resources=RESOURCES)

@app.route('/api/price/<resource>')
def get_price(resource):
    if resource not in RESOURCES:
        return jsonify({'error': 'Resource not found'}), 404
    
    if resource == 'steel':
        return jsonify({
            'resource': resource,
            'name': RESOURCES[resource]['name'],
            'unit': RESOURCES[resource]['unit'],
            'price': 2500,
            'date': datetime.date.today().isoformat()
        })
    
    if resource == 'rub':
        history = get_rub_history()
    else:
        symbol = SYMBOLS.get(resource)
        if not symbol:
            return jsonify({'error': 'No data'}), 404
        history = get_cached_history(symbol)
    
    if not history:
        return jsonify({'error': 'No data'}), 404
    
    latest = history[-1]
    return jsonify({
        'resource': resource,
        'name': RESOURCES[resource]['name'],
        'unit': RESOURCES[resource]['unit'],
        'price': latest['price'],
        'date': latest['date']
    })

@app.route('/api/history/<resource>/<period>')
def get_history_period(resource, period):
    if resource not in RESOURCES:
        return jsonify({'error': 'Resource not found'}), 404
    
    if resource == 'steel':
        return jsonify([{'date': datetime.date.today().isoformat(), 'price': 2500}])
    
    if resource == 'rub':
        history = get_rub_history()
    else:
        symbol = SYMBOLS.get(resource)
        if not symbol:
            return jsonify([])
        history = get_cached_history(symbol)
    
    if not history:
        return jsonify([])
    
    period_days = {
        'week': 7,
        'month': 30,
        '3months': 90,
        'year': 365,
        '3years': 1095,
        'all': None
    }
    
    days = period_days.get(period)
    if days:
        cutoff = datetime.datetime.now().date() - datetime.timedelta(days=days)
        history = [h for h in history if datetime.datetime.strptime(h['date'], '%Y-%m-%d').date() >= cutoff]
    
    return jsonify(history)

@app.route('/chart/<resource>')
def chart_page(resource):
    if resource not in RESOURCES:
        return render_template('404.html'), 404
    return render_template('chart.html', resource=resource, resources=RESOURCES)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
