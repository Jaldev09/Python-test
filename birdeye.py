"""
Client for BirdEyeClient APIs
"""

from decimal import Decimal
from typing import Any
from urllib.parse import quote
import requests

from common import PriceInfo, TokenOverview
from custom_exceptions import InvalidSolanaAddress, InvalidTokens, NoPositionsError
from helper import is_solana_address
# from vars.constants import BIRD_EYE_TOKEN
from dotenv import load_dotenv
import os
load_dotenv()

BIRD_EYE_TOKEN = os.getenv('BIRD_EYE_TOKEN')    # PROVIDED API KEY IS UNAUTHORIZED 


class BirdEyeClient:
    """
    Handler class to assist with all calls to BirdEye API
    """

    @property
    def _headers(self):
        return {
            "accept": "application/json",
            "x-chain": "solana",
            "X-API-KEY": BIRD_EYE_TOKEN,
        }

    def _make_api_call(self, method: str, query_url: str, *args, **kwargs) -> requests.Response:
        match method.upper():
            case "GET":
                query_method = requests.get
            case "POST":
                query_method = requests.post
            case _:
                raise ValueError(f'Unrecognised method "{method}" passed for query - {query_url}')

        resp = query_method(query_url, *args, headers=self._headers, **kwargs)
        return resp


    def fetch_prices(self, token_addresses: list[str]) -> dict[str, PriceInfo[Decimal, Decimal]]:
        """
        For a list of tokens fetches their prices
        via multi-price API ensuring each token has a price

        Args:
            token_addresses (list[str]): A list of tokens for which to fetch prices

        Returns:
           dict[str, dict[str, PriceInfo[Decimal, Decimal]]: Mapping of token to a named tuple PriceInfo with price and liquidity

        Raises:
            NoPositionsError: Raise if no tokens are provided
            InvalidToken: Raised if the API call was unsuccessful
        """

        if not token_addresses:
            raise NoPositionsError()

        base_url = "https://public-api.birdeye.so/defi/multi_price"
        list_address = ",".join(token_addresses)
        encoded_list_address = quote(list_address)
        url = f"{base_url}?list_address={encoded_list_address}"

        response = self._make_api_call("GET", url)
        if response.status_code != 200:
            raise InvalidTokens()

        data = response.json()
        if not data.get("success"):
            raise InvalidTokens()

        prices = {}
        for token_address in token_addresses:
            token_data = data.get("data", {}).get(token_address, {})
            if token_data:
                value = Decimal(token_data.get("price", "0"))
                liquidity = Decimal(token_data.get("liquidity", "0"))
                prices[token_address] = PriceInfo(value, liquidity)

        return prices
        

    def fetch_token_overview(self, address: str) -> TokenOverview:
        """
        For a token fetches their overview
        via multi-price API ensuring each token has a price

        Args:
            address (str): A token address for which to fetch overview

        Returns:
            dict[str, float | str]: Overview with a lot of token information I don't understand

        Raises:
            InvalidSolanaAddress: Raise if invalid solana address is passed
            InvalidToken: Raised if the API call was unsuccessful
       """
        
        if not is_solana_address(address):
            raise InvalidSolanaAddress(f"{address}")

        url = f"https://api.birdeye.so/v1/token-overview/{address}" 
        response = self._make_api_call("GET", url)
        if response.status_code != 200:
            raise InvalidTokens()

        data = response.json()
        if not data.get("success"):
            raise InvalidTokens()

        overview_data = data.get("data", {})
        return TokenOverview(**overview_data)
