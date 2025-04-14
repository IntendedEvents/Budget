import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
import os
import plotly.express as px

# --- Streamlit Config ---
st.set_page_config(page_title="Vancouver Island Wedding Budget Estimator", layout="centered")
if os.path.exists("blk-MAIN.png"):
    logo = Image.open("blk-MAIN.png")
    st.image(logo, width=200)

st.title("💍 Vancouver Island Wedding Budget Estimator")

st.markdown("""
This calculator is designed to support weddings with **guest counts of 30-200** and budgets ranging from **$20,000-$100,000+**.
It is not optimized for elopements, ultra-luxury weddings, or micro-celebrations with unique requirements.

For the most accurate budgeting and guidance, we recommend reviewing your results with a planner who knows your region and priorities well.

_Intended couples planning a Vancouver Island wedding can [contact us](https://intendedevents.ca/pages/contact-us) or follow us on [Instagram](https://instagram.com/intendedevents) for more planning advice and inspiration._
""")


st.info("""

# --- User Inputs: Venue & Floral Preferences (moved earlier to avoid NameError) ---

# --- Input layout using columns ---

use_custom = st.checkbox("🎛️ Advanced Customization: I only want to include specific elements in my budget (click ❌ to remove anything you’re not including)")
included_categories = categories.copy()
if use_custom:
    included_categories = st.multiselect("Included Budget Categories", categories, default=categories)

# --- Improved priority weightings to ensure top choices push values toward max ---
priority_weights = {
    "Essential": {"top": [0.1, 0.3, 0.6], "mid": [0.6, 0.3, 0.1], "bottom": [1.0, 0.0, 0.0]},
    "Enhanced": {"top": [0.0, 0.3, 0.7], "mid": [0.3, 0.4, 0.3], "bottom": [0.8, 0.2, 0.0]},
    "Elevated": {"top": [0.0, 0.1, 0.9], "mid": [0.2, 0.3, 0.5], "bottom": [0.5, 0.4, 0.1]}
}

scaling_factor = guest_count / 100
budget_tiers = {tier: {} for tier in priority_weights}
tier_totals = {}
category_priorities = {}

# Tent toggle
tent_needed = st.checkbox("Will you need a tent for your wedding?")

for cat in categories:
    goals_for_cat = category_to_goals.get(cat, [])
    if any(g in top_3 for g in goals_for_cat):
        category_priorities[cat] = "top"
    elif any(g in lowest for g in goals_for_cat):
        category_priorities[cat] = "bottom"
    else:
        category_priorities[cat] = "mid"

for tier, weights in priority_weights.items():
    total = 0
    goal_spend = {goal: 0 for goal in goals}
    for cat in categories:
        if cat not in included_categories:
            budget_tiers[tier][cat] = 0
            continue
                # Custom logic for Floral Design, Stationery, Tent
        if cat == "Floral Design":
            count = guest_count / 8
            min_val = 100 * count
            avg_val = 350 * count
            max_val = 800 * count
            g, b, bst = min_val, avg_val, max_val
        elif cat == "Stationery":
            g, b, bst = guest_count * 10, guest_count * 20, guest_count * 35
        else:
            g, b, bst = base_costs[cat]

        w = weights[category_priorities[cat]]
        value = (g * w[0] + b * w[1] + bst * w[2]) * scaling_factor

        if cat in category_minimums and cat in included_categories:
            value = max(value, category_minimums[cat])

        if cat == "Decor & Rentals (Furniture, decor, tent, etc.)" and tent_needed:
            sqft = guest_count * 12.5
            if sqft <= 800:
                base_tent_cost = 2500
            elif sqft <= 1500:
                base_tent_cost = 5000
            elif sqft <= 2500:
                base_tent_cost = 6500
            else:
                base_tent_cost = 8000

            if category_priorities[cat] == "top":
                base_tent_cost += 3000

            value += base_tent_cost
        if cat == "Hair & Makeup":
            value += (marrier_hair + wp_hair + marrier_makeup + wp_makeup) * 100
        if cat == "Wedding Attire":
            value += dresses * 250 + suits * 200
        value = round(value)
        budget_tiers[tier][cat] = value
        total += value
        for goal in category_to_goals.get(cat, []):
            goal_spend[goal] += value
    tier_totals[tier] = total
    budget_tiers[tier]["_goal_spend"] = goal_spend

# --- Output ---
st.markdown("---")
st.header("Estimated Budgets")

st.markdown("""



*Intended couples planning a Vancouver Island wedding can [contact us](https://intendedevents.ca/pages/contact-us) for a consultation or [follow us on Instagram](https://instagram.com/intendedevents) for more planning advice and inspiration.*
""")
for tier in ["Essential", "Enhanced", "Elevated"]:
    st.subheader(f"{tier} Budget")
    st.write(f"Total: ${tier_totals[tier]:,} | Per Guest: ${tier_totals[tier] // guest_count:,}/guest")
    df = pd.DataFrame.from_dict(
        {k: v for k, v in budget_tiers[tier].items() if k != "_goal_spend"},
        orient='index',
        columns=['Amount']
    )

    # Handle excluded categories visually and map for styling
    excluded = [cat for cat in df.index if cat not in included_categories]
    rename_map = {cat: f"⚪ {cat}" for cat in excluded if cat in df.index}
    df.rename(index=rename_map, inplace=True)

    # Drop hidden row safely
    if "_goal_spend" in df.index:
        df = df.drop("_goal_spend")

    try:
        styled = df.style.format("${:,.0f}")
        st.dataframe(styled)
    except Exception as e:
        st.warning("Couldn't format the table with styling. Showing raw values instead.")
        st.dataframe(df)

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

if tier == "Elevated":
    csv = df.to_csv().encode('utf-8')
    st.download_button(
        label=f"⬇️ Download {tier} Budget as CSV",
        data=csv,
        file_name=f'{tier.lower()}_budget.csv',
        mime='text/csv'
    )

st.markdown("""
## What’s Next?

If this feels like a helpful starting point, amazing!  
Take your results and review them with your wedding planner or someone with experience navigating local vendors and venues.

If you're planning a **Vancouver Island wedding**, this tool was created with *you* in mind — whether you're dreaming of forest elopements, coastal celebrations, or backyard parties with your people.

We are cheering you on from here!

[Contact Us](https://intendedevents.ca/pages/contact-us)  
[Follow on Instagram](https://instagram.com/intendedevents)
""")
