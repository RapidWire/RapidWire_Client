# RapidWire Client
pythonでAPI操作を簡単に実行できる可能性を高めます(?)

## 使用例

```python
from rapidwire_client import RapidWireClient

API_KEY = "API_KEY" # /api create で取得したキーに置き換える
BASE_URL = "http://127.0.0.1:14550"

client = RapidWireClient(api_key=API_KEY, base_url=BASE_URL)

# 資産残高の取得
balance = client.get_balance()
print("Currencies:")
for sym, bal in balance.currencies.items():
    print(f"  {bal / 10 ** client.get_config().decimal_places} {sym}")

print("Stocks:")
for sym, bal in balance.stocks.items():
    print(f"  {bal} {sym}")

# 取引履歴の取得
history = client.get_history(page=1)
print("最新の取引:")
if history:
    latest_tx = history[0]
    decimal_places = client.get_config().decimal_places
    amount_str = latest_tx.amount/10 ** decimal_places if latest_tx.type == 'currency' else latest_tx.amount
    print(f"  {latest_tx.operation_type} {amount_str} {latest_tx.symbol}")

```
