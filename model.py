import streamlit as st
import pandas as pd

# Page Configuration
st.set_page_config(page_title="MindWell.PH Strategic Decision Engine", layout="wide")

st.title("MindWell.PH Strategic Decision Engine")
st.markdown("Use the 'knobs' below to test scenarios for Restructuring, Outsourcing, or Investment.")

# --- SIDEBAR: THE KNOBS ---
st.sidebar.header("🕹️ Strategy Knobs")

# 1. Behavioral Health Pillar
st.sidebar.subheader("Mental Health Pillar")
mh_model = st.sidebar.selectbox("Clinician Pay Structure",)
mh_sessions = st.sidebar.slider("Avg. Sessions per Month", 0, 500, 130)
mh_price = st.sidebar.number_input("Avg. Session Price (PHP)", value=3500)

# 2. Primary Care (YAKAP) Pillar
st.sidebar.subheader("Primary Care (YAKAP)")
yakap_model = st.sidebar.selectbox("YAKAP Operating Model",)
yakap_patients = st.sidebar.slider("Empaneled Patients", 0, 5000, 800)
careclub_adoption = st.sidebar.slider("CareClub (₱900 Co-pay) Adoption %", 0, 100, 50)

# 3. Financial & Debt Structure
st.sidebar.subheader("Debt & Liquidity")
is_refinanced = st.sidebar.checkbox("Apply ₱3M Bailout to 2.5%/mo Debt", value=False)
fixed_opex_reduction = st.sidebar.slider("Fixed OPEX Optimization %", 0, 70, 0)

# --- LOGIC & CALCULATIONS ---

# Interest Calculation (Monthly)
# High interest: 3M at 2.5% monthly, 1.5M at 30% APR (2.5% monthly)
# Long term: 14.4M at 8% per annum
debt_high_interest_monthly = (3000000 * 0.025) + (1500000 * 0.025)
debt_longterm_monthly = (14400000 * 0.08) / 12

if is_refinanced:
    # Retiring the 3M loan at 2.5% monthly interest
    monthly_interest = (1500000 * 0.025) + debt_longterm_monthly
else:
    monthly_interest = debt_high_interest_monthly + debt_longterm_monthly

# MH Pillar Logic
mh_revenue = mh_sessions * mh_price
if mh_model == "Fixed Salary (Current)":
    mh_gross_margin_pct = 0.20
    mh_clinician_cost = mh_revenue * 0.80
else:
    mh_gross_margin_pct = 0.60
    mh_clinician_cost = mh_revenue * 0.40 # Clinicians get 40% share

# YAKAP Pillar Logic
# Capitation is 1,700 PHP per year
# Co-pay is 900 PHP per year [1, 2]
if yakap_model == "Internal Operations":
    # Cash flow assumes 40% Tranche 1 is realized monthly 
    yakap_revenue = (yakap_patients * 1700 * 0.40 / 12) + (yakap_patients * 900 * (careclub_adoption / 100) / 12)
    yakap_opex = 95000 # Salaries for Primary Care MD and Nurse
    # KPI costs: 50% need Labs (925 avg), 30% need meds (200)
    yakap_variable_cost = (yakap_patients * (0.50 * 925 + 0.30 * 200)) / 12
else:
    # 30% royalty on the full 1700 capitation, zero operational costs
    yakap_revenue = (yakap_patients * 1700 * 0.30) / 12
    yakap_opex = 0
    yakap_variable_cost = 0

# Fixed OPEX (Non-clinical)
base_fixed_opex = 301999 # Based on March 2026 data minus clinical salaries 
if yakap_patients > 1500:
    base_fixed_opex += 25000 # Step cost for second Admin hire
optimized_fixed_opex = base_fixed_opex * (1 - (fixed_opex_reduction / 100))

# Totals
total_revenue = mh_revenue + yakap_revenue
total_direct_cost = mh_clinician_cost + yakap_variable_cost
total_fixed_costs = optimized_fixed_opex + yakap_opex + monthly_interest
net_cash_flow = total_revenue - total_direct_cost - total_fixed_costs

# M&A Valuation (Simplified)
annual_ebitda = max(0, net_cash_flow * 12)
valuation_low = annual_ebitda * 4
valuation_high = annual_ebitda * 8

# --- DISPLAY DASHBOARD ---
col1, col2, col3 = st.columns(3)
col1.metric("Monthly Net Cash Flow", f"₱{net_cash_flow:,.2f}")
col2.metric("Monthly Interest Load", f"₱{monthly_interest:,.2f}")
col3.metric("Est. Enterprise Value", f"₱{valuation_low:,.0f} - ₱{valuation_high:,.0f}")

st.markdown("---")

# Pillar Performance Breakdown
st.subheader("📊 Monthly Pillar Performance Breakdown")
pillar_data = {
    "Pillar":,
    "Monthly Revenue": [mh_revenue, yakap_revenue, 0],
    "Monthly Direct Costs": [mh_clinician_cost, yakap_opex + yakap_variable_cost, optimized_fixed_opex + monthly_interest],
}
df = pd.DataFrame(pillar_data)
st.table(df.style.format({"Monthly Revenue": "₱{:,.2f}", "Monthly Direct Costs": "₱{:,.2f}"}))

# Strategic Insight
st.subheader("💡 Strategic Advisory Insight")
if net_cash_flow < 0:
    st.error(f"**CRITICAL:** Monthly burn of ₱{abs(net_cash_flow):,.2f}. The business requires higher utilization or refinancing.")
elif is_refinanced and yakap_model == "Outsourced (30% Royalty)":
    st.success("**OPTIMIZED:** The core is stabilized and 'M&A Ready' for a territory acquisition.")
else:
    st.warning("**STABLE BUT FRAGILE:** Positive cash flow achieved, but monitor patient retention rates.")
