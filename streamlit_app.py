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

# --- Categories ---
category_groups = {
    "Venues & Setup": [
        "Venues (your event's backdrop & setting)",
        "Ceremony (Rentals, Decor, Officiant, etc.)",
        "Decor & Rentals (Furniture, decor, tent, etc.)",
    ],
    "Experience & Atmosphere": [
        "Music/Entertainment (DJ, Band, Photobooth, etc.)",
        "Photo/Video",
        "Hair & Makeup",
        "Personal Florals (Bouquets, Boutonnieres, Crowns, etc.)",
        "Wedding Attire",
    ],
    "Guest Experience": [
        "Food",
        "Beverage",
        "Stationery",
        "Transportation",
    ],
    "Planning & Extras": [
        "Planner",
        "Other (Signage, Stationery, Gifts, Favours, etc.)",
    ]
}

categories = sum(category_groups.values(), [])

base_costs = {
    "Venues (your event's backdrop & setting)": [3000, 7000, 12000],
    "Ceremony (Rentals, Decor, Officiant, etc.)": [3600, 6350, 11683],
    "Decor & Rentals (Furniture, decor, tent, etc.)": [2500, 4500, 8000],
    "Music/Entertainment (DJ, Band, Photobooth, etc.)": [2000, 3500, 6000],
    "Photo/Video": [4000, 7500, 12000],
    "Hair & Makeup": [1000, 1500, 2500],
    "Personal Florals (Bouquets, Boutonnieres, Crowns, etc.)": [800, 1500, 2500],
    "Wedding Attire": [2500, 6350, 12600],
    "Food": [10400, 15600, 25900],
    "Beverage": [4200, 6700, 12200],
    "Stationery": [1000, 2000, 3500],
    "Transportation": [800, 1800, 3000],
    "Planner": [1500, 3500, 7000],
    "Other (Signage, Stationery, Gifts, Favours, etc.)": [1000, 2000, 4000],
}

minimums = {
    "Hair & Makeup": 500,
    "Wedding Attire": 800,
    "Planner": 1000,
    "Venue": 1500,
}

# --- Input Fields ---
st.markdown("Enter your wedding details below. We'll calculate three budget levels based on your unique priorities!")

guest_count = st.number_input("Guest Count", min_value=1, value=100)
dresses = st.number_input("Wedding Party Dresses You're Paying For", min_value=0, value=0)
suits = st.number_input("Wedding Party Suits You're Paying For", min_value=0, value=0)
marrier_hair = st.number_input("How many marriers are getting hair done?", min_value=0, value=1)
marrier_makeup = st.number_input("How many marriers are getting makeup done?", min_value=0, value=1)
wp_hair = st.number_input("Wedding party hair services you're covering", min_value=0, value=0)
wp_makeup = st.number_input("Wedding party makeup services you're covering", min_value=0, value=0)

st.markdown("---")
st.subheader("Step 2: Select Your Priorities")
top_3 = st.multiselect("Choose Your TOP 3 Priorities", categories, max_selections=3)
bottom_3 = st.multiselect("Choose Your BOTTOM 3 Priorities", [c for c in categories if c not in top_3], max_selections=3)

# Assign priority levels
def get_priority(cat):
    if cat in top_3:
        return "top"
    elif cat in bottom_3:
        return "bottom"
    else:
        return "mid"

# Priority logic map for tiered interpolation
priority_weights = {
    "Essential": {
        "top": [0.6, 0.4, 0.0],
        "mid": [0.8, 0.2, 0.0],
        "bottom": [1.0, 0.0, 0.0],
    },
    "Enhanced": {
        "top": [0.3, 0.7, 0.0],
        "mid": [0.0, 0.5, 0.5],
        "bottom": [0.8, 0.2, 0.0],
    },
    "Elevated": {
        "top": [0.0, 0.1, 0.9],
        "mid": [0.0, 0.2, 0.8],
        "bottom": [0.5, 0.5, 0.0],
    },
}

# --- Budget Calculation ---
scaling_factor = guest_count / 100
budget_tiers = {"Essential": {}, "Enhanced": {}, "Elevated": {}}
tier_totals = {}

for tier in budget_tiers:
    total = 0
    for cat in categories:
        pri = get_priority(cat)
        g, b, bst = base_costs[cat]
        w = priority_weights[tier][pri]
        value = (g * w[0] + b * w[1] + bst * w[2]) * scaling_factor

        # Add-ons
        if cat == "Hair & Makeup":
            value += (marrier_hair + wp_hair) * 100 + (marrier_makeup + wp_makeup) * 100
        if cat == "Wedding Attire":
            value += dresses * 250 + suits * 200

        value = round(value)
        budget_tiers[tier][cat] = value
        total += value

    tier_totals[tier] = total

# --- Display Budgets ---
st.markdown("---")
st.header("Estimated Budgets")
for tier in ["Essential", "Enhanced", "Elevated"]:
    st.subheader(f"{tier} Budget")
    st.write(f"Total: ${tier_totals[tier]:,} | Per Guest: ${tier_totals[tier] // guest_count:,}/guest")

    df = pd.DataFrame.from_dict(budget_tiers[tier], orient='index', columns=['Amount'])
    st.dataframe(df.style.format("${:,.0f}"))

    chart = px.pie(df.reset_index(), names='index', values='Amount', title=f"{tier} Budget Breakdown")
    st.plotly_chart(chart)

    summary = f"{tier} Wedding Budget Estimate\nTotal: ${tier_totals[tier]:,}\nPer Guest: ${tier_totals[tier] // guest_count:,}\n\nBreakdown:\n" + \
              "\n".join([f"{k}: ${v:,}" for k, v in budget_tiers[tier].items()])
    st.text_area(f"{tier} Summary:", summary, height=300)

st.markdown("\n💾 *Take a screenshot or print this page to save your budget breakdowns.*")

