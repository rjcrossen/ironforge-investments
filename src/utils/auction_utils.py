import statistics

# TODO: add more logic to this estimation. e.g. was it likely that an entry was relisted?
# Could implement a function to check for relistings, return these IDs, and remove from set
# TODO: Once I have market trend data, I need to check if the price of the delisting was
# not in line with the market value. This will tell me if it was a cancellation or a sale.


def calculate_median_price(auctions: list[dict]) -> int:
    """Calculate median price from list of auctions"""
    prices = []
    prices.extend(a["unit_price"] for a in auctions for _ in range(a["quantity"]))
    prices.sort()
    return statistics.median(prices)


def estimate_sales(current: list[dict], previous: list[dict]) -> int:
    """Estimate sales by tracking disappeared auctions"""
    current_ids = {a["id"] for a in current}
    return sum(
        a["quantity"]
        for a in previous
        if a["id"] not in current_ids
        and a["time_left"] != 1  # 1 = less than 30 minutes
    )


def count_new_listings(current: list[dict], previous: list[dict]) -> int:
    """Count new listings by tracking appeared auctions"""
    previous_ids = {a["id"] for a in previous}
    return sum(
        a["quantity"]
        for a in current
        # If it has less than 30 minutes left it can't be a new listing
        if a["id"] not in previous_ids
        and a["time_left"] != 1  # 1 = less than 30 minutes
    )


def calculate_commodity_stats(auctions: list[dict]) -> dict:
    """Calculate statistics for a commodity from its auctions
    
    Args:
        auctions: List of auction dictionaries containing 'unit_price' and 'quantity'
    
    Returns:
        Dictionary containing min_price, max_price, mean_price, median_price,
        total_quantity, and num_auctions
    """
    if not auctions:
        return {
            'min_price': None,
            'max_price': None,
            'mean_price': None,
            'median_price': None,
            'total_quantity': 0,
            'num_auctions': 0
        }
        
    prices = []
    quantities = []
    
    for auction in auctions:
        price = auction['unit_price']
        quantity = auction['quantity']
        # Extend prices list with the price repeated for each item
        prices.extend([price] * quantity)
        quantities.append(quantity)
    
    return {
        'min_price': min(prices),
        'max_price': max(prices),
        'mean_price': statistics.mean(prices),
        'median_price': statistics.median(prices),
        'total_quantity': sum(quantities),
        'num_auctions': len(auctions)
    }
