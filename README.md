# CBAM Leadgen App

A lightweight Streamlit app for fast **CBAM screening** on EU imports under the **2026+ definitive regime**.

This tool is designed for importers, traders, sourcing teams, and advisors who need a quick first-pass estimate before moving to a more detailed, reporting-ready assessment.

## Live App

**Streamlit App:** https://cbam-calculator.streamlit.app

## Why this tool exists

CBAM requirements can feel complex, especially for companies that are still at the early screening stage.

This app simplifies the first step:
- enter a few key shipment details
- get a quick screening result
- leave a work email if you want a more accurate CBAM-ready follow-up

The goal is not to replace full reporting or verification. The goal is to reduce friction and help users quickly understand whether a shipment likely needs deeper CBAM analysis.

## What the app does

- Provides a simple user flow for fast CBAM screening
- Uses **2026+ definitive-regime** logic rather than transitional-period logic
- Supports product lookup and factor mapping based on available HS/product data
- Estimates screening-level emissions for selected product groups
- Connects results to a short Tally lead form for follow-up support
- Keeps the interface lightweight and product-oriented, not content-heavy

## Product design goals

This project was intentionally designed with a **lead-generation + usability** mindset:

- minimal inputs
- fast result delivery
- short CTA flow
- reduced form burden
- limited explanatory text
- clear separation between screening and reporting-ready support

## Current workflow

1. User opens the Streamlit app  
2. User enters core shipment/product information  
3. App generates a screening-level estimate  
4. User is invited to leave a work email for a more accurate CBAM report or follow-up  
5. Key context can be passed into the Tally form through hidden fields

## Tally lead capture design

The lead form is intentionally short to reduce drop-off.

**Visible required fields**
- Work email
- What do you need help with?

**Hidden fields may include**
- help_type
- company_name
- country
- hs_code
- product_description
- quantity
- source
- estimated_emissions

## Tech stack

- **Python**
- **Streamlit**
- **CSV-based lookup / mapping logic**
- **Tally** for lead capture
- **GitHub** for version control
- **Streamlit Community Cloud** for deployment

## Repository structure

Typical core files include:

- `cbam_leadgen_app.py` — main Streamlit application
- `webapp_master_lookup.csv` — lookup / mapping data used by the app
- `README.md` — project overview

## Positioning

This is a **screening tool**, not a full compliance engine.

It is most useful for:
- early-stage importer triage
- commercial conversations
- initial customer qualification
- lightweight emissions estimation
- productized consulting workflows

It is **not** intended to serve as a substitute for:
- verified plant-level data collection
- full declarant workflows
- audited embedded-emissions calculations
- legal or customs advice

## Example use cases

- “We import into the EU and want a quick sense of whether this product may need deeper CBAM review.”
- “We need a simple front-end tool to qualify inbound leads before doing manual consulting work.”
- “We want to test a lightweight carbon-data workflow before building a more advanced reporting process.”

## Project highlights

- Translated complex CBAM concepts into a user-facing screening workflow
- Built a lightweight web app with conversion-focused UX decisions
- Reduced friction by simplifying inputs and trimming unnecessary page content
- Connected estimate output with lead capture for reporting-ready follow-up
- Framed the tool as a practical carbon data product, not just a calculator demo

## Roadmap

Planned or possible next steps:

- improve sector-specific logic under the definitive regime
- expand product coverage and factor handling
- improve result explanation without making the page too heavy
- add stronger workflow support for qualified inbound leads
- package the tool alongside broader carbon / LCA / CBAM services

## About the Builder

Ivan Lee is an AI + Data + Carbon analyst building practical tools for carbon reporting and decision support. His work combines analytics, workflow design, and lightweight product development across LCA, PCF, and CBAM-related use cases.

## Contact

For collaboration, project discussion, or CBAM/LCA-related inquiries:

**Email:** zerocarbonlab@gmail.com
