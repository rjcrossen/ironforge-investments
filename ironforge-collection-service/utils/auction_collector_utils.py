
import statistics
from typing import Dict, List


def calculate_median_price(auctions: List[Dict]) -> int:
    """Calculate median price from list of auctions"""
    prices = []
    prices.extend(a['unit_price'] for a in auctions for _ in range(a['quantity']))
    prices.sort()
    print(prices)
    return statistics.median(prices)

        
#TODO: add more logic to this estimation. e.g. was it likely that an entry was relisted?
# Could implement a function to check for relistings, return these IDs, and remove from set
#TODO: Once I have market trend data, I need to check if the price of the delisting was
# not in line with the market value. This will tell me if it was a cancellation or a sale.
def estimate_sales(current: List[Dict], previous: List[Dict]) -> int:
    """Estimate sales by tracking disappeared auctions"""
    current_ids = {a['id'] for a in current}
    return sum(
        a['quantity'] for a in previous 
        if a['id'] not in current_ids and a['time_left'] != 1 # 1 = less than 30 minutes
    )

def count_new_listings(current: List[Dict], previous: List[Dict]) -> int:
    """Count new listings by tracking appeared auctions"""
    previous_ids = {a['id'] for a in previous}
    return sum(
        a['quantity'] for a in current 
        # If it has less than 30 minutes left it can't be a new listing
        if a['id'] not in previous_ids and a['time_left'] != 1 # 1 = less than 30 minutes
    )
