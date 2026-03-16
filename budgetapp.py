import streamlit as st
import json
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from typing import List, Dict, Union
import os

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
        return {'name': self.name, 'ledger': self.ledger, '_balance': self._balance}

    @classmethod
    def from_dict(cls, data: dict) -> 'Category':
        cat = cls(data['name'])
        cat.ledger = data['ledger']
        cat._balance = data['_balance']
        return cat

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
    data = {name: cat.to_dict() for name, cat in categories.items()}
    with open("budget_data.json", "w") as f:
        json.dump(data, f, indent=2)


def load_data() -> Dict[str, Category]:
    try:
        with open("budget_data.json", "r") as f:
            data = json.load(f)
        return {name: Category.from_dict(cat_data) for name, cat_data in data.items()}
    except FileNotFoundError:
        return {}

st.set_page_config(
    page_title="Budget App",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    @media (max-width: 768px) {
        .stMetric {
            background-color: #f0f2f6;
            padding: 10px;
            border-radius: 10px;
            margin: 5px 0;
        }
        .stButton > button {
            width: 100%;
            margin: 5px 0;
        }
    }
    .stMetric {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

st.title("💰 Budget App")

if 'categories' not in st.session_state:
    st.session_state.categories = load_data()

with st.sidebar:
    st.header("☰ Menu")
    menu = st.radio(
        "Navigation",
        ["Dashboard", "Add Category", "Add Transaction", "View Reports", "Save/Load Data"],
        label_visibility="collapsed"
    )
    st.divider()
    st.caption(f"📱 {len(st.session_state.categories)} categories")

if menu == "Dashboard":
    st.header("📊 Dashboard")

    if not st.session_state.categories:
        st.info("👆 Tap menu to add your first category!")
    else:
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()

        with st.expander("📅 Filter by Date Range", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("From", value=start_date)
            with col2:
                end_date = st.date_input("To", value=end_date)
            st.button("Apply Filter", use_container_width=True)

        total_balance = sum(cat.get_balance() for cat in st.session_state.categories.values())

        total_spent = 0
        total_deposited = 0
        for cat in st.session_state.categories.values():
            for item in cat.ledger:
                try:
                    trans_date = datetime.strptime(item['date'], "%Y-%m-%d %H:%M")
                    if start_date <= trans_date <= end_date:
                        if item['amount'] < 0:
                            total_spent += abs(item['amount'])
                        else:
                            total_deposited += item['amount']
                except:
                    pass

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("💵 Balance", f"${total_balance:,.0f}")
        with col2:
            st.metric("📥 Deposited", f"${total_deposited:,.0f}")
        with col3:
            st.metric("📤 Spent", f"${total_spent:,.0f}")

        st.divider()

        st.subheader("📁 Categories")
        for name, cat in st.session_state.categories.items():
            with st.container():
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"**{name}**")
                with col2:
                    st.write(f"${cat.get_balance():,.2f}")
                st.divider()

        st.subheader("📝 Recent Activity")
        all_transactions = []
        for cat in st.session_state.categories.values():
            for item in cat.ledger[-5:]:
                try:
                    trans_date = datetime.strptime(item['date'], "%Y-%m-%d %H:%M")
                    if start_date <= trans_date <= end_date:
                        all_transactions.append({
                            "Category": cat.name,
                            "Description": item['description'],
                            "Amount": item['amount'],
                            "Date": item.get('date', 'N/A')[:10]
                        })
                except:
                    all_transactions.append({
                        "Category": cat.name,
                        "Description": item['description'],
                        "Amount": item['amount'],
                        "Date": item.get('date', 'N/A')[:10]
                    })

        if all_transactions:
            df = pd.DataFrame(all_transactions)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.write("No transactions in this period.")

elif menu == "Add Category":
    st.header("📁 New Category")

    new_cat_name = st.text_input("Category Name", placeholder="e.g., Food, Rent")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Create", use_container_width=True, type="primary"):
            if new_cat_name and new_cat_name not in st.session_state.categories:
                st.session_state.categories[new_cat_name] = Category(new_cat_name)
                st.success(f"Created '{new_cat_name}'!")
                st.rerun()
            elif new_cat_name in st.session_state.categories:
                st.error("Already exists!")
            else:
                st.error("Enter a name")

    with col2:
        if st.button("🗑️ Clear", use_container_width=True):
            st.rerun()

    if st.session_state.categories:
        st.divider()
        st.subheader("Existing Categories")
        for name in st.session_state.categories.keys():
            st.write(f"• {name}")

elif menu == "Add Transaction":
    st.header("💸 Transaction")

    if not st.session_state.categories:
        st.warning("Create a category first!")
    else:
        cat_names = list(st.session_state.categories.keys())
        selected_cat = st.selectbox("Category", cat_names)

        current_balance = st.session_state.categories[selected_cat].get_balance()
        st.info(f"💵 Balance: ${current_balance:,.2f}")

        tab1, tab2, tab3 = st.tabs(["💰 Deposit", "💸 Withdraw", "🔄 Transfer"])

        with tab1:
            dep_amount = st.number_input("Amount", min_value=0.0, step=0.01, key="dep")
            dep_desc = st.text_input("Description", placeholder="e.g., Salary", key="dep_desc")
            if st.button("Deposit", use_container_width=True, type="primary"):
                if dep_amount > 0:
                    st.session_state.categories[selected_cat].deposit(dep_amount, dep_desc)
                    st.success(f"✅ +${dep_amount:,.2f}")
                    st.rerun()

        with tab2:
            wd_amount = st.number_input("Amount", min_value=0.0, step=0.01, key="wd")
            wd_desc = st.text_input("Description", placeholder="e.g., Groceries", key="wd_desc")
            if st.button("Withdraw", use_container_width=True, type="primary"):
                if wd_amount > 0:
                    success = st.session_state.categories[selected_cat].withdraw(wd_amount, wd_desc)
                    if success:
                        st.success(f"✅ -${wd_amount:,.2f}")
                        st.rerun()
                    else:
                        st.error("❌ Insufficient funds!")

        with tab3:
            transfer_amount = st.number_input("Amount", min_value=0.0, step=0.01, key="transfer")
            target_cats = [c for c in cat_names if c != selected_cat]
            if target_cats:
                target_cat = st.selectbox("To", target_cats)
                if st.button("Transfer", use_container_width=True, type="primary"):
                    if transfer_amount > 0:
                        success = st.session_state.categories[selected_cat].transfer(
                            transfer_amount,
                            st.session_state.categories[target_cat]
                        )
                        if success:
                            st.success(f"✅ Transferred ${transfer_amount:,.2f}")
                            st.rerun()
                        else:
                            st.error("❌ Insufficient funds!")
            else:
                st.info("Need 2+ categories for transfers")

elif menu == "View Reports":
    st.header("📈 Reports")

    if not st.session_state.categories:
        st.info("No data yet!")
    else:
        st.subheader("📅 Date Range")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("From", value=datetime.now() - timedelta(days=30))
        with col2:
            end_date = st.date_input("To", value=datetime.now())

        preset_cols = st.columns(4)
        with preset_cols[0]:
            if st.button("7 Days", use_container_width=True, key="p7"):
                start_date = datetime.now() - timedelta(days=7)
        with preset_cols[1]:
            if st.button("30 Days", use_container_width=True, key="p30"):
                start_date = datetime.now() - timedelta(days=30)
        with preset_cols[2]:
            if st.button("90 Days", use_container_width=True, key="p90"):
                start_date = datetime.now() - timedelta(days=90)
        with preset_cols[3]:
            if st.button("All Time", use_container_width=True, key="pall"):
                start_date = datetime(2000, 1, 1)

        st.divider()

        spending_data = {}
        for name, cat in st.session_state.categories.items():
            spent = 0
            for item in cat.ledger:
                if item['amount'] < 0:
                    try:
                        trans_date = datetime.strptime(item['date'], "%Y-%m-%d %H:%M")
                        if start_date <= trans_date <= end_date:
                            spent += abs(item['amount'])
                    except:
                        spent += abs(item['amount'])
            spending_data[name] = spent

        df_spending = pd.DataFrame(list(spending_data.items()), columns=['Category', 'Amount Spent'])
        has_spending = df_spending['Amount Spent'].sum() > 0

        chart_type = st.radio("Chart Type", ["Bar", "Pie", "Donut", "ASCII"], horizontal=True)

        if not has_spending:
            st.info("💡 No spending in this period")
        else:
            if chart_type == "Bar":
                fig = px.bar(df_spending, x='Category', y='Amount Spent', color='Category', text='Amount Spent')
                fig.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
                fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=40, b=0))
                st.plotly_chart(fig, use_container_width=True)

            elif chart_type == "Pie":
                fig = px.pie(df_spending, values='Amount Spent', names='Category', hole=0)
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(margin=dict(l=0, r=0, t=40, b=0))
                st.plotly_chart(fig, use_container_width=True)

            elif chart_type == "Donut":
                fig = px.pie(df_spending, values='Amount Spent', names='Category', hole=0.4)
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(margin=dict(l=0, r=0, t=40, b=0))
                st.plotly_chart(fig, use_container_width=True)

            else:
                st.code(create_spend_chart(list(st.session_state.categories.values())), language="text")

        if has_spending:
            st.divider()
            st.subheader("💡 Insights")
            total = df_spending['Amount Spent'].sum()
            max_spender = df_spending.loc[df_spending['Amount Spent'].idxmax()]

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Spent", f"${total:,.2f}")
            with col2:
                st.metric("Top Category", max_spender['Category'], f"${max_spender['Amount Spent']:,.2f}")

            with st.expander("📊 Detailed Breakdown"):
                for _, row in df_spending.iterrows():
                    pct = (row['Amount Spent'] / total) * 100
                    st.write(f"- **{row['Category']}**: {pct:.1f}% (${row['Amount Spent']:,.2f})")

        st.divider()
        st.subheader("📄 Ledger")
        selected_cat = st.selectbox("Select Category", list(st.session_state.categories.keys()))
        cat = st.session_state.categories[selected_cat]

        if cat.ledger:
            filtered_ledger = []
            for item in cat.ledger:
                try:
                    trans_date = datetime.strptime(item['date'], "%Y-%m-%d %H:%M")
                    if start_date <= trans_date <= end_date:
                        filtered_ledger.append(item)
                except:
                    filtered_ledger.append(item)

            if filtered_ledger:
                df_ledger = pd.DataFrame(filtered_ledger)
                st.dataframe(df_ledger, use_container_width=True, hide_index=True)
                st.metric("Balance", f"${cat.get_balance():,.2f}")
            else:
                st.write("No transactions in this period.")

elif menu == "Save/Load Data":
    st.header("💾 Data")

    st.write("Save your data to keep it after refresh!")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("💾 Save", use_container_width=True, type="primary"):
            save_data(st.session_state.categories)
            st.success("✅ Saved!")
    with col2:
        if st.button("📂 Load", use_container_width=True):
            st.session_state.categories = load_data()
            st.success("✅ Loaded!")
            st.rerun()
    with col3:
        if st.button("🗑️ Reset", type="error", use_container_width=True):
            st.session_state.categories = {}
            st.success("✅ Reset!")
            st.rerun()

    if os.path.exists("budget_data.json"):
        file_size = os.path.getsize("budget_data.json")
        st.info(f"📁 Saved to `budget_data.json` ({file_size} bytes)")

st.divider()
st.caption("💰 Budget App • Made with Streamlit")