import streamlit as st
import pandas as pd

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="MindWell.PH Strategic Decision Engine",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🏥 MindWell.PH Strategic Decision Engine")
st.markdown(
    "Use the **'knobs'** below to test scenarios for Restructuring, Outsourcing, or Investment."
)

# ============================================================================
# CONSTANTS & CONFIGURATION
# ============================================================================

# Mental Health Pillar Options
MH_MODELS = ["Fixed Salary (Current)", "Commission on Collection"]
MH_MODEL_DEFAULTS = {
    "Fixed Salary (Current)": {"margin": 0.20, "clinician_cost_pct": 0.80},
    "Commission on Collection": {"margin": 0.60, "clinician_cost_pct": 0.40},
}

# YAKAP Pillar Options
YAKAP_MODELS = ["Internal Operations", "Outsourced (Royalty Model)"]

# Debt Configuration (in PHP)
DEBT_CONFIG = {
    "high_interest_3m": {"amount": 3_000_000, "rate_monthly": 0.025},
    "revolving_1_5m": {"amount": 1_500_000, "rate_monthly": 0.025},
    "current_5m": {"amount": 5_000_000, "rate_annual": 0.08},
    "incoming_9_4m": {"amount": 9_400_000, "rate_annual": 0.08},
}

# YAKAP Capitation & Co-pay (Annual)
YAKAP_CAPITATION = 1700
YAKAP_COPAY_ANNUAL = 900
YAKAP_CAPITATION_REALIZATION = 0.40  # 40% Tranche 1

# YAKAP Internal Operations Cost
YAKAP_INTERNAL_OPEX = 95_000  # MD + Nurse salaries
YAKAP_LAB_COST_RATIO = 0.50
YAKAP_LAB_COST_AVG = 925
YAKAP_MED_COST_RATIO = 0.30
YAKAP_MED_COST_AVG = 200

# Fixed OPEX (Non-clinical, from March 2026 data)
BASE_FIXED_OPEX = 301_999
YAKAP_SCALE_THRESHOLD = 1500
YAKAP_SCALE_COST = 25_000

# M&A Valuation Multiples
VALUATION_LOW_MULTIPLE = 4
VALUATION_HIGH_MULTIPLE = 8

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_monthly_interest(is_refinanced: bool) -> float:
    """
    Calculate total monthly interest based on debt stack.
    
    Args:
        is_refinanced: If True, retire the 3M high-interest loan via bailout.
        
    Returns:
        Total monthly interest in PHP.
    """
    high_interest = (
        DEBT_CONFIG["high_interest_3m"]["amount"] * 
        DEBT_CONFIG["high_interest_3m"]["rate_monthly"]
    ) + (
        DEBT_CONFIG["revolving_1_5m"]["amount"] * 
        DEBT_CONFIG["revolving_1_5m"]["rate_monthly"]
    )
    
    longterm = (
        DEBT_CONFIG["current_5m"]["amount"] * 
        DEBT_CONFIG["current_5m"]["rate_annual"]
    ) / 12
    
    incoming = (
        DEBT_CONFIG["incoming_9_4m"]["amount"] * 
        DEBT_CONFIG["incoming_9_4m"]["rate_annual"]
    ) / 12
    
    if is_refinanced:
        # Retire the 3M high-interest loan only; keep revolving line
        return (
            DEBT_CONFIG["revolving_1_5m"]["amount"] * 
            DEBT_CONFIG["revolving_1_5m"]["rate_monthly"]
        ) + longterm + incoming
    else:
        return high_interest + longterm + incoming


def calculate_mh_financials(mh_model: str, mh_sessions: int, mh_price: float) -> dict:
    """
    Calculate Mental Health pillar financials.
    
    Args:
        mh_model: Selected clinician pay structure.
        mh_sessions: Average sessions per month.
        mh_price: Average session price in PHP.
        
    Returns:
        Dictionary with revenue, cost, and margin.
    """
    revenue = mh_sessions * mh_price
    model_config = MH_MODEL_DEFAULTS[mh_model]
    clinician_cost = revenue * model_config["clinician_cost_pct"]
    margin_pct = model_config["margin"]
    
    return {
        "revenue": revenue,
        "clinician_cost": clinician_cost,
        "margin_pct": margin_pct,
    }


def calculate_yakap_financials(
    yakap_model: str,
    yakap_patients: int,
    careclub_adoption: float,
) -> dict:
    """
    Calculate YAKAP (Primary Care) pillar financials.
    
    Args:
        yakap_model: Selected operating model.
        yakap_patients: Number of empaneled patients.
        careclub_adoption: CareClub adoption rate (0-100%).
        
    Returns:
        Dictionary with revenue, opex, and variable cost.
    """
    if yakap_model == "Internal Operations":
        # 40% Tranche 1 realized monthly + Co-pay adoption
        capitation_revenue = (
            yakap_patients * 
            YAKAP_CAPITATION * 
            YAKAP_CAPITATION_REALIZATION / 12
        )
        copay_revenue = (
            yakap_patients * 
            YAKAP_COPAY_ANNUAL * 
            (careclub_adoption / 100) / 12
        )
        revenue = capitation_revenue + copay_revenue
        opex = YAKAP_INTERNAL_OPEX
        variable_cost = (
            yakap_patients * (
                YAKAP_LAB_COST_RATIO * YAKAP_LAB_COST_AVG +
                YAKAP_MED_COST_RATIO * YAKAP_MED_COST_AVG
            )
        ) / 12
    else:
        # 30% royalty on capitation; zero operational costs for MindWell
        revenue = (yakap_patients * YAKAP_CAPITATION * 0.30) / 12
        opex = 0
        variable_cost = 0
    
    return {
        "revenue": revenue,
        "opex": opex,
        "variable_cost": variable_cost,
    }


def calculate_fixed_opex(yakap_patients: int, opex_reduction_pct: float) -> float:
    """
    Calculate optimized fixed OPEX.
    
    Args:
        yakap_patients: Number of empaneled patients.
        opex_reduction_pct: Optimization percentage (0-100%).
        
    Returns:
        Optimized monthly fixed OPEX in PHP.
    """
    base = BASE_FIXED_OPEX
    if yakap_patients > YAKAP_SCALE_THRESHOLD:
        base += YAKAP_SCALE_COST
    
    return base * (1 - (opex_reduction_pct / 100))


def calculate_valuation(net_cash_flow: float) -> dict:
    """
    Calculate M&A enterprise value based on simplified EBITDA multiples.
    
    Args:
        net_cash_flow: Monthly net cash flow.
        
    Returns:
        Dictionary with low and high valuation estimates.
    """
    annual_ebitda = max(0, net_cash_flow * 12)
    return {
        "low": annual_ebitda * VALUATION_LOW_MULTIPLE,
        "high": annual_ebitda * VALUATION_HIGH_MULTIPLE,
    }


# ============================================================================
# SIDEBAR: THE KNOBS
# ============================================================================

st.sidebar.header("🕹️ Strategy Knobs")

# --- Mental Health Pillar ---
st.sidebar.subheader("🧠 Mental Health Pillar")
mh_model = st.sidebar.selectbox(
    "Clinician Pay Structure",
    options=MH_MODELS,
    help="Fixed Salary: Lower margin, stable costs. Commission: Higher margin but variable costs.",
)
mh_sessions = st.sidebar.slider(
    "Avg. Sessions per Month",
    min_value=0,
    max_value=500,
    value=130,
    help="Average number of clinical sessions delivered per month.",
)
mh_price = st.sidebar.number_input(
    "Avg. Session Price (₱)",
    value=3500,
    min_value=0,
    step=100,
    help="Average reimbursement or charge per session.",
)

# --- Primary Care (YAKAP) Pillar ---
st.sidebar.subheader("🏥 Primary Care (YAKAP)")
yakap_model = st.sidebar.selectbox(
    "YAKAP Operating Model",
    options=YAKAP_MODELS,
    help="Internal: Direct margin but requires operational overhead. Outsourced: Lower margin but minimal overhead.",
)
yakap_patients = st.sidebar.slider(
    "Empaneled Patients",
    min_value=0,
    max_value=5000,
    value=800,
    help="Total number of PhilHealth-enrolled patients.",
)
careclub_adoption = st.sidebar.slider(
    "CareClub (₱900/yr Co-pay) Adoption %",
    min_value=0,
    max_value=100,
    value=50,
    help="Percentage of empaneled patients adopting the private co-pay option.",
)

# --- Debt & Liquidity ---
st.sidebar.subheader("💰 Debt & Liquidity")
is_refinanced = st.sidebar.checkbox(
    "Apply ₱3M Bailout to plug 'Leakage Debt'",
    value=False,
    help="If checked, the ₱3M high-interest loan is retired via the bailout.",
)
fixed_opex_reduction = st.sidebar.slider(
    "Fixed OPEX Optimization %",
    min_value=0,
    max_value=70,
    value=0,
    help="Percentage reduction in non-clinical fixed costs (e.g., admin, rent, IT).",
)

# ============================================================================
# CALCULATIONS
# ============================================================================

# Interest Calculation
monthly_interest = calculate_monthly_interest(is_refinanced)

# Mental Health Financials
mh_financials = calculate_mh_financials(mh_model, mh_sessions, mh_price)

# YAKAP Financials
yakap_financials = calculate_yakap_financials(yakap_model, yakap_patients, careclub_adoption)

# Fixed OPEX
optimized_fixed_opex = calculate_fixed_opex(yakap_patients, fixed_opex_reduction)

# Totals
total_revenue = mh_financials["revenue"] + yakap_financials["revenue"]
total_direct_cost = mh_financials["clinician_cost"] + yakap_financials["variable_cost"]
total_fixed_costs = (
    optimized_fixed_opex +
    yakap_financials["opex"] +
    monthly_interest
)
net_cash_flow = total_revenue - total_direct_cost - total_fixed_costs

# Valuation
valuation = calculate_valuation(net_cash_flow)

# ============================================================================
# DISPLAY DASHBOARD
# ============================================================================

# Key Metrics (Top Row)
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(
        "💵 Monthly Net Cash Flow",
        f"₱{net_cash_flow:,.2f}",
        delta=f"Annual: ₱{net_cash_flow * 12:,.0f}",
    )
with col2:
    st.metric(
        "📊 Monthly Interest Load",
        f"₱{monthly_interest:,.2f}",
        delta=f"Annual: ₱{monthly_interest * 12:,.0f}",
    )
with col3:
    st.metric(
        "🎯 Est. Enterprise Value",
        f"₱{valuation['low']:,.0f}",
        delta=f"Range: ₱{valuation['high']:,.0f}",
    )

st.markdown("---")

# Pillar Performance Breakdown
st.subheader("📊 Monthly Pillar Performance Breakdown")
pillar_data = {
    "Pillar": ["Mental Health", "Primary Care (YAKAP)", "Fixed Costs & Interest"],
    "Monthly Revenue": [
        mh_financials["revenue"],
        yakap_financials["revenue"],
        0.0,
    ],
    "Direct Variable Costs": [
        mh_financials["clinician_cost"],
        yakap_financials["variable_cost"],
        0.0,
    ],
    "Fixed / Interest Costs": [
        0.0,
        yakap_financials["opex"],
        optimized_fixed_opex + monthly_interest,
    ],
}
df_pillar = pd.DataFrame(pillar_data)
st.table(
    df_pillar.style.format({
        "Monthly Revenue": "₱{:,.2f}",
        "Direct Variable Costs": "₱{:,.2f}",
        "Fixed / Interest Costs": "₱{:,.2f}",
    })
)

# Detailed Metrics (Second Row)
st.subheader("📈 Detailed Financial Metrics")
col4, col5, col6, col7 = st.columns(4)
with col4:
    st.metric(
        "Mental Health Gross Margin",
        f"{mh_financials['margin_pct'] * 100:.1f}%",
        help=f"Model: {mh_model}",
    )
with col5:
    st.metric(
        "Total Monthly Revenue",
        f"₱{total_revenue:,.2f}",
        delta=f"Annual: ₱{total_revenue * 12:,.0f}",
    )
with col6:
    st.metric(
        "Total Direct Costs",
        f"₱{total_direct_cost:,.2f}",
        help="Clinician costs + variable operational costs",
    )
with col7:
    st.metric(
        "Debt Refinanced",
        "✅ Yes" if is_refinanced else "❌ No",
        help="Status of ₱3M high-interest loan bailout",
    )

st.markdown("---")

# Strategic Advisory
st.subheader("💡 Strategic Advisory Insight")

if net_cash_flow < 0:
    st.error(
        f"""
        **🚨 CRITICAL:** Monthly burn of **₱{abs(net_cash_flow):,.2f}**
        
        The business model is **fragile**. Restructuring is urgently required to:
        - Bridge the PhilHealth capitation lag
        - Reduce fixed costs or increase patient volumes
        - Consider outsourcing YAKAP if internal operations are unprofitable
        """
    )
elif is_refinanced and yakap_model == "Outsourced (Royalty Model)":
    st.success(
        f"""
        **✅ OPTIMIZED:** Monthly cash flow of **₱{net_cash_flow:,.2f}**
        
        **Your core is stabilized and 'M&A Ready'!**
        - The ₱3M bailout successfully retired high-interest debt
        - Outsourced YAKAP minimizes overhead while capturing margin
        - Enterprise value estimated at **₱{valuation['low']:,.0f} - ₱{valuation['high']:,.0f}**
        """
    )
else:
    st.warning(
        f"""
        **⚠️ STABLE BUT FRAGILE:** Monthly cash flow of **₱{net_cash_flow:,.2f}**
        
        Positive cash flow achieved, but:
        - Monitor your **interest-coverage ratio** (should be > 1.5x)
        - Consider OPEX optimization or patient scaling
        - Interest payments are eating into profitability
        """
    )

st.divider()

st.info(
    """
    **📌 Model Assumptions:**
    - **YAKAP Capitation:** ₱1,700/year per patient (40% Tranche 1 realized monthly)
    - **CareClub Co-pay:** ₱900/year annual limit for private clinics
    - **Mental Health:** Session-based pricing with fixed or commission-based clinician costs
    - **Debt Stack:** ₱3M (2.5%/mo) + ₱1.5M (2.5%/mo) + ₱5M (8%/yr) + ₱9.4M incoming (8%/yr)
    - **Fixed OPEX:** ₱301,999/mo (March 2026 baseline) + ₱25K scaling step at 1,500+ patients
    """
)
