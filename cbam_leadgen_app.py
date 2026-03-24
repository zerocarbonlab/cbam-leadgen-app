
import re
from urllib.parse import urlencode

import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="CBAM Calculator for EU Imports",
    page_icon="🌿",
    layout="wide"
)

DATA_FILE = "webapp_master_lookup.csv"
TALLY_FORM_URL = "https://tally.so/r/b5LV5e"
CONTACT_EMAIL = "zerocarbonlab@gmail.com"

DEFAULT_EUA_PRICE_EUR_PER_TCO2 = 69.08

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
    .micro {
        color: #73807c;
        font-size: 0.92rem;
        line-height: 1.45;
    }
    .result-box {
        border: 1px solid #e5e9e7;
        border-radius: 14px;
        background: #ffffff;
        padding: 0.9rem 1rem;
        min-height: 150px;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        box-sizing: border-box;
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
        margin-bottom: 0.3rem;
    }
    .metric-subline {
        color: #73807c;
        font-size: 0.92rem;
        line-height: 1.35;
        margin-top: auto;
    }
    .inline-cta-title {
        color: #2a2f3a;
        font-size: 1.05rem;
        font-weight: 600;
        margin-top: 0.35rem;
        margin-bottom: 0.45rem;
    }
    .field-label-spacer {
        height: 1.9rem;
    }
    .footer-note {
        color: #74807c;
        font-size: 0.92rem;
        margin-top: 0.2rem;
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

def _fetch_text(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
    }
    response = requests.get(url, headers=headers, timeout=12)
    response.raise_for_status()
    return response.text

def _parse_tradingeconomics_price(text: str):
    patterns = [
        r"EU Carbon Permits traded at\s*([0-9]+(?:\.[0-9]+)?)",
        r'"price"\s*:\s*([0-9]+(?:\.[0-9]+)?)',
        r'"close"\s*:\s*([0-9]+(?:\.[0-9]+)?)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return float(match.group(1))
    return None

def _parse_investing_price(text: str):
    patterns = [
        r'The current price of Carbon Emissions futures is\s*([0-9]+(?:\.[0-9]+)?)',
        r'"last"\s*:\s*([0-9]+(?:\.[0-9]+)?)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return float(match.group(1))
    return None

@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def get_current_eua_price():
    sources = [
        ("TradingEconomics", "https://tradingeconomics.com/eecxm:ind", _parse_tradingeconomics_price),
        ("Investing.com", "https://www.investing.com/commodities/carbon-emissions", _parse_investing_price),
    ]
    for source_name, url, parser in sources:
        try:
            text = _fetch_text(url)
            price = parser(text)
            if price is not None and price > 0:
                return {"price": float(price), "source": source_name, "is_fallback": False}
        except Exception:
            pass
    return {"price": DEFAULT_EUA_PRICE_EUR_PER_TCO2, "source": "Manual fallback", "is_fallback": True}

def render_result_box(label: str, value: str, subline: str):
    html = (
        '<div class="result-box">'
        f'<div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div>'
        f'<div class="metric-subline">{subline}</div>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)

df = load_data()
price_info = get_current_eua_price()
current_eua_price = float(price_info["price"])

st.title("Free CBAM Calculator for EU Imports")
st.markdown("## Start your estimate")

countries = sorted([c for c in df["country"].dropna().unique() if str(c).strip()])
default_country = infer_default_country(countries)
default_country_index = countries.index(default_country) if default_country in countries else None

top_left, top_right = st.columns([1.25, 1])
with top_left:
    country = st.selectbox("Country of origin", countries, index=default_country_index, placeholder="Select country")
with top_right:
    quantity_text = st.text_input("Quantity (tonnes)", placeholder="e.g. 10")

bottom_left, bottom_right = st.columns([1.25, 1])
with bottom_left:
    hs_code = st.text_input("HS code", placeholder="e.g. 72026000")
with bottom_right:
    st.markdown('<div class="field-label-spacer"></div>', unsafe_allow_html=True)
    calculate = st.button("Estimate CBAM emissions & cost", type="primary", width="stretch")

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
            indicative_cbam_cost = emissions * current_eua_price

            a, b, c, d = st.columns(4)
            with a:
                render_result_box(factor_label, f"{float(factor_value):,.4g}", "tCO2e / tonne")
            with b:
                render_result_box("Quantity", f"{quantity:,.4g}", "tonnes")
            with c:
                render_result_box("Estimated emissions", f"{emissions:,.4g}", "tCO2e")
            with d:
                render_result_box("Indicative CBAM cost", f"€{indicative_cbam_cost:,.0f}", f"at €{current_eua_price:,.2f} / tCO2e")

            if price_info["is_fallback"]:
                note_text = f"Indicative only. Using fallback EUA price (€{current_eua_price:,.2f}/tCO2e)."
            else:
                note_text = f"Indicative only. Based on current EUA price (€{current_eua_price:,.2f}/tCO2e, cached daily)."
            st.caption(note_text)

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
            st.markdown("Need supplier-specific support, HS code review, or a more accurate estimate? Leave your details and we’ll follow up by email.")
            d1, d2 = st.columns(2)
            with d1:
                st.link_button("Get a more accurate CBAM report", result_tally_url, width="stretch")
            with d2:
                st.link_button("Email us directly", f"mailto:{CONTACT_EMAIL}", width="stretch")

st.markdown(
    f'<div class="footer-note">Built by a data analyst focused on carbon, LCA, and CBAM workflow design. · <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></div>',
    unsafe_allow_html=True
)
