
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
        max-width: 1100px;
        padding-top: 1.4rem;
        padding-bottom: 2.2rem;
    }
    h1, h2, h3 {
        color: #1f2430;
        letter-spacing: -0.02em;
    }
    .subtle {
        color: #5d6a66;
        font-size: 1.02rem;
        line-height: 1.55;
        margin-top: -0.3rem;
        margin-bottom: 0.75rem;
    }
    .micro {
        color: #73807c;
        font-size: 0.92rem;
        line-height: 1.5;
    }
    .tag {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        border-radius: 999px;
        background: #eef5f1;
        color: #2f6b59;
        font-size: 0.82rem;
        margin-right: 0.35rem;
        margin-bottom: 0.35rem;
    }
    .result-box {
        border: 1px solid #e5e9e7;
        border-radius: 16px;
        background: #ffffff;
        padding: 1rem 1.05rem;
    }
    .metric-label {
        color: #6f7b77;
        font-size: 0.9rem;
        margin-bottom: 0.2rem;
    }
    .metric-value {
        color: #202733;
        font-size: 1.85rem;
        font-weight: 700;
        line-height: 1.15;
    }
    .section-spacer {
        margin-top: 0.8rem;
        margin-bottom: 0.5rem;
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
    if not code:
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

    default_country = "China" if "China" in countries else countries[0]

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

    return default_country

def safe_num(row, *cols):
    for col in cols:
        if col in row.index:
            value = pd.to_numeric(row.get(col), errors="coerce")
            if pd.notna(value):
                return float(value)
    return None

def detect_sector_text(row):
    bits = [
        str(row.get("aggregated_goods_category", "")),
        str(row.get("product_name_final", "")),
        str(row.get("lookup_display_message", "")),
        str(row.get("definitive_period_primary_focus", "")),
    ]
    return " ".join(bits).lower()

def choose_factor(row):
    direct = safe_num(row, "calculator_direct_factor_tco2e_per_ton", "direct_emission_factor_tco2e_per_ton")
    indirect = safe_num(row, "calculator_indirect_factor_tco2e_per_ton", "indirect_emission_factor_tco2e_per_ton")
    total = safe_num(row, "calculator_total_factor_tco2e_per_ton", "total_emission_factor_tco2e_per_ton")

    focus = str(row.get("definitive_period_primary_focus", "")).strip().lower()
    sector_text = detect_sector_text(row)

    if "total" in focus and total is not None:
        return total, "Total factor", "Uses total embedded emissions."
    if "direct" in focus and direct is not None:
        return direct, "Direct factor", "Uses direct embedded emissions."
    if "indirect" in focus and indirect is not None:
        return indirect, "Indirect factor", "Uses indirect embedded emissions."

    if "cement" in sector_text or "fertili" in sector_text:
        if total is not None:
            return total, "Total factor", "Uses total embedded emissions."
        if direct is not None:
            return direct, "Direct factor", "Total factor unavailable; using direct factor."
    if "electricity" in sector_text:
        if direct is not None:
            return direct, "Direct factor", "Electricity is treated with direct emissions only in the definitive regime."
        if total is not None:
            return total, "Total factor", "Direct factor unavailable; using total factor."
    if "hydrogen" in sector_text:
        if direct is not None:
            return direct, "Direct factor", "Hydrogen uses direct emissions in the definitive regime."
        if total is not None:
            return total, "Total factor", "Direct factor unavailable; using total factor."
    if any(x in sector_text for x in ["iron", "steel", "aluminium", "aluminum"]):
        if direct is not None:
            return direct, "Direct factor", "Uses direct embedded emissions."
        if total is not None:
            return total, "Total factor", "Direct factor unavailable; using total factor."

    if direct is not None:
        return direct, "Direct factor", "Defaulted to direct factor."
    if total is not None:
        return total, "Total factor", "Direct factor unavailable; using total factor."
    if indirect is not None:
        return indirect, "Indirect factor", "Only indirect factor available."

    return None, "Factor", ""

df = load_data()

st.title("Free CBAM Calculator for EU Imports")
st.markdown(
    '<div class="subtle">Fast default-value screening for CBAM goods.</div>',
    unsafe_allow_html=True
)
st.markdown(
    '<span class="tag">Fast screening</span>'
    '<span class="tag">Country + HS code</span>'
    '<span class="tag">Email follow-up</span>',
    unsafe_allow_html=True
)

st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
st.markdown("## Start your estimate")

countries = sorted([c for c in df["country"].dropna().unique() if str(c).strip()])
default_country = infer_default_country(countries)
default_country_index = countries.index(default_country) if default_country in countries else 0

left, right = st.columns([1.25, 1])

with left:
    country = st.selectbox(
        "Country of origin",
        countries,
        index=default_country_index if countries else None
    )
    hs_code = st.text_input("HS code", placeholder="e.g. 72026000")

with right:
    quantity = st.number_input(
        "Quantity (tonnes)",
        min_value=0.0,
        value=1.0,
        step=1.0
    )
    st.write("")
    calculate = st.button("Estimate CBAM emissions", type="primary", width="stretch")

with st.expander("Methodology and limitations"):
    st.markdown(
        """
- Uses screening-level default values
- Not a final filing engine
- Some products need classification or methodology review
        """
    )

if calculate:
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
        factor_value, factor_label, factor_note = choose_factor(row)

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
st.caption(f"Questions: {CONTACT_EMAIL}")
