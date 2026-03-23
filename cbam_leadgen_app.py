import pandas as pd
import streamlit as st
from urllib.parse import urlencode

st.set_page_config(
    page_title="CBAM Default Emissions Finder",
    page_icon="🌿",
    layout="wide"
)

DATA_FILE = "webapp_master_lookup.csv"

# -----------------------------
# Replace these 2 values only
# -----------------------------
TALLY_FORM_URL = "https://tally.so/r/REPLACE_WITH_YOUR_TALLY_FORM_ID"
CONTACT_EMAIL = "zerocarbonlab@gmail.com"

# -----------------------------
# Soft minimalist styling
# -----------------------------
SOFT_CSS = """
<style>
    .stApp {
        background: #fbfcfa;
    }
    .block-container {
        max-width: 980px;
        padding-top: 2.2rem;
        padding-bottom: 3rem;
    }
    h1, h2, h3 {
        color: #22312f;
        letter-spacing: -0.02em;
    }
    .subtle {
        color: #6b7b78;
        font-size: 1rem;
        margin-top: -0.3rem;
        margin-bottom: 1.4rem;
    }
    .hero-card, .cta-card, .result-card {
        border: 1px solid #e7eeea;
        background: #ffffff;
        border-radius: 18px;
        padding: 1.1rem 1.2rem;
        box-shadow: 0 6px 20px rgba(28, 44, 40, 0.04);
    }
    .cta-card {
        background: linear-gradient(180deg, #f6fbf8 0%, #ffffff 100%);
        border-color: #dbe9e2;
    }
    .metric-label {
        color: #71817f;
        font-size: 0.9rem;
        margin-bottom: 0.25rem;
    }
    .metric-value {
        color: #1f2b29;
        font-size: 2rem;
        font-weight: 700;
        line-height: 1.1;
    }
    .tiny-note {
        color: #768683;
        font-size: 0.88rem;
    }
    .pill {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        border-radius: 999px;
        background: #edf6f1;
        color: #2f6758;
        font-size: 0.82rem;
        margin-right: 0.4rem;
        margin-bottom: 0.3rem;
    }
    .footer-note {
        color: #71857d;
        font-size: 0.95rem;
        line-height: 1.6;
    }
</style>
"""
st.markdown(SOFT_CSS, unsafe_allow_html=True)

# -----------------------------
# Data loading
# -----------------------------
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_FILE, dtype=str)

    num_cols = [
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
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

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

    if "lookup_display_message" not in df.columns:
        df["lookup_display_message"] = ""
    if "user_action_hint" not in df.columns:
        df["user_action_hint"] = ""
    if "calculator_ready_flag" not in df.columns:
        df["calculator_ready_flag"] = ""
    if "factor_status" not in df.columns:
        df["factor_status"] = ""
    if "definitive_period_primary_focus" not in df.columns:
        df["definitive_period_primary_focus"] = ""
    if "aggregated_goods_category" not in df.columns:
        df["aggregated_goods_category"] = ""
    if "hs_code_prefix" not in df.columns:
        df["hs_code_prefix"] = ""
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
    source: str = "cbam_default_emissions_finder",
    estimated_emissions: str = ""
):
    """
    Build a Tally URL with hidden field params.
    In your Tally form, add hidden fields with matching names if you want
    them stored automatically, or use them to prefill visible optional fields.
    """
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

# -----------------------------
# Hero
# -----------------------------
st.markdown('<div class="hero-card">', unsafe_allow_html=True)
st.title("CBAM Default Emissions Finder")
st.markdown(
    '<div class="subtle">Free screening tool for CBAM default values. '
    'Enter your country of origin, HS code, and shipment quantity to estimate emissions in seconds.</div>',
    unsafe_allow_html=True
)
st.markdown(
    '<span class="pill">Free default-value lookup</span>'
    '<span class="pill">All countries in official workbook</span>'
    '<span class="pill">Low-friction lead capture</span>',
    unsafe_allow_html=True
)
st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# Always-visible CTA
# -----------------------------
top_help_type = "More accurate CBAM estimate"
top_tally_url = build_tally_url(
    TALLY_FORM_URL,
    help_type=top_help_type,
    source="hero_cta"
)

st.write("")
st.markdown('<div class="cta-card">', unsafe_allow_html=True)
st.markdown("### Need more than a default-value estimate?")
st.markdown(
    "Use the free tool below for screening. If you need supplier-specific support, "
    "methodology review, precursor analysis, or help with unclear HS classification, "
    "leave your details and we’ll follow up by email."
)
cta1, cta2 = st.columns([1, 1])
with cta1:
    st.link_button("Request custom support", top_tally_url, width="stretch")
with cta2:
    st.link_button("Email us", f"mailto:{CONTACT_EMAIL}", width="stretch")
st.caption("No need to book a call. Leave your details and we’ll follow up by email.")
st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# Calculator
# -----------------------------
st.write("")
left, right = st.columns([1.2, 1])

with left:
    countries = sorted([c for c in df["country"].dropna().unique() if str(c).strip()])
    default_country_index = countries.index("China") if "China" in countries else 0
    country = st.selectbox(
        "Country of origin",
        countries,
        index=default_country_index if countries else None
    )
    hs_code = st.text_input("HS code", placeholder="e.g. 72026000")

with right:
    quantity = st.number_input("Quantity (tonnes)", min_value=0.0, value=1.0, step=1.0)
    st.write("")
    calculate = st.button("Calculate", type="primary", width="stretch")

with st.expander("Methodology & scope"):
    st.markdown(
        """
- This tool uses published CBAM default values as a **screening-level** estimate.
- Default values can be useful for quick checks, but may not be sufficient for supplier-specific or reporting-ready work.
- Some products require more detailed classification, product description review, or methodology-based calculation.
        """
    )

# -----------------------------
# Results + context-aware CTA
# -----------------------------
if calculate:
    matches = find_matches(df, country, hs_code)

    if matches.empty:
        st.error("No matching row found. Try a more specific HS code.")

        no_match_tally_url = build_tally_url(
            TALLY_FORM_URL,
            help_type="HS code or product classification support",
            country=country,
            hs_code=hs_code,
            quantity=str(quantity),
            source="no_match_result"
        )

        st.markdown('<div class="cta-card">', unsafe_allow_html=True)
        st.markdown("### Can’t find a match?")
        st.markdown(
            "That usually means you may need a more specific HS code, or a quick classification review. "
            "You can leave your details and we’ll follow up by email."
        )
        st.link_button("Request classification support", no_match_tally_url, width="stretch")
        st.markdown('</div>', unsafe_allow_html=True)

    else:
        if len(matches) > 1:
            st.info("More than one product description matches this HS code. Select the closest product below.")
            option_labels = [
                f"{row['product_name_final']} | {row.get('aggregated_goods_category','')} | {row.get('hs_code_prefix','')}"
                for _, row in matches.iterrows()
            ]
            selected_label = st.selectbox("Choose the matching product description", option_labels)
            selected_idx = option_labels.index(selected_label)
            row = matches.iloc[selected_idx]
        else:
            row = matches.iloc[0]

        ready = str(row.get("calculator_ready_flag", "")).strip().lower() == "yes"
        direct_factor = pd.to_numeric(row.get("direct_factor_final"), errors="coerce")

        if not ready or pd.isna(direct_factor):
            st.warning("This row is not directly calculator-ready.")

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
            st.markdown("### Need a reporting-ready answer?")
            st.markdown(
                "If this product cannot be estimated cleanly with a simple default-value lookup, "
                "we can help with a methodology-based approach, product review, and next-step guidance."
            )
            d1, d2 = st.columns(2)
            with d1:
                st.link_button("Request custom assessment", support_tally_url, width="stretch")
            with d2:
                st.link_button("Email us", f"mailto:{CONTACT_EMAIL}", width="stretch")
            st.markdown('</div>', unsafe_allow_html=True)

        else:
            emissions = quantity * float(direct_factor)

            a, b, c = st.columns(3)
            with a:
                st.markdown(
                    '<div class="result-card"><div class="metric-label">Direct factor</div>'
                    f'<div class="metric-value">{float(direct_factor):,.4g}</div>'
                    '<div class="tiny-note">tCO2e / tonne</div></div>',
                    unsafe_allow_html=True
                )
            with b:
                st.markdown(
                    '<div class="result-card"><div class="metric-label">Quantity</div>'
                    f'<div class="metric-value">{quantity:,.4g}</div>'
                    '<div class="tiny-note">tonnes</div></div>',
                    unsafe_allow_html=True
                )
            with c:
                st.markdown(
                    '<div class="result-card"><div class="metric-label">Estimated emissions</div>'
                    f'<div class="metric-value">{emissions:,.4g}</div>'
                    '<div class="tiny-note">tCO2e</div></div>',
                    unsafe_allow_html=True
                )

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

            st.write("")
            st.markdown('<div class="cta-card">', unsafe_allow_html=True)
            st.markdown("### Want a more accurate CBAM assessment?")
            st.markdown(
                "Default values are useful for fast screening, but official reporting or decision-grade work may require "
                "supplier-specific emissions, process review, or a methodology-based calculation."
            )
            d1, d2 = st.columns(2)
            with d1:
                st.link_button("Request a custom calculation", result_tally_url, width="stretch")
            with d2:
                st.link_button("Email for consultation", f"mailto:{CONTACT_EMAIL}", width="stretch")
            st.caption("No need to schedule a call. Leave your details and we’ll follow up by email.")
            st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# Footer
# -----------------------------
st.markdown("---")
st.markdown(
    '<div class="footer-note">'
    'This tool is designed as a free screening layer for CBAM default values. '
    'For supplier-specific calculations, methodology design, or reporting support, '
    f'please leave your details via the form above or email {CONTACT_EMAIL}.'
    '</div>',
    unsafe_allow_html=True
)
