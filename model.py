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
mh_model = st.sidebar.selectbox("Clinician Pay Structure", 
                               )
mh_sessions = st.sidebar.slider("Avg. Sessions per Month", 0, 500, 100)
mh_price = st.sidebar.number_input("Avg. Session Price (PHP)", value=3500)

# 2. Primary Care (YAKAP) Pillar
st.sidebar.subheader("Primary Care (YAKAP)")
yakap_model = st.sidebar.selectbox("YAKAP Operating Model", 
                                  )
yakap_patients = st.sidebar.slider("Empaneled Patients", 0, 5000, 800)
careclub_adoption = st.sidebar.slider("CareClub (₱900 Co-pay) Adoption %", 0, 100, 0)

# 3. Financial & Debt Structure
st.sidebar.subheader("Debt & Liquidity")
is_refinanced = st.sidebar.checkbox("Apply ₱3M Bailout to High-Interest Debt", value=False)
fixed_opex_reduction = st.sidebar.slider("Fixed OPEX Optimization %", 0, 70, 0)

# --- LOGIC & CALCULATIONS ---

# Interest Calculation
debt_3m_rate = 0.025 # 2.5% monthly
debt_1_5m_rate = 0.30 / 12 # 30% APR
debt_long_term_rate = 0.08 / 12 # 8% per annum

if is_refinanced:
    # Retiring 3M and 1.5M debt
    monthly_interest = (14400000 * debt_long_term_rate) # Total 14.4M at 8%
else:
    monthly_interest = (3000000 * debt_3m_rate) + (1500000 * debt_1_5m_rate) + (5000000 * debt_long_term_rate)

# MH Pillar Logic
if mh_model == "Fixed Salary (Current)":
    mh_gross_margin_pct = 0.20
    mh_variable_cost = 0
else:
    mh_gross_margin_pct = 0.60
    mh_variable_cost = 0 # In rev share, the 40% is the cost

mh_revenue = mh_sessions * mh_price
mh_gross_profit = mh_revenue * mh_gross_margin_pct

# YAKAP Pillar Logic
# Tranche 1 (40%) is the only reliable short-term monthly revenue
yakap_capitation_monthly = (yakap_patients * 1700 * 0.40) / 12
yakap_copay_monthly = (yakap_patients * 900 * (careclub_adoption / 100)) / 12

if yakap_model == "Internal Operations":
    yakap_opex = 95000 # MD + Nurse Salary
    yakap_variable_cost = (yakap_patients * 0.5 * 925 / 12) + (yakap_patients * 0.3 * 200 / 12) # Labs/Meds KPI
else:
    # 30% royalty on capitation, 0 expense
    yakap_capitation_monthly = (yakap_patients * 1700 * 0.30) / 12
    yakap_opex = 0
    yakap_variable_cost = 0

# Fixed OPEX
base_fixed_opex = 300999 # Non-clinical staff, Rent, Utilities, Software minus clinical salaries [1]
optimized_fixed_opex = base_fixed_opex * (1 - (fixed_opex_reduction / 100))

# Totals
total_revenue = mh_revenue + yakap_capitation_monthly + yakap_copay_monthly
total_opex = optimized_fixed_opex + yakap_opex + monthly_interest + yakap_variable_cost
net_cash_flow = total_revenue - (mh_revenue * (1 - mh_gross_margin_pct)) - total_opex

# M&A Valuation (Simplified)
annual_ebitda = max(0, net_cash_flow * 12)
valuation_low = annual_ebitda * 4
valuation_high = annual_ebitda * 8

# --- DISPLAY DASHBOARD ---

col1, col2, col3 = st.columns(3)
col1.metric("Monthly Net Cash Flow", f"₱{net_cash_flow:,.2f}", delta=net_cash_flow, delta_color="normal")
col2.metric("Monthly Interest Load", f"₱{monthly_interest:,.2f}", delta_color="inverse")
col3.metric("Est. Enterprise Value", f"₱{valuation_low:,.0f} - ₱{valuation_high:,.0f}")

st.markdown("---")

# Pillar Performance Breakdown
st.subheader("📊 Pillar Performance Breakdown")
pillar_data = {
    "Pillar":,
    "Monthly Revenue": [mh_revenue, yakap_capitation_monthly + yakap_copay_monthly, 0],
    "Monthly Direct Cost": [mh_revenue * (1 - mh_gross_margin_pct), yakap_opex + yakap_variable_cost, optimized_fixed_opex + monthly_interest],
}
df = pd.DataFrame(pillar_data)
st.table(df.style.format({"Monthly Revenue": "₱{:,.2f}", "Monthly Direct Cost": "₱{:,.2f}"}))

# Strategic Insight
st.subheader("💡 Strategic Advisory Insight")
if net_cash_flow < 0:
    st.error(f"**CRITICAL:** The business is burning ₱{abs(net_cash_flow):,.2f} per month. Refinancing or Outsourcing is required to close the 'Liquidity Valley'.")
elif is_refinanced and yakap_model == "Outsourced (30% Royalty)":
    st.success("**OPTIMIZED:** You have stabilized the core. This model is 'M&A Ready' for a platform acquisition.")
else:
    st.warning("**STABLE BUT FRAGILE:** Cash flow is positive, but high fixed costs remain a risk if patient volume drops.")

st.info("**Expert Note:** The ₱900 CareClub fee adds ₱" + f"{yakap_copay_monthly:,.2f}" + " to your monthly liquidity. This is your most effective tool to bridge the PhilHealth collection lag.")
