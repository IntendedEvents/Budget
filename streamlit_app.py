
import streamlit as st
import pandas as pd
import numpy as np

# --- CATEGORY DATA ---
categories = [
    "Ceremony Venue Fees",
    "Reception Venue Fees",
    "Ceremony (Rentals, Decor, Officiant, etc.)",
    "Wedding Attire",
    "Food",
    "Beverage",
    "Stationery",
    "Transportation",
]

# Estimated base costs for 100 guests
base_costs = {
    "Ceremony Venue Fees": [1000, 2500, 4000],
    "Reception Venue Fees": [2000, 4500, 8000],
    "Ceremony (Rentals, Decor, Officiant, etc.)": [3600, 6350, 11683],
    "Wedding Attire": [2500, 6350, 12600],
    "Food": [10400, 15600, 25900],
    "Beverage": [4200, 6700, 12200],
    "Stationery": [1000, 2000, 3500],
    "Transportation": [800, 1800, 3000],
}

# --- STREAMLIT APP START ---
st.set_page_config(page_title="Wedding Budget Estimator", layout="centered")
st.title("💍 Wedding Budget Estimator")

st.markdown("Enter your estimated guest count and rank your priorities. We'll show you what your budget could look like!")

guest_count = st.number_input("Guest Count", min_value=1, max_value=500, value=100)

st.markdown("---")

st.header("Step 1: Set Your Priorities")
st.markdown("Use the sliders to rank how important each category is to you (1 = low, 5 = high).")

priorities = {}
for category in categories:
    priorities[category] = st.slider(category, 1, 5, 3)

st.markdown("---")

# --- BUDGET TIER ESTIMATION ---
base_guests = 100
scaling_factor = guest_count / base_guests

budget_tiers = {"Essential": {}, "Enhanced": {}, "Elevated": {}}
tier_totals = {"Essential": 0, "Enhanced": 0, "Elevated": 0}

for tier_name, index in zip(["Essential", "Enhanced", "Elevated"], [0, 1, 2]):
    weights = np.array([priorities[cat] for cat in categories])
    base_vals = np.array([base_costs[cat][index] * scaling_factor for cat in categories])
    total = sum(base_vals)
    weighted_distribution = (weights / weights.sum()) * total

    for cat, val in zip(categories, weighted_distribution):
        budget_tiers[tier_name][cat] = round(val)
    tier_totals[tier_name] = round(total)

# --- OUTPUT ---
st.header("Step 2: See Your Estimated Budgets")
for tier in ["Essential", "Enhanced", "Elevated"]:
    st.subheader(f"{tier} Budget")
    st.write(f"Estimated Total: ${tier_totals[tier]:,}")
    st.dataframe(pd.DataFrame.from_dict(budget_tiers[tier], orient='index', columns=['Amount']).style.format("${:,.0f}"))

st.markdown("---")
st.markdown("💾 *To save your results, take a screenshot or print this page as a PDF.*")
