class OrderProcessor:
    def __init__(self, orders):
        self.orders = orders

    def process_orders(self):
        def converted_lambda_26(x):
                result = { "id": x["id"], "priority": ( x["priority"] * 2 if x.get("rush", False) else x["priority"] ), "status": "processed", "remarks": f"Order from {x.get('client', 'unknown')} processed with priority {x['priority']}.", }
                return result

        # Long lambda functions for sorting, filtering, and mapping orders
        sorted_orders = sorted(
            self.orders,
            # LONG LAMBDA FUNCTION
            key=lambda x: x.get("priority", 0) + (10 if x.get("vip", False) else 0) + (5 if x.get("urgent", False) else 0),
        )

        filtered_orders = list(
            filter(
                # LONG LAMBDA FUNCTION
                lambda x: x.get("status", "").lower() in ["pending", "confirmed"]
                and len(x.get("notes", "")) > 50
                and x.get("department", "").lower() == "sales",
                sorted_orders,
            )
        )

        processed_orders = list(
            map(
                # LONG LAMBDA FUNCTION
                converted_lambda_26,
                filtered_orders,
            )
        )

        return processed_orders


if __name__ == "__main__":
    orders = [
        {
            "id": 1,
            "priority": 5,
            "vip": True,
            "status": "pending",
            "notes": "Important order.",
            "department": "sales",
        },
        {
            "id": 2,
            "priority": 2,
            "vip": False,
            "status": "confirmed",
            "notes": "Rush delivery requested.",
            "department": "support",
        },
        {
            "id": 3,
            "priority": 1,
            "vip": False,
            "status": "shipped",
            "notes": "Standard order.",
            "department": "sales",
        },
    ]
    processor = OrderProcessor(orders)
    print(processor.process_orders())
