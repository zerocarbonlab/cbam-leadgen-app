import pandas as pd
import streamlit as st
from urllib.parse import urlencode

st.set_page_config(
    page_title="CBAM Calculator for EU Imports",
    page_icon="🌿",
    layout="wide"
)

DATA_FILE = "webapp_master_lookup.csv"

# --------------------------------
# Replace these 2 values only
# --------------------------------
TALLY_FORM_URL = "https://tally.so/r/REPLACE_WITH_YOUR_TALLY_FORM_ID"
CONTACT_EMAIL = "zerocarbonlab@gmail.com"

# --------------------------------
# Styling
# --------------------------------
CUSTOM_CSS = """
<style>
    .stApp {
        background: #f7faf8;
    }
    .block-container {
        max-width: 1020px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    h1, h2, h3 {
        color: #1f2f2b;
        letter-spacing: -0.02em;
    }
    .hero-card, .section-card, .result-card, .cta-card {
        border: 1px solid #e4ece8;
        background: #ffffff;
        border-radius: 18px;
        padding: 1.2rem 1.25rem;
        box-shadow: 0 8px 24px rgba(25, 40, 35, 0.04);
    }
    .hero-card {
        background: linear-gradient(180deg, #f5fbf8 0%, #ffffff 100%);
        border-color: #dcebe4;
    }
    .cta-card {
        background: linear-gradient(180deg, #f7fbf9 0%, #ffffff 100%);
        border-color: #d7e7df;
    }
    .subtle {
        color: #61736f;
        font-size: 1rem;
        line-height: 1.6;
        margin-top: 0.2rem;
        margin-bottom: 0.8rem;
    }
    .small-note {
        color: #71827d;
        font-size: 0.92rem;
        line-height: 1.55;
    }
    .pill {
        display: inline-block;
        padding: 0.28rem 0.68rem;
        border-radius: 999px;
        background: #edf6f1;
        color: #2a6757;
        font-size: 0.83rem;
        margin-right: 0.45rem;
        margin-bottom: 0.4rem;
    }
    .metric-label {
        color: #73837f;
        font-size: 0.92rem;
        margin-bottom: 0.28rem;
    }
    .metric-value {
        color: #1f2d2a;
        font-size: 2rem;
        font-weight: 700;
        line-height: 1.1;
    }
    .trust-box {
        border-left: 4px solid #7db49c;
        background: #f8fcfa;
        padding: 0.95rem 1rem;
        border-radius: 10px;
        color: #41524e;
        margin-top: 0.8rem;
    }
    .footer-note {
        color: #6f817b;
        font-size: 0.95rem;
        line-height: 1.65;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# --------------------------------
# Helpers
# --------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_FILE, dtype=str)

    numeric_cols = [
        "calculator_direct_factor_tco2e_per_ton",
        "calculator_indirect_factor_tco2e_per_ton",
        "calculator_total_factor_tco2e_per_ton",
        "direct_emission_factor_tco2e_per_ton",
        "indirect_emission_factor_tco2e_per_ton",
        "total_emission_factor_tco2e_per_ton",
        "2026_default_value_including_markup",
        "2027_default_value_including_markup",
        "2028_onwards_default_value_including_markup",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "display_name" in df.columns:
        df["product_name_final"] = df["display_name"]
    elif "product_display_name" in df.columns:
        df["product_name_final"] = df["product_display_name"]
    else:
        df["product_name_final"] = ""

    if "country" not in df.columns and "origin_country_assumed" in df.columns:
        df["country"] = df["origin_country_assumed"]

    if "calculator_direct_factor_tco2e_per_ton" in df.columns:
        df["direct_factor_final"] = df["calculator_direct_factor_tco2e_per_ton"]
    else:
        df["direct_factor_final"] = pd.to_numeric(
            df.get("direct_emission_factor_tco2e_per_ton"), errors="coerce"
        )

    defaults = {
        "lookup_display_message": "",
        "user_action_hint": "",
        "calculator_ready_flag": "",
        "factor_status": "",
        "definitive_period_primary_focus": "",
        "aggregated_goods_category": "",
        "hs_code_prefix": "",
    }
    for key, value in defaults.items():
        if key not in df.columns:
            df[key] = value

    if "display_hs_code" not in df.columns:
        df["display_hs_code"] = df["hs_code_prefix"]

    return df

def clean_hs_code(x):
    if x is None:
        return ""
    return "".join(ch for ch in str(x).strip() if ch.isdigit())

def find_matches(df, country, hs_code):
    code = clean_hs_code(hs_code)
    if not code:
        return pd.DataFrame()

    subset = df[df["country"] == country].copy()

    exact = subset[subset["hs_code_prefix"] == code].copy()
    if not exact.empty:
        return exact

    starts = subset[subset["hs_code_prefix"].fillna("").str.startswith(code)].copy()
    return starts.sort_values(["hs_code_prefix", "product_name_final"])

def build_tally_url(
    base_url: str,
    *,
    help_type: str = "",
    company_name: str = "",
    country: str = "",
    hs_code: str = "",
    product_description: str = "",
    quantity: str = "",
    source: str = "cbam_calculator",
    estimated_emissions: str = ""
):
    params = {
        "help_type": help_type,
        "company_name": company_name,
        "country": country,
        "hs_code": hs_code,
        "product_description": product_description,
        "quantity": quantity,
        "source": source,
        "estimated_emissions": estimated_emissions,
    }
    params = {k: v for k, v in params.items() if str(v).strip() != ""}
    if not params:
        return base_url
    return f"{base_url}?{urlencode(params)}"

df = load_data()

# --------------------------------
# Hero
# --------------------------------
st.markdown('<div class="hero-card">', unsafe_allow_html=True)
st.title("Free CBAM Calculator for EU Imports")
st.markdown(
    '<div class="subtle">'
    'Estimate CBAM default-value emissions for iron and steel imports in under a minute. '
    'Use this tool for fast screening, then request a more accurate report by email if needed.'
    '</div>',
    unsafe_allow_html=True
)
st.markdown(
    '<span class="pill">Fast screening estimate</span>'
    '<span class="pill">Built for EU import workflows</span>'
    '<span class="pill">Email-based follow-up, no call required</span>',
    unsafe_allow_html=True
)
st.markdown(
    """
    <div class="trust-box">
    <strong>Who this is for:</strong> exporters, traders, importers, and compliance teams that need a quick CBAM screening result before deeper reporting work.
    </div>
    """,
    unsafe_allow_html=True
)
st.markdown('</div>', unsafe_allow_html=True)

st.write("")

# --------------------------------
# Top CTA
# --------------------------------
top_tally_url = build_tally_url(
    TALLY_FORM_URL,
    help_type="More accurate CBAM estimate",
    source="hero_cta"
)

st.markdown('<div class="cta-card">', unsafe_allow_html=True)
st.markdown("### Need more than a screening estimate?")
st.markdown(
    "This free tool is designed for quick default-value checks. "
    "If you need supplier-specific support, HS code review, methodology guidance, or a more decision-ready estimate, "
    "leave your details and we’ll follow up by email."
)
c1, c2 = st.columns(2)
with c1:
    st.link_button("Get a more accurate CBAM report", top_tally_url, width="stretch")
with c2:
    st.link_button("Email us directly", f"mailto:{CONTACT_EMAIL}", width="stretch")
st.caption("No call booking needed. Leave your email and we’ll follow up.")
st.markdown('</div>', unsafe_allow_html=True)

st.write("")

# --------------------------------
# What this tool does
# --------------------------------
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown("### What this tool does")
st.markdown(
    """
- Estimates embedded emissions using screening-level CBAM default values  
- Helps you quickly check whether a shipment may need deeper review  
- Gives you a starting point before supplier-specific or reporting-ready work  
    """
)
st.markdown(
    '<div class="small-note">This is a screening tool, not a final compliance submission engine.</div>',
    unsafe_allow_html=True
)
st.markdown('</div>', unsafe_allow_html=True)

st.write("")

# --------------------------------
# Calculator
# --------------------------------
st.markdown("## Start your estimate")

left, right = st.columns([1.2, 1])

with left:
    countries = sorted([c for c in df["country"].dropna().unique() if str(c).strip()])
    default_country_index = countries.index("China") if "China" in countries else 0
    country = st.selectbox(
        "Country of origin",
        countries,
        index=default_country_index if countries else None
    )
    hs_code = st.text_input(
        "HS code",
        placeholder="e.g. 72026000"
    )

with right:
    quantity = st.number_input(
        "Quantity (tonnes)",
        min_value=0.0,
        value=1.0,
        step=1.0
    )
    st.write("")
    calculate = st.button("Estimate CBAM emissions", type="primary", width="stretch")

with st.expander("Methodology, scope, and limitations"):
    st.markdown(
        """
- This tool uses published CBAM default values for **screening-level estimates**
- Default values are useful for fast checks, but may not be sufficient for supplier-specific or reporting-ready work
- Some products require more detailed classification, precursor review, or methodology-based calculation
- Results should be used as an initial estimate, not as a substitute for a complete compliance assessment
        """
    )

# --------------------------------
# Results
# --------------------------------
if calculate:
    matches = find_matches(df, country, hs_code)

    if matches.empty:
        st.error("No matching row found for this country and HS code.")
        st.info("Try a more specific HS code, or request help if you are unsure about classification.")

        no_match_tally_url = build_tally_url(
            TALLY_FORM_URL,
            help_type="HS code or product classification support",
            country=country,
            hs_code=hs_code,
            quantity=str(quantity),
            source="no_match_result"
        )

        st.markdown('<div class="cta-card">', unsafe_allow_html=True)
        st.markdown("### Need help finding the right HS code?")
        st.markdown(
            "A missing match usually means the code needs refinement or the product needs a quick classification review. "
            "Leave your details and we’ll follow up by email."
        )
        st.link_button("Get HS code / classification support", no_match_tally_url, width="stretch")
        st.markdown('</div>', unsafe_allow_html=True)

    else:
        if len(matches) > 1:
            st.info("More than one product description matches this HS code. Select the closest option below.")
            option_labels = [
                f"{row['product_name_final']} | {row.get('aggregated_goods_category','')} | {row.get('hs_code_prefix','')}"
                for _, row in matches.iterrows()
            ]
            selected_label = st.selectbox("Choose the closest matching product", option_labels)
            selected_idx = option_labels.index(selected_label)
            row = matches.iloc[selected_idx]
        else:
            row = matches.iloc[0]

        ready = str(row.get("calculator_ready_flag", "")).strip().lower() == "yes"
        direct_factor = pd.to_numeric(row.get("direct_factor_final"), errors="coerce")

        st.write("")
        st.markdown("## Your screening result")

        if not ready or pd.isna(direct_factor):
            st.warning("This product is not directly calculator-ready from a simple default-value lookup.")

            if row.get("lookup_display_message"):
                st.write(row["lookup_display_message"])
            if row.get("user_action_hint"):
                st.info(row["user_action_hint"])

            support_tally_url = build_tally_url(
                TALLY_FORM_URL,
                help_type="Methodology-based CBAM calculation",
                country=country,
                hs_code=row.get("hs_code_prefix", hs_code),
                product_description=row.get("product_name_final", ""),
                quantity=str(quantity),
                source="not_calculator_ready"
            )

            st.markdown('<div class="cta-card">', unsafe_allow_html=True)
            st.markdown("### Need a reporting-ready answer instead?")
            st.markdown(
                "Some products need more than a simple lookup. "
                "We can help with product review, methodology-based calculation, and next-step guidance."
            )
            d1, d2 = st.columns(2)
            with d1:
                st.link_button("Request a reporting-ready CBAM assessment", support_tally_url, width="stretch")
            with d2:
                st.link_button("Email us directly", f"mailto:{CONTACT_EMAIL}", width="stretch")
            st.caption("Leave your email and we’ll follow up. No call required.")
            st.markdown('</div>', unsafe_allow_html=True)

        else:
            emissions = quantity * float(direct_factor)

            a, b, c = st.columns(3)
            with a:
                st.markdown(
                    '<div class="result-card"><div class="metric-label">Direct factor</div>'
                    f'<div class="metric-value">{float(direct_factor):,.4g}</div>'
                    '<div class="small-note">tCO2e / tonne</div></div>',
                    unsafe_allow_html=True
                )
            with b:
                st.markdown(
                    '<div class="result-card"><div class="metric-label">Quantity</div>'
                    f'<div class="metric-value">{quantity:,.4g}</div>'
                    '<div class="small-note">tonnes</div></div>',
                    unsafe_allow_html=True
                )
            with c:
                st.markdown(
                    '<div class="result-card"><div class="metric-label">Estimated emissions</div>'
                    f'<div class="metric-value">{emissions:,.4g}</div>'
                    '<div class="small-note">tCO2e</div></div>',
                    unsafe_allow_html=True
                )

            st.write("")
            st.success("This result is useful as a fast CBAM screening estimate.")

            result_tally_url = build_tally_url(
                TALLY_FORM_URL,
                help_type="More accurate CBAM estimate",
                country=country,
                hs_code=row.get("hs_code_prefix", hs_code),
                product_description=row.get("product_name_final", ""),
                quantity=str(quantity),
                estimated_emissions=f"{emissions:.6g}",
                source="successful_result"
            )

            st.markdown('<div class="cta-card">', unsafe_allow_html=True)
            st.markdown("### Want a more accurate CBAM report by email?")
            st.markdown(
                "Default values are useful for fast screening, but official reporting or decision-grade work may require "
                "supplier-specific emissions, product review, and methodology-based calculation."
            )
            d1, d2 = st.columns(2)
            with d1:
                st.link_button("Get a more accurate CBAM report", result_tally_url, width="stretch")
            with d2:
                st.link_button("Email us directly", f"mailto:{CONTACT_EMAIL}", width="stretch")
            st.caption("No call booking needed. Leave your details and we’ll follow up.")
            st.markdown('</div>', unsafe_allow_html=True)

# --------------------------------
# Footer
# --------------------------------
st.markdown("---")
st.markdown(
    '<div class="footer-note">'
    'This tool is designed as a free screening layer for CBAM default values. '
    'For supplier-specific calculations, methodology support, product review, or reporting-ready estimates, '
    f'please leave your details via the form or email {CONTACT_EMAIL}.'
    '</div>',
    unsafe_allow_html=True
)
