import os
import requests
import pandas as pd
import matplotlib.pyplot as plt

api_key = os.environ['API_KEY']
url = 'https://api.eia.gov/v2/electricity/state-electricity-profiles/capability/data/'

params= {
    'frequency':'annual',
    'data[0]':'capability',
    'sort[0][column]': 'period',
    'sort[0][direction]': 'desc',
    'offset':0,
    'length':5000,
}
response = requests.get(url, params=params)
data = response.json()
df = pd.DataFrame(data,['response']['data'])
df['period'] = pd.to_datetime(df['period'])
df.set_index('period',inplace=True)

plt.figure(figsize=(10,6))
plt.plot(df['value'])
plt.xlabel('Date')
plt.ylabel('Value')
plt.title('Electricity Data')
plt.grid(True)
plt.show()