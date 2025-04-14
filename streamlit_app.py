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
categories = [
    "Officiant",
    "Ceremony Decor, Rentals, and AV",
    "Venues (your event's backdrop & setting)",
    "Decor & Rentals (Furniture, decor, tent, etc.)",
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
    "Other (Signage, Stationery, Gifts, Favours, etc.)"
]

# Base costs: [Good, Better, Best]
base_costs = {
    "Officiant": [400, 600, 1000],
    "Ceremony Decor, Rentals, and AV": [1200, 3000, 6000],
    "Venues (your event's backdrop & setting)": [3000, 7000, 12000],
    "Decor & Rentals (Furniture, decor, tent, etc.)": [2500, 4500, 8000],
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
    "Other (Signage, Stationery, Gifts, Favours, etc.)": [1000, 2000, 4000]
}

# Experience goal mapping
experience_goals = {
    "A Beautiful Atmosphere": ["Decor & Rentals (Furniture, decor, tent, etc.)", "Personal Florals (Bouquets, Boutonnieres, Crowns, etc.)", "Ceremony Decor, Rentals, and AV"],
    "A Meaningful Ceremony": ["Officiant", "Ceremony Decor, Rentals, and AV"],
    "Incredible Food & Drink": ["Food", "Beverage"],
    "Memories that Last Forever": ["Photography", "Videography"],
    "A Comfortable, Seamless Guest Experience": ["Transportation", "Planning Support", "Event Management"],
    "A Great Party & Vibe": ["Music/Entertainment (DJ, Band, Photobooth, etc.)"],
    "Looking and Feeling Your Best": ["Hair & Makeup", "Wedding Attire"],
    "Stress-Free Planning": ["Planning Support", "Event Management"],
    "A Unique and Personalized Experience": ["Stationery", "Other (Signage, Stationery, Gifts, Favours, etc.)"]
}

# --- Inputs ---
st.markdown("Enter your wedding details below. We'll calculate three budget levels based on your unique priorities!")

guest_count = st.number_input("Guest Count", min_value=1, value=100)
dresses = st.number_input("Wedding Party Dresses You're Paying For", min_value=0, value=0)
suits = st.number_input("Wedding Party Suits You're Paying For", min_value=0, value=0)
marrier_hair = st.number_input("How many marriers are getting hair done?", min_value=0, value=1)
marrier_makeup = st.number_input("How many marriers are getting makeup done?", min_value=0, value=1)
wp_hair = st.number_input("Wedding party hair services you're covering", min_value=0, value=0)
wp_makeup = st.number_input("Wedding party makeup services you're covering", min_value=0, value=0)

st.markdown("---")
st.subheader("Step 2: Select Your Experience Priorities")
st.markdown("Choose the top 3 experience goals that matter most to you. Optionally, mark any that you don't want to prioritize.")

top_3 = st.multiselect("Top 3 Priorities", list(experience_goals.keys()), max_selections=3)
lowest = st.multiselect("Optional: Do Not Prioritize", [g for g in experience_goals.keys() if g not in top_3])

# Map categories to priority based on experience goals
priority_map = {cat: "mid" for cat in categories}
for goal in top_3:
    for cat in experience_goals[goal]:
        priority_map[cat] = "top"
for goal in lowest:
    for cat in experience_goals[goal]:
        if priority_map.get(cat) != "top":
            priority_map[cat] = "bottom"

# Priority logic map
priority_weights = {
    "Essential": {"top": [0.6, 0.4, 0.0], "mid": [0.8, 0.2, 0.0], "bottom": [1.0, 0.0, 0.0]},
    "Enhanced": {"top": [0.3, 0.7, 0.0], "mid": [0.0, 0.5, 0.5], "bottom": [0.8, 0.2, 0.0]},
    "Elevated": {"top": [0.0, 0.1, 0.9], "mid": [0.0, 0.2, 0.8], "bottom": [0.5, 0.5, 0.0]}
}

# Budget calculation
scaling_factor = guest_count / 100
budget_tiers = {"Essential": {}, "Enhanced": {}, "Elevated": {}}
tier_totals = {}

for tier in budget_tiers:
    total = 0
    for cat in categories:
        g, b, bst = base_costs[cat]
        w = priority_weights[tier][priority_map[cat]]
        value = (g * w[0] + b * w[1] + bst * w[2]) * scaling_factor

        if cat == "Hair & Makeup":
            value += (marrier_hair + wp_hair + marrier_makeup + wp_makeup) * 100
        if cat == "Wedding Attire":
            value += dresses * 250 + suits * 200

        value = round(value)
        budget_tiers[tier][cat] = value
        total += value

    tier_totals[tier] = total

# Output
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

# Experience Key
st.markdown("---")
st.subheader("Experience Goal Key")
for goal, cats in experience_goals.items():
    st.markdown(f"**{goal}:** includes {', '.join(cats)}")

st.markdown("\n💾 *Take a screenshot or print this page to save your budget breakdowns.*")
