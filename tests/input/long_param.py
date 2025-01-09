class OrderProcessor:
    def __init__(self, database_config, api_keys, logger, retry_policy, cache_settings, timezone, locale):
        self.database_config = database_config
        self.api_keys = api_keys
        self.logger = logger
        self.retry_policy = retry_policy
        self.cache_settings = cache_settings
        self.timezone = timezone
        self.locale = locale

    def process_order(self, order_id, customer_info, payment_info, order_items, delivery_info, config, tax_rate, discount_policy):
        # Unpacking data parameters
        customer_name, address, phone, email = customer_info
        payment_method, total_amount, currency = payment_info
        items, quantities, prices, category_tags = order_items
        delivery_address, delivery_date, special_instructions = delivery_info

        # Configurations
        priority_order, allow_partial, gift_wrap = config

        final_total = total_amount * (1 + tax_rate) - discount_policy.get('flat_discount', 0)

        return (
            f"Processed order {order_id} for {customer_name} (Email: {email}).\n"
            f"Items: {items}\n"
            f"Final Total: {final_total} {currency}\n"
            f"Delivery: {delivery_address} on {delivery_date}\n"
            f"Priority: {priority_order}, Partial Allowed: {allow_partial}, Gift Wrap: {gift_wrap}\n"
            f"Special Instructions: {special_instructions}"
        )

    def calculate_shipping(self, package_info, shipping_info, config, surcharge_rate, delivery_speed, insurance_options, tax_config):
        # Unpacking data parameters
        weight, dimensions, package_type = package_info
        destination, origin, country_code = shipping_info

        # Configurations
        shipping_method, insurance, fragile, tracking = config

        surcharge = weight * surcharge_rate if package_type == 'heavy' else 0
        tax_rate = tax_config
        return (
            f"Shipping from {origin} ({country_code}) to {destination}.\n"
            f"Weight: {weight}kg, Dimensions: {dimensions}, Method: {shipping_method}, Speed: {delivery_speed}.\n"
            f"Insurance: {insurance}, Fragile: {fragile}, Tracking: {tracking}.\n"
            f"Surcharge: ${surcharge}, Options: {insurance_options}.\n"
            f"Tax rate: ${tax_rate}"
        )

    def generate_invoice(self, invoice_id, customer_info, order_details, financials, payment_terms, billing_address, support_contact):
        # Unpacking data parameters
        customer_name, email, loyalty_id = customer_info
        items, quantities, prices, shipping_fee, discount_code = order_details
        tax_rate, discount, total_amount, currency = financials

        tax_amount = total_amount * tax_rate
        discounted_total = total_amount - discount

        return (
            f"Invoice {invoice_id} for {customer_name} (Email: {email}, Loyalty ID: {loyalty_id}).\n"
            f"Items: {items}, Quantities: {quantities}, Prices: {prices}.\n"
            f"Shipping Fee: ${shipping_fee}, Tax: ${tax_amount}, Discount: ${discount}.\n"
            f"Final Total: {discounted_total} {currency}.\n"
            f"Payment Terms: {payment_terms}, Billing Address: {billing_address}.\n"
            f"Support Contact: {support_contact}"
        )

# Example usage:

processor = OrderProcessor(
    database_config={"host": "localhost", "port": 3306},
    api_keys={"payment": "abc123", "shipping": "xyz789"},
    logger="order_logger",
    retry_policy={"max_retries": 3, "delay": 5},
    cache_settings={"enabled": True, "ttl": 3600},
    timezone="UTC",
    locale="en-US"
)

# Processing orders
order1 = processor.process_order(
    101,
    ("Alice Smith", "123 Elm St", "555-1234", "alice@example.com"),
    ("Credit Card", 299.99, "USD"),
    (["Laptop", "Mouse"], [1, 1], [999.99, 29.99], ["electronics", "accessories"]),
    ("123 Elm St", "2025-01-15", "Leave at front door"),
    (True, False, True),
    tax_rate=0.07,
    discount_policy={"flat_discount": 50}
)

# Generating invoices
invoice1 = processor.generate_invoice(
    201,
    ("Alice Smith", "alice@example.com", "LOY12345"),
    (["Laptop", "Mouse"], [1, 1], [999.99, 29.99], 20.0, "DISC2025"),
    (0.07, 50.0, 1099.98, "USD"),
    payment_terms="Due upon receipt",
    billing_address="123 Elm St",
    support_contact="support@example.com"
)
