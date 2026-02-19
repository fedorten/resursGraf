import os
import json
import datetime
import yfinance as yf
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

DATA_DIR = os.path.join(os.path.join(os.path.dirname(__file__), 'data'))
os.makedirs(DATA_DIR, exist_ok=True)

RESOURCES = {
    'oil': {'name': 'Нефть', 'symbol': 'CL=F', 'unit': '$/баррель'},
    'gas': {'name': 'Газ', 'symbol': 'NG=F', 'unit': '$/MMBtu'},
    'gasoline': {'name': 'Бензин', 'symbol': 'RB=F', 'unit': '$/галлон'},
    'diesel': {'name': 'Дизель', 'symbol': 'HO=F', 'unit': '$/галлон'},
    'gold': {'name': 'Золото', 'symbol': 'GC=F', 'unit': '$/унция'},
    'silver': {'name': 'Серебро', 'symbol': 'SI=F', 'unit': '$/унция'},
    'copper': {'name': 'Медь', 'symbol': 'HG=F', 'unit': '$/фунт'},
    'steel': {'name': 'Нержавеющая сталь', 'symbol': ' stainless steel', 'unit': '$/тонна'},
    'rub': {'name': 'Рубль', 'symbol': 'RUB=X', 'unit': '₽/USD'}
}

COMMODITY_MAP = {
    'oil': 'CL=F',
    'gas': 'NG=F', 
    'gasoline': 'RB=F',
    'diesel': 'HO=F',
    'gold': 'GC=F',
    'silver': 'SI=F',
    'copper': 'HG=F',
    'rub': 'RUB=X'
}

def get_data_file_path(resource):
    return os.path.join(DATA_DIR, f'{resource}.json')

def load_history(resource):
    filepath = get_data_file_path(resource)
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return []

def save_history(resource, history):
    filepath = get_data_file_path(resource)
    with open(filepath, 'w') as f:
        json.dump(history, f)

def fetch_price_yahoo(symbol):
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period='1d')
        if not data.empty:
            return float(data['Close'].iloc[-1])
        return None
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None

def fetch_history_yahoo(symbol, period='1y', interval='1d'):
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=period, interval=interval)
        if data.empty:
            return []
        result = []
        for date, row in data.iterrows():
            result.append({
                'date': date.strftime('%Y-%m-%d'),
                'price': float(row['Close'])
            })
        return result
    except Exception as e:
        print(f"Error fetching history for {symbol}: {e}")
        return []

def update_all_prices():
    for resource, info in RESOURCES.items():
        symbol = info['symbol']
        history = load_history(resource)
        today = datetime.date.today().isoformat()
        
        if resource == 'steel':
            continue
            
        if history and history[-1].get('date') == today:
            continue
        
        price = fetch_price_yahoo(symbol)
        if price is not None:
            history.append({'date': today, 'price': price})
            save_history(resource, history)

def update_history_for_all():
    period_map = {
        'week': '5d',
        'month': '1mo', 
        '3months': '3mo',
        'year': '1y',
        '3years': '3y',
        'all': '5y'
    }
    
    for resource, info in RESOURCES.items():
        symbol = info['symbol']
        
        if resource == 'steel':
            continue
        
        existing = load_history(resource)
        
        for period_name, yf_period in period_map.items():
            history = fetch_history_yahoo(symbol, yf_period)
            if history:
                filepath = os.path.join(DATA_DIR, f'{resource}_{period_name}.json')
                with open(filepath, 'w') as f:
                    json.dump(history, f)
        
        if not existing or len(existing) == 0:
            full_history = fetch_history_yahoo(symbol, '5y')
            if full_history:
                save_history(resource, full_history)

@app.route('/')
def index():
    return render_template('index.html', resources=RESOURCES)

@app.route('/api/price/<resource>')
def get_price(resource):
    if resource not in RESOURCES:
        return jsonify({'error': 'Resource not found'}), 404
    
    history = load_history(resource)
    if not history:
        price = fetch_price_yahoo(RESOURCES[resource]['symbol'])
        if price:
            history = [{'date': datetime.date.today().isoformat(), 'price': price}]
            save_history(resource, history)
        else:
            return jsonify({'error': 'No data'}), 404
    
    latest = history[-1]
    return jsonify({
        'resource': resource,
        'name': RESOURCES[resource]['name'],
        'unit': RESOURCES[resource]['unit'],
        'price': latest['price'],
        'date': latest['date']
    })

@app.route('/api/history/<resource>')
def get_history(resource):
    if resource not in RESOURCES:
        return jsonify({'error': 'Resource not found'}), 404
    
    history = load_history(resource)
    if not history or len(history) == 0:
        history = fetch_history_yahoo(RESOURCES[resource]['symbol'], '5y')
        if history:
            save_history(resource, history)
    
    return jsonify(history)

@app.route('/api/history/<resource>/<period>')
def get_history_period(resource, period):
    if resource not in RESOURCES:
        return jsonify({'error': 'Resource not found'}), 404
    
    if resource == 'steel':
        return jsonify([{'date': datetime.date.today().isoformat(), 'price': 2500}])
    
    period_map = {
        'week': ('5d', '1d'),
        'month': ('1mo', '1d'),
        '3months': ('3mo', '1d'),
        'year': ('1y', '1d'),
        '3years': ('3y', '1wk'),
        'all': ('5y', '1wk')
    }
    
    yf_period, yf_interval = period_map.get(period, ('1y', '1d'))
    history = fetch_history_yahoo(RESOURCES[resource]['symbol'], yf_period, yf_interval)
    
    if history and len(history) > 0:
        save_history(resource, history)
    
    return jsonify(history)

@app.route('/chart/<resource>')
def chart_page(resource):
    if resource not in RESOURCES:
        return render_template('404.html'), 404
    return render_template('chart.html', resource=resource, resources=RESOURCES)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
