from typing import List, Optional, Dict, Any, Literal
from dataclasses import dataclass
import requests

# --- Client Version ---
CLIENT_VERSION = "1.0.0"

# --- Custom Exception ---

class RapidWireAPIError(Exception):
    """
    RapidWire APIからエラーが返された場合に発生するカスタム例外。
    
    Attributes:
        status_code (int): HTTPステータスコード。
        detail (str): APIから返されたエラー詳細メッセージ。
    """
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"API Error {status_code}: {detail}")

# --- Data Models (Type Hinting) ---

@dataclass
class CurrencyInfo:
    """通貨情報を表すデータクラス。"""
    id: int
    symbol: str
    name: str
    supply: int
    issuer_id: Optional[int]
    description: Optional[str]

@dataclass
class StockInfo:
    """株式情報を表すデータクラス。"""
    id: int
    symbol: str
    name: str
    supply: int
    issuer_id: Optional[int]
    industry: Optional[str]
    overview: Optional[str]

@dataclass
class Balance:
    """ユーザーの資産残高を表すデータクラス。"""
    currencies: Dict[str, int]
    stocks: Dict[str, int]

@dataclass
class HistoryEntry:
    """取引履歴のエントリを表すデータクラス。"""
    type: str
    operation_type: str
    timestamp: int
    source: int
    dest: int
    symbol: str
    amount: int

@dataclass
class UserOrder:
    """ユーザーのアクティブな売り注文を表すデータクラス。"""
    order_id: int
    stock_symbol: str
    price: int
    amount: int
    timestamp: int

@dataclass
class OrderbookEntry:
    """注文板のエントリを表すデータクラス。"""
    price: int
    amount: int

@dataclass
class Orderbook:
    """株式の注文板を表すデータクラス。"""
    stock_symbol: str
    orders: List[OrderbookEntry]

@dataclass
class LiquidityInfo:
    """流動性プールの情報を表すデータクラス。"""
    currency_symbol: str
    base_liquidity: int
    pair_liquidity: int
    total_lp_points: int

@dataclass
class Config:
    """APIサーバーの設定情報を表すデータクラス。"""
    decimal_places: int
    base_currency: CurrencyInfo

@dataclass
class SuccessResponse:
    """成功時のAPIレスポンスを表すデータクラス。"""
    message: str
    details: Optional[Dict] = None


# --- API Client ---

class RapidWireClient:
    """
    RapidWire APIと対話するためのクライアント。
    """
    def __init__(self, api_key: str, base_url: str = "http://127.0.0.1:14550"):
        """
        RapidWireClientを初期化します。

        Args:
            api_key (str): RapidWireボットから取得したAPIキー。
            base_url (str, optional): RapidWire APIサーバーのベースURL。
                                      デフォルトは "http://127.0.0.1:14550"。
        """
        if not api_key:
            raise ValueError("APIキーは必須です。")
        self.base_url = base_url.rstrip('/')
        self._session = requests.Session()
        self._session.headers.update({
            "API-Key": api_key,
            "Content-Type": "application/json"
        })

        # 初期化時にサーバーバージョンをチェック
        self._check_version()

    def _check_version(self):
        """
        クライアントとサーバーのメジャーバージョンが一致するか確認し、
        不一致の場合は警告を表示します。
        """
        try:
            server_version_response = self.get_version()
            server_version_str = server_version_response.details.get("version")

            if not server_version_str:
                print(
                    "Warning: サーバーのバージョンを特定できませんでした。互換性は保証されません。",
                )
                return

            client_major = CLIENT_VERSION.split('.')[0]
            server_major = server_version_str.split('.')[0]

            if client_major != server_major:
                print(
                    f"Warning: クライアントバージョン ({CLIENT_VERSION}) とサーバーバージョン ({server_version_str}) の "
                    f"メジャーバージョンが一致しません。機能が正常に動作しない可能性があります。",
                )
        except RapidWireAPIError as e:
            print(
                f"Warning: バージョン確認のためにサーバーへの接続に失敗しました: {e}。 "
                "クライアントに互換性がない可能性があります。",
            )


    def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        """
        APIへのリクエストを送信する内部メソッド。

        Args:
            method (str): HTTPメソッド (GET, POST, DELETEなど)。
            endpoint (str): APIエンドポイント。

        Raises:
            RapidWireAPIError: APIがエラーステータスコードを返した場合。

        Returns:
            Any: APIからのレスポンス(JSON)。
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = self._session.request(method, url, **kwargs)
            
            if not response.ok:
                error_detail = "Unknown error"
                try:
                    error_detail = response.json().get("detail", error_detail)
                except requests.exceptions.JSONDecodeError:
                    error_detail = response.text
                raise RapidWireAPIError(response.status_code, error_detail)

            if response.status_code == 204: # No Content
                return None
                
            return response.json()
        except requests.exceptions.RequestException as e:
            raise RapidWireAPIError(status_code=500, detail=f"Request failed: {e}")

    # --- Info Endpoints ---
    def get_version(self) -> SuccessResponse:
        """APIサーバーのバージョンを取得します。"""
        # api_server.pyのバージョンは"1.0.0"
        data = self._request("GET", "/version")
        return SuccessResponse(**data)

    def get_config(self) -> Config:
        """APIサーバーの設定情報を取得します。"""
        data = self._request("GET", "/config")
        data['base_currency'] = CurrencyInfo(**data['base_currency'])
        return Config(**data)

    # --- Account Endpoints ---
    def get_balance(self) -> Balance:
        """認証ユーザーの資産残高を取得します。"""
        data = self._request("GET", "/account/balance")
        return Balance(**data)

    def get_history(self, page: int = 1) -> List[HistoryEntry]:
        """認証ユーザーの取引履歴を取得します。"""
        data = self._request("GET", "/account/history", params={"page": page})
        return [HistoryEntry(**entry) for entry in data]

    def get_my_stock_orders(self) -> List[UserOrder]:
        """認証ユーザーのアクティブな株式売り注文をすべて取得します。"""
        data = self._request("GET", "/account/stock/orders")
        return [UserOrder(**order) for order in data]

    # --- Public Info Endpoints ---
    def get_currency_info(self, symbol: str) -> CurrencyInfo:
        """指定された通貨の公開情報を取得します。"""
        data = self._request("GET", f"/currency/{symbol.upper()}")
        return CurrencyInfo(**data)

    def get_stock_info(self, symbol: str) -> StockInfo:
        """指定された株式の公開情報を取得します。"""
        data = self._request("GET", f"/stock/{symbol.upper()}")
        return StockInfo(**data)

    # --- Transfer Endpoints ---
    def transfer_currency(self, recipient_id: int, asset_symbol: str, amount: int) -> SuccessResponse:
        """指定した量の通貨を別のユーザーに送金します。"""
        payload = {
            "recipient_id": recipient_id,
            "asset_symbol": asset_symbol.upper(),
            "amount": amount
        }
        data = self._request("POST", "/currency/transfer", json=payload)
        return SuccessResponse(**data)

    def transfer_stock(self, recipient_id: int, asset_symbol: str, amount: int) -> SuccessResponse:
        """指定した株数の株式を別のユーザーに送付します。"""
        payload = {
            "recipient_id": recipient_id,
            "asset_symbol": asset_symbol.upper(),
            "amount": amount
        }
        data = self._request("POST", "/stock/transfer", json=payload)
        return SuccessResponse(**data)

    # --- Trading Endpoints ---
    def get_stock_orderbook(self, symbol: str) -> Orderbook:
        """指定された株式の現在の売り注文板を取得します。"""
        data = self._request("GET", f"/stock/{symbol.upper()}/orderbook")
        data['orders'] = [OrderbookEntry(**entry) for entry in data['orders']]
        return Orderbook(**data)

    def create_sell_order(self, stock_symbol: str, price: int, amount: int) -> SuccessResponse:
        """株式の新しい売り注文を作成します。"""
        payload = {
            "stock_symbol": stock_symbol.upper(),
            "price": price,
            "amount": amount
        }
        data = self._request("POST", "/market/stock/sell-order", json=payload)
        return SuccessResponse(**data)

    def market_buy_stock(self, stock_symbol: str, amount: int) -> SuccessResponse:
        """株式の成行買いを実行します。"""
        payload = {
            "stock_symbol": stock_symbol.upper(),
            "amount": amount
        }
        data = self._request("POST", "/market/stock/market-buy", json=payload)
        return SuccessResponse(**data)

    def cancel_sell_order(self, order_id: int) -> SuccessResponse:
        """作成したアクティブな売り注文をキャンセルします。"""
        data = self._request("DELETE", f"/market/stock/sell-order/{order_id}")
        return SuccessResponse(**data)

    def get_liquidity_info(self, symbol: str) -> LiquidityInfo:
        """通貨の現在の流動性情報を取得します。"""
        data = self._request("GET", f"/market/currency/liquidity/{symbol.upper()}")
        return LiquidityInfo(**data)
        
    def buy_currency(self, currency_symbol: str, amount_in: int) -> SuccessResponse:
        """流動性プールから通貨を購入（スワップ）します。"""
        payload = {
            "currency_symbol": currency_symbol.upper(),
            "amount": amount_in
        }
        data = self._request("POST", "/market/currency/buy", json=payload)
        return SuccessResponse(**data)

    def sell_currency(self, currency_symbol: str, amount_in: int) -> SuccessResponse:
        """流動性プールへ通貨を売却（スワップ）します。"""
        payload = {
            "currency_symbol": currency_symbol.upper(),
            "amount": amount_in
        }
        data = self._request("POST", "/market/currency/sell", json=payload)
        return SuccessResponse(**data)
