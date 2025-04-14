import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
import os
import plotly.express as px

# --- Streamlit Config ---
st.set_page_config(page_title="Wedding Budget Estimator", layout="centered")
if os.path.exists("blk-MAIN.png"):
    logo = Image.open("blk-MAIN.png")
    st.image(logo, width=200)

st.title("💍 Wedding Budget Estimator")

st.info("""
This tool is meant to help you **start the conversation** around your wedding budget — not to be a precise quote.

It uses estimated ranges based on real weddings and vendor averages across Vancouver Island, but actual prices may vary depending on season, style, and location.

Take this as your planning launchpad, not your final spreadsheet 🌛
""")

# --- Categories and Base Costs ---
categories = [
    "Officiant",
    "Ceremony Decor, Rentals, and AV",
    "Venues (your event's backdrop & setting)",
    "Decor & Rentals (Furniture, decor, tent, etc.)",
    "Floral Design",
    "Music/Entertainment (DJ, Band, Photobooth, etc.)",
    "Photography",
    "Videography",
    "Hair & Makeup",
    "Personal Florals (Bouquets, Boutonnieres, Crowns, etc.)",
    "Wedding Attire",
    "Food",
    "Beverage",
    "Stationery",
    "Transportation",
    "Planning Support",
    "Event Management",
    "Design Services",
    "Other (Signage, Stationery, Gifts, Favours, etc.)"
]

base_costs = {
    "Officiant": [400, 600, 1000],
    "Ceremony Decor, Rentals, and AV": [1200, 3000, 6000],
    "Venues (your event's backdrop & setting)": [3000, 7000, 12000],
    "Decor & Rentals (Furniture, decor, tent, etc.)": [2500, 4500, 8000],
    "Floral Design": [2000, 4000, 8000],
    "Music/Entertainment (DJ, Band, Photobooth, etc.)": [2000, 3500, 6000],
    "Photography": [3000, 4500, 7000],
    "Videography": [2000, 3000, 5000],
    "Hair & Makeup": [1000, 1500, 2500],
    "Personal Florals (Bouquets, Boutonnieres, Crowns, etc.)": [800, 1500, 2500],
    "Wedding Attire": [2500, 6350, 12600],
    "Food": [10400, 15600, 25900],
    "Beverage": [4200, 6700, 12200],
    "Stationery": [1000, 2000, 3500],
    "Transportation": [800, 1800, 3000],
    "Planning Support": [1500, 2500, 4000],
    "Event Management": [1000, 2000, 3000],
    "Design Services": [1500, 3000, 6000],
    "Other (Signage, Stationery, Gifts, Favours, etc.)": [1000, 2000, 4000]
}

# --- (all previous setup and calculations remain the same) ---

# --- Output ---
st.markdown("---")
st.header("Estimated Budgets")
for tier in ["Essential", "Enhanced", "Elevated"]:
    st.subheader(f"{tier} Budget")
    st.write(f"Total: ${tier_totals[tier]:,} | Per Guest: ${tier_totals[tier] // guest_count:,}/guest")
    df = pd.DataFrame.from_dict(budget_tiers[tier], orient='index', columns=['Amount'])

    # Handle excluded categories visually and map for styling
    excluded = [cat for cat in df.index if cat not in included_categories]
    rename_map = {cat: f"⚪ {cat}" for cat in excluded if cat in df.index}
    df.rename(index=rename_map, inplace=True)

    # Drop hidden row safely
    if "_goal_spend" in df.index:
        df = df.drop("_goal_spend")

    styled = df.style.format("${:,.0f}")
    st.dataframe(styled)

    chart = px.pie(
        df[df["Amount"] > 0].reset_index(),
        names='index',
        values='Amount',
        title=f"{tier} Budget Breakdown",
        color_discrete_sequence=[
            "#2e504c", "#c8a566", "#9bb7be", "#dad0af", "#477485", "#dee5e3", "#ffffff"
        ]
    )
    st.plotly_chart(chart)

    st.subheader(f"{tier} Budget by Experience Goal")
    goal_breakdown = budget_tiers[tier]["_goal_spend"]
    goal_df = pd.DataFrame.from_dict(goal_breakdown, orient='index', columns=['Amount'])
    goal_df = goal_df[goal_df['Amount'] > 0]
    goal_df['Percent'] = (goal_df['Amount'] / tier_totals[tier]) * 100
    st.dataframe(goal_df.style.format({"Amount": "${:,.0f}", "Percent": "{:.1f}%"}))

    summary = f"{tier} Wedding Budget Estimate\nTotal: ${tier_totals[tier]:,}\nPer Guest: ${tier_totals[tier] // guest_count:,}\n\nBreakdown:\n" + \
             "\n".join([f"{k}: ${v:,}" for k, v in df["Amount"].items()])
    st.text_area(f"{tier} Summary:", summary, height=300)

    csv = df.to_csv().encode('utf-8')
    st.download_button(
        label=f"⬇️ Download {tier} Budget as CSV",
        data=csv,
        file_name=f'{tier.lower()}_budget.csv',
        mime='text/csv'
    )
