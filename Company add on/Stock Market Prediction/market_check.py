import yfinance as yf
from datetime import datetime, time
import pytz

sym = 'RELIANCE.NS'
df = yf.download(sym, period='7d', interval='1h', progress=False)
print('Rows:', 0 if df is None else len(df))
print('Last rows:')
if df is not None and len(df)>0:
    print(df.tail(3))
else:
    print('No data')

# Market open check
now = datetime.now(pytz.timezone('Asia/Kolkata'))
open_time = time(9,15)
close_time = time(15,30)
print('Now (IST):', now.strftime('%Y-%m-%d %H:%M:%S'))
print('Market open:', open_time <= now.time() <= close_time)
