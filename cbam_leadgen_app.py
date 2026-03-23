
import pandas as pd
import streamlit as st
from urllib.parse import urlencode

st.set_page_config(
    page_title="CBAM Calculator for EU Imports",
    page_icon="🌿",
    layout="wide"
)

DATA_FILE = "webapp_master_lookup.csv"
TALLY_FORM_URL = "https://tally.so/r/b5LV5e"
CONTACT_EMAIL = "zerocarbonlab@gmail.com"

CUSTOM_CSS = """
<style>
    .block-container {
        max-width: 1080px;
        padding-top: 1.1rem;
        padding-bottom: 1.6rem;
    }
    h1, h2, h3 {
        color: #1f2430;
        letter-spacing: -0.02em;
        margin-bottom: 0.35rem;
    }
    .subtle {
        color: #5f6c68;
        font-size: 1rem;
        line-height: 1.45;
        margin-top: -0.1rem;
        margin-bottom: 0.55rem;
    }
    .micro {
        color: #73807c;
        font-size: 0.92rem;
        line-height: 1.45;
    }
    .tag {
        display: inline-block;
        padding: 0.23rem 0.58rem;
        border-radius: 999px;
        background: #eef5f1;
        color: #2f6b59;
        font-size: 0.82rem;
        margin-right: 0.30rem;
        margin-bottom: 0.30rem;
    }
    .result-box {
        border: 1px solid #e5e9e7;
        border-radius: 14px;
        background: #ffffff;
        padding: 0.9rem 1rem;
    }
    .metric-label {
        color: #6f7b77;
        font-size: 0.88rem;
        margin-bottom: 0.15rem;
    }
    .metric-value {
        color: #202733;
        font-size: 1.75rem;
        font-weight: 700;
        line-height: 1.1;
    }
    .inline-cta-title {
        color: #2a2f3a;
        font-size: 1.05rem;
        font-weight: 600;
        margin-top: 0.35rem;
        margin-bottom: 0.45rem;
    }
    .button-spacer {
        height: 2.1rem;
    }
    .footer-note {
        color: #74807c;
        font-size: 0.92rem;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

REGION_TO_COUNTRY = {
    "CN": "China",
    "US": "United States",
    "GB": "United Kingdom",
    "UK": "United Kingdom",
    "DE": "Germany",
    "FR": "France",
    "IT": "Italy",
    "ES": "Spain",
    "NL": "Netherlands",
    "BE": "Belgium",
    "PL": "Poland",
    "JP": "Japan",
    "KR": "South Korea",
    "IN": "India",
    "TR": "Turkey",
    "VN": "Vietnam",
    "TH": "Thailand",
    "MY": "Malaysia",
    "SG": "Singapore",
    "ID": "Indonesia",
    "BR": "Brazil",
    "CA": "Canada",
    "MX": "Mexico",
    "AU": "Australia",
    "AE": "United Arab Emirates",
    "SA": "Saudi Arabia",
    "ZA": "South Africa",
    "HK": "Hong Kong",
    "TW": "Taiwan",
}

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
        df["product_name_final"] = df["display_name"].fillna("")
    elif "product_display_name" in df.columns:
        df["product_name_final"] = df["product_display_name"].fillna("")
    else:
        df["product_name_final"] = ""

    if "country" not in df.columns and "origin_country_assumed" in df.columns:
        df["country"] = df["origin_country_assumed"]
    if "country" not in df.columns:
        df["country"] = ""

    defaults = {
        "lookup_display_message": "",
        "user_action_hint": "",
        "calculator_ready_flag": "",
        "factor_status": "",
        "definitive_period_primary_focus": "",
        "aggregated_goods_category": "",
        "cbam_sector": "",
        "hs_code_prefix": "",
        "methodology_note": "",
        "rule_source": "",
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

def find_matches(df, country, hs_code):
    code = clean_hs_code(hs_code)
    if not code or not country:
        return pd.DataFrame()

    subset = df[df["country"] == country].copy()

    exact = subset[subset["hs_code_prefix"] == code].copy()
    if not exact.empty:
        return exact

    starts = subset[subset["hs_code_prefix"].fillna("").str.startswith(code)].copy()
    return starts.sort_values(["hs_code_prefix", "product_name_final"])

def infer_default_country(countries):
    if not countries:
        return None

    try:
        locale = getattr(st.context, "locale", None)
    except Exception:
        locale = None

    if locale:
        locale = str(locale)
        region = None
        if "-" in locale:
            region = locale.split("-")[-1].upper()
        elif "_" in locale:
            region = locale.split("_")[-1].upper()
        elif len(locale) == 2:
            region = locale.upper()

        candidate = REGION_TO_COUNTRY.get(region)
        if candidate in countries:
            return candidate

    return None

def parse_quantity(qtext):
    if qtext is None:
        return None
    qtext = str(qtext).strip().replace(",", "")
    if qtext == "":
        return None
    try:
        value = float(qtext)
        if value <= 0:
            return None
        return value
    except Exception:
        return None

def safe_num(row, *cols):
    for col in cols:
        if col in row.index:
            value = pd.to_numeric(row.get(col), errors="coerce")
            if pd.notna(value):
                return float(value)
    return None

def choose_definitive_factor(row):
    """
    Definitive regime (2026 onwards):
    - Prefer the official 2026 default value field from the user's workbook.
    - If unavailable, fall back by sector/focus:
      * cement, fertilisers -> total
      * iron_and_steel, aluminium, hydrogen, electricity -> direct
      * then safe fallback to any available factor
    """
    factor_2026 = safe_num(row, "2026_default_value_including_markup")
    direct = safe_num(row, "calculator_direct_factor_tco2e_per_ton", "direct_emission_factor_tco2e_per_ton")
    indirect = safe_num(row, "calculator_indirect_factor_tco2e_per_ton", "indirect_emission_factor_tco2e_per_ton")
    total = safe_num(row, "calculator_total_factor_tco2e_per_ton", "total_emission_factor_tco2e_per_ton")

    sector = str(row.get("cbam_sector", "")).strip().lower()
    focus = str(row.get("definitive_period_primary_focus", "")).strip().lower()

    if factor_2026 is not None:
        return factor_2026, "2026 default value", "Uses the 2026 definitive default value from your workbook."

    if sector in {"cement", "fertilisers", "fertilizers"} or "direct and indirect" in focus:
        if total is not None:
            return total, "Total factor", "Uses total embedded emissions for the definitive regime."
        if direct is not None and indirect is not None:
            return direct + indirect, "Total factor", "Computed as direct + indirect."
        if direct is not None:
            return direct, "Direct factor", "Total factor unavailable; using direct factor."

    if sector in {"iron_and_steel", "aluminium", "aluminum", "hydrogen", "electricity"} or "direct emissions" in focus:
        if direct is not None:
            return direct, "Direct factor", "Uses direct embedded emissions for the definitive regime."
        if total is not None:
            return total, "Total factor", "Direct factor unavailable; using total factor."

    if total is not None:
        return total, "Total factor", "Fallback to total factor."
    if direct is not None:
        return direct, "Direct factor", "Fallback to direct factor."
    if indirect is not None:
        return indirect, "Indirect factor", "Only indirect factor available."

    return None, "Factor", ""

df = load_data()

st.title("Free CBAM Calculator for EU Imports")
st.markdown(
    '<div class="subtle">Fast default-value screening for CBAM goods.</div>',
    unsafe_allow_html=True
)
st.markdown("## Start your estimate")

countries = sorted([c for c in df["country"].dropna().unique() if str(c).strip()])
default_country = infer_default_country(countries)
default_country_index = countries.index(default_country) if default_country in countries else None

top_left, top_right = st.columns([1.25, 1])

with top_left:
    country = st.selectbox(
        "Country of origin",
        countries,
        index=default_country_index,
        placeholder="Select country"
    )

with top_right:
    quantity_text = st.text_input("Quantity (tonnes)", placeholder="e.g. 10")

bottom_left, bottom_right = st.columns([1.25, 1])

with bottom_left:
    hs_code = st.text_input("HS code", placeholder="e.g. 72026000")

with bottom_right:
    st.markdown('<div class="button-spacer"></div>', unsafe_allow_html=True)
    calculate = st.button("Estimate CBAM emissions", type="primary", width="stretch")

lead_url = build_tally_url(
    TALLY_FORM_URL,
    help_type="More accurate CBAM estimate",
    country=country or "",
    hs_code=hs_code or "",
    quantity=quantity_text or "",
    source="inline_lead_capture"
)

st.markdown('<div class="inline-cta-title">Need a reporting-ready answer?</div>', unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    st.link_button("Get a more accurate CBAM report", lead_url, width="stretch")
with c2:
    st.link_button("Email us directly", f"mailto:{CONTACT_EMAIL}", width="stretch")

st.caption("2026+ screening logic. For reporting-ready work, request a more accurate CBAM report.")

if calculate:
    quantity = parse_quantity(quantity_text)
    if not country:
        st.error("Please select a country.")
        st.stop()
    if not clean_hs_code(hs_code):
        st.error("Please enter an HS code.")
        st.stop()
    if quantity is None:
        st.error("Please enter a valid quantity in tonnes, for example 10.")
        st.stop()

    matches = find_matches(df, country, hs_code)

    if matches.empty:
        st.error("No matching row found.")
        no_match_tally_url = build_tally_url(
            TALLY_FORM_URL,
            help_type="HS code or product classification support",
            country=country,
            hs_code=hs_code,
            quantity=str(quantity),
            source="no_match_result"
        )
        st.link_button("Get HS code support", no_match_tally_url, width="stretch")

    else:
        if len(matches) > 1:
            option_labels = [
                f"{row['product_name_final']} | {row.get('aggregated_goods_category','')} | {row.get('hs_code_prefix','')}"
                for _, row in matches.iterrows()
            ]
            selected_label = st.selectbox("Select product", option_labels)
            row = matches.iloc[option_labels.index(selected_label)]
        else:
            row = matches.iloc[0]

        ready = str(row.get("calculator_ready_flag", "")).strip().lower() == "yes"
        factor_value, factor_label, factor_note = choose_definitive_factor(row)

        st.write("")
        st.markdown("## Result")

        if not ready or factor_value is None:
            st.warning("This item needs a methodology-based review.")
            support_tally_url = build_tally_url(
                TALLY_FORM_URL,
                help_type="Methodology-based CBAM calculation",
                country=country,
                hs_code=row.get("hs_code_prefix", hs_code),
                product_description=row.get("product_name_final", ""),
                quantity=str(quantity),
                source="not_calculator_ready"
            )
            st.link_button("Request support", support_tally_url, width="stretch")

        else:
            emissions = quantity * float(factor_value)

            a, b, c = st.columns(3)
            with a:
                st.markdown(
                    '<div class="result-box"><div class="metric-label">'
                    + factor_label +
                    '</div><div class="metric-value">'
                    + f'{float(factor_value):,.4g}'
                    + '</div><div class="micro">tCO2e / tonne</div></div>',
                    unsafe_allow_html=True
                )
            with b:
                st.markdown(
                    '<div class="result-box"><div class="metric-label">Quantity</div><div class="metric-value">'
                    + f'{quantity:,.4g}'
                    + '</div><div class="micro">tonnes</div></div>',
                    unsafe_allow_html=True
                )
            with c:
                st.markdown(
                    '<div class="result-box"><div class="metric-label">Estimated emissions</div><div class="metric-value">'
                    + f'{emissions:,.4g}'
                    + '</div><div class="micro">tCO2e</div></div>',
                    unsafe_allow_html=True
                )

            if factor_note:
                st.caption(factor_note)

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
            st.markdown("## Need more than a screening estimate?")
            st.markdown(
                "Need supplier-specific support, HS code review, or a more accurate estimate? Leave your details and we’ll follow up by email."
            )
            d1, d2 = st.columns(2)
            with d1:
                st.link_button("Get a more accurate CBAM report", result_tally_url, width="stretch")
            with d2:
                st.link_button("Email us directly", f"mailto:{CONTACT_EMAIL}", width="stretch")

st.markdown("---")
st.markdown(
    f'<div class="footer-note">Questions: <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></div>',
    unsafe_allow_html=True
)
