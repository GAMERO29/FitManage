import os
from decimal import Decimal

import requests

from domain.ports import PaymentGatewayPort


class PayUGateway(PaymentGatewayPort):
    def __init__(self):
        self.api_key = os.environ["PAYU_API_KEY"]

    def charge(self, amount: Decimal) -> bool:
        response = requests.post(
            "https://api.payulatam.com/payments-api/4.0/service.cgi",
            json={"apiKey": self.api_key, "amount": str(amount)},
            timeout=10,
        )
        return response.status_code == 200
