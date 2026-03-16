from typing import Union, List, Optional
from datetime import datetime


class Category:
    """
    A budget category that tracks deposits, withdrawals, and transfers.

    Attributes:
        name (str): The name of the category
        ledger (list): List of transaction dictionaries
    """

    def __init__(self, name: str):
        """
        Initialize a new Category instance.

        Args:
            name (str): The name of the category
        """
        self.name = name
        self.ledger: List[dict] = []
        self._balance: float = 0.0  # Cached balance for performance

    def deposit(self, amount: Union[int, float], description: str = "") -> None:
        """
        Add a deposit to the ledger.

        Args:
            amount (float): Positive amount to deposit
            description (str): Optional description of the transaction

        Raises:
            ValueError: If amount is negative or not a number
        """
        if not isinstance(amount, (int, float)):
            raise TypeError("Amount must be a number")
        if amount < 0:
            raise ValueError("Amount must be non-negative")

        self.ledger.append({
            'amount': float(amount),
            'description': description,
            'date': datetime.now().strftime("%Y-%m-%d")  # Bonus: date tracking
        })
        self._balance += float(amount)

    def withdraw(self, amount: Union[int, float], description: str = "") -> bool:
        """
        Add a withdrawal to the ledger if sufficient funds exist.

        Args:
            amount (float): Positive amount to withdraw
            description (str): Optional description of the transaction

        Returns:
            bool: True if withdrawal succeeded, False otherwise
        """
        if not isinstance(amount, (int, float)):
            return False
        if amount < 0:
            return False

        if self.check_funds(amount):
            self.ledger.append({
                'amount': -float(amount),
                'description': description,
                'date': datetime.now().strftime("%Y-%m-%d")
            })
            self._balance -= float(amount)
            return True
        return False

    def get_balance(self) -> float:
        """
        Calculate and return the current balance.

        Returns:
            float: Current balance of the category
        """
        # Use cached balance for performance
        # If you need to recalculate (e.g., after manual ledger edits):
        # return sum(item['amount'] for item in self.ledger)
        return self._balance

    def transfer(self, amount: Union[int, float], category: 'Category') -> bool:
        """
        Transfer funds from this category to another.

        Args:
            amount (float): Amount to transfer
            category (Category): Destination category

        Returns:
            bool: True if transfer succeeded, False otherwise
        """
        if not isinstance(amount, (int, float)) or amount < 0:
            return False
        if not isinstance(category, Category):
            raise TypeError("Transfer target must be a Category instance")

        if self.check_funds(amount):
            self.withdraw(amount, f"Transfer to {category.name}")
            category.deposit(amount, f"Transfer from {self.name}")
            return True
        return False

    def check_funds(self, amount: Union[int, float]) -> bool:
        """
        Check if the category has sufficient funds for a transaction.

        Args:
            amount (float): Amount to check

        Returns:
            bool: True if funds are sufficient, False otherwise
        """
        return amount <= self.get_balance()

    def get_withdrawals(self) -> List[dict]:
        """
        Get all withdrawal transactions from the ledger.

        Returns:
            list: List of withdrawal transaction dictionaries
        """
        return [item for item in self.ledger if item['amount'] < 0]

    def __str__(self) -> str:
        """
        Return a formatted string representation of the category ledger.

        Returns:
            str: Formatted ledger output
        """
        title = f"{self.name:*^30}\n"
        items = ""

        for transaction in self.ledger:
            # Truncate description to 23 chars for formatting
            description = f"{transaction['description'][:23]:<23}"
            amount = f"{transaction['amount']:>7.2f}"
            items += f"{description}{amount}\n"

        total = f"Total: {self.get_balance():.2f}"
        return title + items + total

    def __repr__(self) -> str:
        """
        Return a developer-friendly representation of the Category.

        Returns:
            str: Repr string with name and balance
        """
        return f"Category('{self.name}', balance={self.get_balance():.2f})"


def create_spend_chart(categories: List[Category]) -> str:
    """
    Create a horizontal bar chart showing percentage spent by category.

    Args:
        categories (list): List of Category objects to analyze

    Returns:
        str: Formatted chart string ready for printing
    """
    # Handle empty input
    if not categories:
        return "Percentage spent by category\n"

    # Calculate total withdrawals for each category
    spends = []
    for cat in categories:
        spend = sum(abs(item['amount']) for item in cat.ledger if item['amount'] < 0)
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
        chart += row.rstrip() + "\n"

    # Horizontal line (4 spaces indent + dashes)
    chart += "    " + "-" * (len(categories) * 3 + 1) + "\n"

    # Category names vertically below the bar
    max_len = max(len(cat.name) for cat in categories)

    for i in range(max_len):
        row = "     "  # 5 spaces indent to align with bars
        for cat in categories:
            if i < len(cat.name):
                row += cat.name[i] + "  "
            else:
                row += "   "
        chart += row.rstrip() + "\n"

    # Remove only the final newline character
    return chart.rstrip("\n")


# ============= UTILITY FUNCTIONS =============

def export_to_csv(category: Category, filename: Optional[str] = None) -> str:
    """
    Export a category's ledger to CSV format.

    Args:
        category (Category): The category to export
        filename (str, optional): If provided, saves to file

    Returns:
        str: CSV formatted string
    """
    csv_lines = ["date,amount,description"]
    for item in category.ledger:
        date = item.get('date', '')
        amount = item['amount']
        desc = item['description'].replace(',', ';')  # Escape commas
        csv_lines.append(f"{date},{amount:.2f},{desc}")

    csv_content = "\n".join(csv_lines)

    if filename:
        with open(filename, 'w') as f:
            f.write(csv_content)

    return csv_content


# ============= TEST SUITE =============

def run_tests():
    """Run basic unit tests to verify functionality."""
    print("🧪 Running tests...\n")

    # Test 1: Deposit and balance
    food = Category("Food")
    food.deposit(100, "initial")
    assert food.get_balance() == 100.0, "❌ Deposit test failed"
    print("✅ Deposit and balance test passed")

    # Test 2: Withdraw with sufficient funds
    success = food.withdraw(30, "groceries")
    assert success == True, "❌ Withdraw success test failed"
    assert food.get_balance() == 70.0, "❌ Balance after withdraw failed"
    print("✅ Withdraw with sufficient funds test passed")

    # Test 3: Withdraw with insufficient funds
    success = food.withdraw(100, "overspend")
    assert success == False, "❌ Withdraw failure test failed"
    assert food.get_balance() == 70.0, "❌ Balance should not change on failed withdraw"
    print("✅ Withdraw with insufficient funds test passed")

    # Test 4: Transfer between categories
    entertainment = Category("Entertainment")
    entertainment.deposit(50)
    assert food.transfer(20, entertainment) == True, "❌ Transfer success test failed"
    assert food.get_balance() == 50.0, "❌ Food balance after transfer failed"
    assert entertainment.get_balance() == 70.0, "❌ Entertainment balance after transfer failed"
    print("✅ Transfer test passed")

    # Test 5: Check ledger descriptions for transfers
    transfer_descriptions = [item['description'] for item in food.ledger if 'Transfer' in item['description']]
    assert any("Transfer to Entertainment" in desc for desc in
               transfer_descriptions), "❌ Transfer description in source failed"
    print("✅ Transfer description test passed")

    # Test 6: Input validation
    try:
        food.deposit(-10, "invalid")
        assert False, "❌ Should have raised ValueError for negative deposit"
    except ValueError:
        print("✅ Negative deposit validation test passed")

    # Test 7: create_spend_chart with sample data
    auto = Category("Auto")
    auto.deposit(1000)
    auto.withdraw(300, "gas")
    auto.withdraw(200, "maintenance")

    chart = create_spend_chart([food, entertainment, auto])
    assert "Percentage spent by category" in chart, "❌ Chart title missing"
    assert "Food" in chart and "Entertainment" in chart and "Auto" in chart, "❌ Category names missing from chart"
    print("✅ Spend chart generation test passed")

    # Test 8: Empty categories list
    empty_chart = create_spend_chart([])
    assert empty_chart == "Percentage spent by category\n", "❌ Empty chart handling failed"
    print("✅ Empty categories chart test passed")

    print("\n🎉 All tests passed!")


# ============= DEMO / USAGE EXAMPLE =============

if __name__ == "__main__":
    # Create categories
    food = Category("Food")
    entertainment = Category("Entertainment")
    auto = Category("Auto")

    # Add transactions
    food.deposit(900, "deposit")
    food.deposit(45.56, "bonus")
    food.withdraw(34.06, "groceries")
    food.withdraw(21.89, "restaurant")

    entertainment.deposit(200, "initial")
    entertainment.withdraw(50, "movies")
    entertainment.withdraw(30, "concert")

    auto.deposit(500, "initial")
    auto.withdraw(150, "gas")
    auto.withdraw(75.50, "oil change")

    # Transfer between categories
    food.transfer(50, entertainment)

    # Print individual category ledgers
    print(food)
    print("\n" + "=" * 30 + "\n")
    print(entertainment)
    print("\n" + "=" * 30 + "\n")
    print(auto)

    # Print spend chart
    print("\n" + "=" * 30 + "\n")
    print(create_spend_chart([food, entertainment, auto]))

    # Run tests (uncomment to execute)
    # run_tests()

    # Export to CSV example
    # csv_output = export_to_csv(food, "food_ledger.csv")
    # print(csv_output)