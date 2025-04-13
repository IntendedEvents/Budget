import streamlit as st
import pandas as pd
import numpy as np
import pyperclip
import matplotlib.pyplot as plt

# --- CATEGORY DATA WITH GROUPINGS, TOOLTIPS, AND DEFAULT MINIMUMS ---
category_groups = {
    "Venues & Setup": [
        ("Venues (your event's backdrop & setting)", "Covers ceremony & reception venue fees", 1500),
        ("Ceremony (Rentals, Decor, Officiant, etc.)", "Includes seating, decor, and your officiant", 1000),
        ("Decor & Rentals (Furniture, decor, tent, etc.)", "Furniture, lighting, linens, tents, and more", 1000),
    ],
    "Experience & Atmosphere": [
        ("Music/Entertainment (DJ, Band, Photobooth, etc.)", "Live music, DJs, or unique entertainment", 800),
        ("Photo/Video", "Photography and videography services", 2000),
        ("Hair & Makeup", "Beauty services for the wedding day", 500),
        ("Personal Florals (Bouquets, Boutonnieres, Crowns, etc.)", "Florals for the couple & wedding party", 400),
        ("Wedding Attire", "Wedding dress, suit, and accessories", 800),
    ],
    "Guest Experience": [
        ("Food", "Meals, desserts, and food experiences", 5000),
        ("Beverage", "Bar service, alcohol, and non-alcoholic drinks", 1000),
        ("Stationery", "Invitations, signage, menus, and more", 300),
        ("Transportation", "Shuttles, vintage cars, ferries, etc.", 300),
    ],
    "Planning & Extras": [
        ("Planner", "Planning, coordination, and support", 1000),
        ("Other (Signage, Stationery, Gifts, Favours, etc.)", "Things like favours, gifts, and signage", 300),
    ]
}

categories_info = sum(category_groups.values(), [])

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
    "Other (Signage, Stationery, Gifts, Favours, etc.)": [1000, 2000, 4000]
}

# --- STREAMLIT APP START ---
from PIL import Image

# Load and display custom logo
logo = Image.open("logo.png")
st.image(logo, width=200)

st.set_page_config(page_title="Wedding Budget Estimator", layout="centered")
st.title("\ud83d\udc8d Wedding Budget Estimator")

st.markdown("Enter your estimated guest count and rank your priorities. We'll show you what your budget could look like!")

guest_count = st.number_input("Guest Count", min_value=1, max_value=500, value=100)
wedding_party = st.number_input("Number of people in your wedding party", min_value=0, max_value=20, value=4)
include_attire = st.checkbox("We're paying for wedding party attire")
include_beauty = st.checkbox("We're paying for wedding party hair & makeup")

# Recommend general per-guest pricing tiers
st.markdown("---")
if guest_count:
    st.info(f"💡 For {guest_count} guests, average weddings often range from **${guest_count * 200:,} to ${guest_count * 600:,}** total. Your budget results will fall within or around this range depending on your priorities.")

st.markdown("---")

st.header("Step 1: Set Your Priorities")
st.markdown("Use the sliders to rank how important each category is to you (1 = low, 5 = high). Hover to learn more.")

priorities = {}
for group, items in category_groups.items():
    with st.expander(group):
        for category, tooltip, _ in items:
            priorities[category] = st.slider(category, 1, 5, 3, help=tooltip)

st.markdown("---")

# --- BUDGET TIER ESTIMATION ---
base_guests = 100
scaling_factor = guest_count / base_guests

budget_tiers = {"Essential": {}, "Enhanced": {}, "Elevated": {}}
tier_totals = {"Essential": 0, "Enhanced": 0, "Elevated": 0}

for tier_name, index in zip(["Essential", "Enhanced", "Elevated"], [0, 1, 2]):
    weights = np.array([priorities[cat] for cat, _, _ in categories_info])
    base_vals = np.array([base_costs[cat][index] * scaling_factor for cat, _, _ in categories_info])

    # Add cost for wedding party extras
    if include_attire:
        attire_index = [cat for cat, _, _ in categories_info].index("Wedding Attire")
        base_vals[attire_index] += wedding_party * 150  # Estimate $150 per person
    if include_beauty:
        beauty_index = [cat for cat, _, _ in categories_info].index("Hair & Makeup")
        base_vals[beauty_index] += wedding_party * 100  # Estimate $100 per person

    total = sum(base_vals)
    weighted_distribution = (weights / weights.sum()) * total

    for i, (cat, _, minimum) in enumerate(categories_info):
        value = max(round(weighted_distribution[i]), minimum)
        budget_tiers[tier_name][cat] = value
    tier_totals[tier_name] = sum(budget_tiers[tier_name].values())

# --- OUTPUT ---
st.header("Step 2: See Your Estimated Budgets")
for tier in ["Essential", "Enhanced", "Elevated"]:
    st.subheader(f"{tier} Budget")
    st.write(f"Estimated Total: ${tier_totals[tier]:,}  ")
    per_guest = tier_totals[tier] / guest_count
    st.write(f"Per Guest: ${per_guest:,.0f}")

    budget_df = pd.DataFrame.from_dict(budget_tiers[tier], orient='index', columns=['Amount'])
    st.dataframe(budget_df.style.format("${:,.0f}"))

    # --- Chart ---
    fig, ax = plt.subplots()
    budget_df.plot(kind='pie', y='Amount', ax=ax, legend=False, autopct='%1.1f%%', startangle=90)
    ax.set_ylabel("")
    ax.set_title(f"{tier} Budget Breakdown")
    st.pyplot(fig)

    # --- Shareable Text ---
    result_summary = f"{tier} Wedding Budget Estimate\nTotal: ${tier_totals[tier]:,}\nPer Guest: ${per_guest:,.0f}\n\nBreakdown:\n" + \
                     "\n".join([f"{cat}: ${amt:,}" for cat, amt in budget_tiers[tier].items()])
    st.text_area(f"{tier} Copyable Summary:", result_summary, height=300)

st.markdown("---")
st.markdown("\ud83d\udcc0 *To save your results, take a screenshot or print this page as a PDF.*")
