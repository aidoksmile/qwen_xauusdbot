def get_asset_data(symbol='GC=F'):
    """Поддержка нескольких активов"""
    symbols = {
        'XAU/USD': 'GC=F',
        'XAG/USD': 'SI=F',
        'EUR/USD': 'EURUSD=X',
        'GBP/USD': 'GBPUSD=X',
        'USD/JPY': 'JPY=X',
        'BTC/USD': 'BTC-USD',
        'TESLA': 'TSLA'
    }
    
    ticker = symbols.get(symbol, symbol)
    daily = download_data(ticker, '1d')
    fifteen_min = download_data(ticker, '15m')
    return daily, fifteen_min
