from typing import List
from dataclasses import dataclass

@dataclass
class Route:
    country: str
    currency: str
    banks: List[str]
    percentages: List[int]
    received: List[int] = None
    index: int = 0
    sent: int = 0

    def __post_init__(self):
        self.received = [0] * len(self.banks)

    def get_bank(self, down_banks: set[str]) -> str:
        if all(bank in down_banks for bank in self.banks):
            return ""
        
        if len(self.percentages) == 0:
            while self.banks[self.index] in down_banks:
                self.index = (self.index + 1) % len(self.banks)
            bank = self.banks[self.index]
            self.index = (self.index + 1) % len(self.banks)
            return bank

        up = sum([percentage for i, percentage in enumerate(self.percentages) if self.banks[i] not in down_banks])

        target = -1
        max_weight = -1
        for i in range(len(self.banks)):
            if self.banks[i] in down_banks:
                continue
            weight = (self.sent + 1) * self.percentages[i] - self.received[i] * up
            if weight > max_weight:
                target = i
                max_weight = weight

        self.received[target] += 1
        self.sent += 1
        return self.banks[target]


class Solution:
    def routePayments(self, partners: List[List[str]], availability: List[List[str]], percentages: List[List[int]], payments: List[List[str]]) -> List[str]:
        routes = {}
        down_banks = set()
        output = []

        for i, partner in enumerate(partners):
            country, currency, banks = partner[0], partner[1], partner[2:]
            routes[(country, currency)] = Route(country, currency, banks, percentages[i])

        for bank, status in availability:
            if status == "no":
                down_banks.add(bank)

        for payment in payments:
            country, currency = payment
            if (country, currency) not in routes:
                output.append("")
                continue
            route = routes[(country, currency)]
            output.append(route.get_bank(down_banks))

        return output

s = Solution()
# partners = [["US","USD","chase","bank_of_america"],["US","EUR","wells","bank_of_america"],["UK","USD","symphony","tello"],["UK","EUR","bank2","bank9"]]
# availability = [["chase","no"],["bank_of_america","yes"]]
# percentages = [[],[],[],[]]
# payments = [["US","USD"],["US","EUR"],["UK","USD"],["US","EUR"],["UK","USD"],["US","USD"],["UK","USD"]]
# partners = [["US","USD","chase","bank_of_america"]]
# availability = []
# percentages = [[70,30]]
# payments = [["US","USD"],["US","USD"],["US","USD"],["US","USD"],["US","USD"],["US","USD"],["US","USD"],["US","USD"],["US","USD"],["US","USD"]]
partners = [["US","USD","chase","bank_of_america","wells"],["UK","USD","symphony"]]
availability = [["chase","no"],["tello","yes"]]
percentages = [[50,30,20],[]]
payments = [["US","USD"],["US","USD"],["CA","USD"],["US","USD"],["US","USD"],["UK","USD"]]
a= s.routePayments(partners, availability, percentages, payments)
print(a)