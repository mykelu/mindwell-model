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
mh_model = st.sidebar.selectbox(
    "Clinician Pay Structure",
    options=
)
mh_sessions = st.sidebar.slider("Avg. Sessions per Month", 0, 500, 130)
mh_price = st.sidebar.number_input("Avg. Session Price (PHP)", value=3500)

# 2. Primary Care (YAKAP) Pillar
st.sidebar.subheader("Primary Care (YAKAP)")
yakap_model = st.sidebar.selectbox(
    "YAKAP Operating Model",
    options=
)
yakap_patients = st.sidebar.slider("Empaneled Patients", 0, 5000, 800)
careclub_adoption = st.sidebar.slider("CareClub (₱900 Co-pay) Adoption %", 0, 100, 50)

# 3. Financial & Debt Structure
st.sidebar.subheader("Debt & Liquidity")
is_refinanced = st.sidebar.checkbox("Apply ₱3M Bailout to plug 'Leakage Debt'", value=False)
fixed_opex_reduction = st.sidebar.slider("Fixed OPEX Optimization %", 0, 70, 0)

# --- LOGIC & CALCULATIONS ---

# Monthly Interest Calculation
# Stack: 3M at 2.5%/mo, 1.5M at 30% APR (2.5%/mo), 5M at 8%/yr, 9.4M at 8%/yr
debt_high_interest_monthly = (3000000 * 0.025) + (1500000 * 0.025)
debt_longterm_monthly = (5000000 * 0.08) / 12 
incoming_loan_monthly = (9400000 * 0.08) / 12

if is_refinanced:
    # Retire the 3M high-interest loan as per your budget
    monthly_interest = (1500000 * 0.025) + debt_longterm_monthly + incoming_loan_monthly
else:
    monthly_interest = debt_high_interest_monthly + debt_longterm_monthly + incoming_loan_monthly

# Mental Health Pillar Logic
mh_revenue = mh_sessions * mh_price
if mh_model == "Fixed Salary (Current)":
    mh_gross_margin_pct = 0.20
    mh_clinician_cost = mh_revenue * 0.80
else:
    mh_gross_margin_pct = 0.60
    mh_clinician_cost = mh_revenue * 0.40

# YAKAP Pillar Logic (Capitation: 1700/yr, Co-pay: 900/yr)
if yakap_model == "Internal Operations":
    # 40% Tranche 1 realized monthly + Co-pay
    yakap_revenue = (yakap_patients * 1700 * 0.40 / 12) + (yakap_patients * 900 * (careclub_adoption / 100) / 12)
    yakap_opex = 95000 # Salary: 65k MD + 30k Nurse
    # KPI costs: 50% Labs (925), 30% meds (200)
    yakap_variable_cost = (yakap_patients * (0.50 * 925 + 0.30 * 200)) / 12
else:
    # 30% royalty on the 1,700 capitation, zero operational costs for you
    yakap_revenue = (yakap_patients * 1700 * 0.30) / 12
    yakap_opex = 0
    yakap_variable_cost = 0

# Fixed OPEX (Non-clinical)
base_fixed_opex = 301999 # Derived from March 2026 itemized records [2]
if yakap_patients > 1500:
    base_fixed_opex += 25000 
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
    st.error(f"**CRITICAL:** Monthly burn of ₱{abs(net_cash_flow):,.2f}. Structural intervention required to bridge the PhilHealth lag.")
elif is_refinanced and yakap_model == "Outsourced (Royalty Model)":
    st.success("**OPTIMIZED:** Stabilized core. Model is 'M&A Ready' for platform acquisition.")
else:
    st.warning("**STABLE BUT FRAGILE:** Positive cash flow achieved, but monitor debt service coverage.")

st.info("**Benchmark:** PhilHealth YAKAP capitation is ₱1,700/year with a ₱900/year private co-pay limit.")
