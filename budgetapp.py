import streamlit as st
import json
from datetime import datetime
from typing import List, Dict, Union


# ==========================================
# 1. YOUR ORIGINAL CATEGORY CLASS (Improved)
# ==========================================

class Category:
    def __init__(self, name: str):
        self.name = name
        self.ledger: List[dict] = []
        self._balance: float = 0.0

    def deposit(self, amount: Union[int, float], description: str = "") -> None:
        if not isinstance(amount, (int, float)) or amount < 0:
            raise ValueError("Amount must be a non-negative number")
        self.ledger.append({
            'amount': float(amount),
            'description': description,
            'date': datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        self._balance += float(amount)

    def withdraw(self, amount: Union[int, float], description: str = "") -> bool:
        if not isinstance(amount, (int, float)) or amount < 0:
            return False
        if self.check_funds(amount):
            self.ledger.append({
                'amount': -float(amount),
                'description': description,
                'date': datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            self._balance -= float(amount)
            return True
        return False

    def get_balance(self) -> float:
        return self._balance

    def transfer(self, amount: Union[int, float], category: 'Category') -> bool:
        if self.check_funds(amount):
            self.withdraw(amount, f"Transfer to {category.name}")
            category.deposit(amount, f"Transfer from {self.name}")
            return True
        return False

    def check_funds(self, amount: Union[int, float]) -> bool:
        return amount <= self.get_balance()

    def to_dict(self) -> dict:
        """Serialize category for JSON saving"""
        return {'name': self.name, 'ledger': self.ledger, '_balance': self._balance}

    @classmethod
    def from_dict(cls, data: dict) -> 'Category':
        """Deserialize category from JSON"""
        cat = cls(data['name'])
        cat.ledger = data['ledger']
        cat._balance = data['_balance']
        return cat


# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================

def create_spend_chart(categories: List[Category]) -> str:
    """Original ASCII chart function"""
    if not categories:
        return "No categories to display."

    spends = [sum(abs(item['amount']) for item in cat.ledger if item['amount'] < 0) for cat in categories]
    total_spend = sum(spends)
    percentages = [int((s / total_spend) * 100 // 10) * 10 if total_spend > 0 else 0 for s in spends]

    chart = "Percentage spent by category\n"
    for i in range(100, -1, -10):
        label = str(i).rjust(3) + "| "
        row = label
        for pct in percentages:
            row += "o  " if pct >= i else "   "
        chart += row + "\n"

    chart += "    " + "-" * (len(categories) * 3 + 1) + "\n"
    max_len = max(len(cat.name) for cat in categories)
    for i in range(max_len):
        row = "     "
        for cat in categories:
            row += (cat.name[i] if i < len(cat.name) else " ") + "  "
        chart += row + "\n"
    return chart


def save_data(categories: Dict[str, Category]) -> None:
    """Save categories to JSON file"""
    data = {name: cat.to_dict() for name, cat in categories.items()}
    with open("budget_data.json", "w") as f:
        json.dump(data, f, indent=2)


def load_data() -> Dict[str, Category]:
    """Load categories from JSON file"""
    try:
        with open("budget_data.json", "r") as f:
            data = json.load(f)
        return {name: Category.from_dict(cat_data) for name, cat_data in data.items()}
    except FileNotFoundError:
        return {}


# ==========================================
# 3. STREAMLIT UI
# ==========================================

st.set_page_config(page_title="Budget App", page_icon="💰")
st.title("💰 Personal Budget App")

# Initialize Session State
if 'categories' not in st.session_state:
    st.session_state.categories = load_data()  # Load from JSON on start

# Sidebar Navigation
menu = st.sidebar.selectbox("Menu", ["Dashboard", "Add Category", "Add Transaction", "View Reports", "Save/Load Data"])

# --- DASHBOARD ---
if menu == "Dashboard":
    st.header("Overview")
    if not st.session_state.categories:
        st.info("No categories yet. Go to 'Add Category' to start!")
    else:
        cols = st.columns(len(st.session_state.categories))
        for idx, (name, cat) in enumerate(st.session_state.categories.items()):
            with cols[idx % len(cols)]:
                st.metric(label=name, value=f"${cat.get_balance():.2f}")

        # Show recent transactions across all categories
        st.subheader("Recent Transactions")
        all_transactions = []
        for cat in st.session_state.categories.values():
            for item in cat.ledger[-5:]:  # Last 5 transactions
                all_transactions.append({
                    "Category": cat.name,
                    "Description": item['description'],
                    "Amount": item['amount'],
                    "Date": item.get('date', 'N/A')
                })
        if all_transactions:
            st.dataframe(all_transactions, use_container_width=True)

# --- ADD CATEGORY ---
elif menu == "Add Category":
    st.header("Create New Category")
    new_cat_name = st.text_input("Category Name (e.g., Food, Rent)")
    if st.button("Create Category"):
        if new_cat_name and new_cat_name not in st.session_state.categories:
            st.session_state.categories[new_cat_name] = Category(new_cat_name)
            st.success(f"Category '{new_cat_name}' created!")
            st.rerun()
        elif new_cat_name in st.session_state.categories:
            st.error("Category already exists!")
        else:
            st.error("Please enter a name.")

# --- ADD TRANSACTION ---
elif menu == "Add Transaction":
    st.header("Add Transaction")
    if not st.session_state.categories:
        st.warning("Please create a category first.")
    else:
        cat_names = list(st.session_state.categories.keys())
        selected_cat = st.selectbox("Select Category", cat_names)

        tab1, tab2 = st.tabs(["Deposit", "Withdraw"])

        with tab1:
            dep_amount = st.number_input("Amount", min_value=0.0, step=0.01, key="dep")
            dep_desc = st.text_input("Description", key="dep_desc")
            if st.button("Deposit"):
                st.session_state.categories[selected_cat].deposit(dep_amount, dep_desc)
                st.success(f"Deposited ${dep_amount:.2f} to {selected_cat}")
                st.rerun()

        with tab2:
            wd_amount = st.number_input("Amount", min_value=0.0, step=0.01, key="wd")
            wd_desc = st.text_input("Description", key="wd_desc")
            if st.button("Withdraw"):
                success = st.session_state.categories[selected_cat].withdraw(wd_amount, wd_desc)
                if success:
                    st.success(f"Withdrew ${wd_amount:.2f} from {selected_cat}")
                    st.rerun()
                else:
                    st.error("Insufficient funds!")

# --- VIEW REPORTS ---
elif menu == "View Reports":
    st.header("Reports")
    if not st.session_state.categories:
        st.info("No data available.")
    else:
        # Ledger View
        selected_cat = st.selectbox("View Ledger for", list(st.session_state.categories.keys()))
        cat = st.session_state.categories[selected_cat]

        st.subheader(f"{selected_cat} Ledger")
        if cat.ledger:
            st.dataframe(cat.ledger, use_container_width=True)
            st.metric("Current Balance", f"${cat.get_balance():.2f}")
        else:
            st.write("No transactions yet.")

        st.divider()

        # ASCII Chart View
        st.subheader("Spending Chart (ASCII)")
        chart_data = create_spend_chart(list(st.session_state.categories.values()))
        st.code(chart_data, language="text")

# --- SAVE/LOAD ---
elif menu == "Save/Load Data":
    st.header("Data Management")
    st.write("Streamlit resets memory on refresh. Save your data to keep it!")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save to JSON"):
            save_data(st.session_state.categories)
            st.success("Data saved to budget_data.json")
    with col2:
        if st.button("📂 Load from JSON"):
            st.session_state.categories = load_data()
            st.success("Data loaded!")
            st.rerun()

    if st.button("🗑️ Reset All Data"):
        st.session_state.categories = {}
        st.success("All data cleared.")
        st.rerun()