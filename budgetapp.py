class Category:
    def __init__(self, name):
        self.name = name
        self.ledger = []

    def deposit(self, amount, description=""):
        self.ledger.append({'amount': amount, 'description': description})

    def withdraw(self, amount, description=""):
        if self.check_funds(amount):
            self.ledger.append({'amount': -amount, 'description': description})
            return True
        return False

    def get_balance(self):
        balance = 0
        for transaction in self.ledger:
            balance += transaction['amount']
        return balance

    def transfer(self, amount, category):
        if self.check_funds(amount):
            self.withdraw(amount, f"Transfer to {category.name}")
            category.deposit(amount, f"Transfer from {self.name}")
            return True
        return False

    def check_funds(self, amount):
        if amount > self.get_balance():
            return False
        return True

    def __str__(self):
        title = f"{self.name:*^30}\n"
        items = ""
        for transaction in self.ledger:
            description = f"{transaction['description'][:23]:<23}"
            amount = f"{transaction['amount']:>7.2f}"
            items += f"{description}{amount}\n"
        total = f"Total: {self.get_balance():.2f}"
        return title + items + total


def create_spend_chart(categories):
    """
    Returns a bar-chart string showing percentage spent by category.
    """
    # Calculate total withdrawals for each category
    spends = []
    for cat in categories:
        spend = 0
        for item in cat.ledger:
            if item['amount'] < 0:
                spend += abs(item['amount'])
        spends.append(spend)

    # Calculate total spent across all categories
    total_spend = sum(spends)

    # Calculate percentages (rounded down to nearest 10)
    percentages = []
    for spend in spends:
        if total_spend == 0:
            percentages.append(0)
        else:
            pct = (spend / total_spend) * 100
            percentages.append(int(pct // 10) * 10)

    # Build the chart string
    chart = "Percentage spent by category\n"

    # Y-axis labels and bars (100 down to 0 in steps of 10)
    for i in range(100, -1, -10):
        label = str(i).rjust(3) + "| "
        row = label
        for pct in percentages:
            if pct >= i:
                row += "o  "
            else:
                row += "   "
        chart += row + "\n"

    # Horizontal line (4 spaces indent + dashes)
    chart += "    " + "-" * (len(categories) * 3 + 1) + "\n"

    # Category names vertically below the bar
    # FIX: Use 5 spaces indent to align with bars (not 4)
    max_len = max(len(cat.name) for cat in categories)

    for i in range(max_len):
        row = "     "  # 5 spaces indent (aligns with bar positions)
        for cat in categories:
            if i < len(cat.name):
                row += cat.name[i] + "  "  # Character + 2 spaces
            else:
                row += "   "  # 3 spaces for padding
        chart += row + "\n"

    # Remove only the final newline character
    return chart.rstrip("\n")