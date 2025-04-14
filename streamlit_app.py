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

Take this as your planning launchpad, not your final spreadsheet 💫
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

# --- Experience Goals & Mapping ---
goals = {
    "🌿 A Beautiful Atmosphere": "Creating a visually stunning space with decor, florals, and lighting",
    "💍 A Meaningful Ceremony": "Prioritizing the emotional heart of your day — your vows and the setting",
    "🍽️ Incredible Food & Drink": "Ensuring guests are wowed by the meal, drinks, and overall experience",
    "📸 Memories that Last Forever": "Capturing your day through photography and video",
    "🛋️ A Comfortable, Seamless Experience": "Guests feel cared for and everything flows smoothly",
    "🎶 A Great Party & Vibe": "Bringing the energy with music, dancing, and unforgettable moments",
    "💄 Looking and Feeling Your Best": "Style, beauty, and confidence for you and your people",
    "🧘 Stress-Free Planning": "Ongoing support and logistics that remove overwhelm",
    "🎨 A Wedding That Feels and Flows Beautifully": "Design, flow, and cohesive aesthetic throughout the day",
    "✨ A Unique and Personalized Experience": "Touches that tell your story, from signage to stationery"
}

category_to_goals = {
    "Officiant": ["💍 A Meaningful Ceremony"],
    "Ceremony Decor, Rentals, and AV": ["🌿 A Beautiful Atmosphere", "💍 A Meaningful Ceremony"],
    "Venues (your event's backdrop & setting)": ["🎨 A Wedding That Feels and Flows Beautifully"],
    "Decor & Rentals (Furniture, decor, tent, etc.)": ["🌿 A Beautiful Atmosphere"],
    "Floral Design": ["🌿 A Beautiful Atmosphere"],
    "Music/Entertainment (DJ, Band, Photobooth, etc.)": ["🎶 A Great Party & Vibe"],
    "Photography": ["📸 Memories that Last Forever"],
    "Videography": ["📸 Memories that Last Forever"],
    "Hair & Makeup": ["💄 Looking and Feeling Your Best"],
    "Personal Florals (Bouquets, Boutonnieres, Crowns, etc.)": ["🌿 A Beautiful Atmosphere"],
    "Wedding Attire": ["💄 Looking and Feeling Your Best"],
    "Food": ["🍽️ Incredible Food & Drink"],
    "Beverage": ["🍽️ Incredible Food & Drink"],
    "Stationery": ["✨ A Unique and Personalized Experience"],
    "Transportation": ["🛋️ A Comfortable, Seamless Experience", "🎨 A Wedding That Feels and Flows Beautifully"],
    "Planning Support": ["🧘 Stress-Free Planning", "🎨 A Wedding That Feels and Flows Beautifully"],
    "Event Management": ["🧘 Stress-Free Planning", "🛋️ A Comfortable, Seamless Experience"],
    "Design Services": ["🎨 A Wedding That Feels and Flows Beautifully"],
    "Other (Signage, Stationery, Gifts, Favours, etc.)": ["✨ A Unique and Personalized Experience"]
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
for icon_title, desc in goals.items():
    st.markdown(f"**{icon_title}** — {desc}")

top_3 = st.multiselect("Top 3 Priorities", list(goals.keys()), max_selections=3)
lowest = st.multiselect("Optional: Do Not Prioritize", [g for g in goals if g not in top_3])

st.markdown("---")
use_custom = st.checkbox("🎛️ Advanced Customization: I only want to include specific elements in my budget (click ❌ to remove anything you’re not including)")
included_categories = categories.copy()
if use_custom:
    included_categories = st.multiselect("Included Budget Categories", categories, default=categories)

# --- Budget Calculation ---
priority_weights = {
    "Essential": {"top": [0.6, 0.4, 0.0], "mid": [0.8, 0.2, 0.0], "bottom": [1.0, 0.0, 0.0]},
    "Enhanced": {"top": [0.3, 0.7, 0.0], "mid": [0.0, 0.5, 0.5], "bottom": [0.8, 0.2, 0.0]},
    "Elevated": {"top": [0.0, 0.1, 0.9], "mid": [0.0, 0.2, 0.8], "bottom": [0.5, 0.5, 0.0]}
}

scaling_factor = guest_count / 100
budget_tiers = {tier: {} for tier in priority_weights}
tier_totals = {}
category_priorities = {}

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
        g, b, bst = base_costs[cat]
        w = weights[category_priorities[cat]]
        value = (g * w[0] + b * w[1] + bst * w[2]) * scaling_factor
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
for tier in ["Essential", "Enhanced", "Elevated"]:
    st.subheader(f"{tier} Budget")
    st.write(f"Total: ${tier_totals[tier]:,} | Per Guest: ${tier_totals[tier] // guest_count:,}/guest")
    df = pd.DataFrame.from_dict(budget_tiers[tier], orient='index', columns=['Amount'])
    excluded = [cat for cat in df.index if cat not in included_categories]
    for cat in excluded:
        df.rename(index={cat: f"⚪ {cat}"}, inplace=True)
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

st.markdown("💾 *Take a screenshot or print this page to save your budget breakdowns.*")

st.markdown("""
## What’s Next?

If this feels like a helpful starting point — amazing!  
Take your results and review them with your wedding planner or someone with experience navigating local vendors and venues.

If you’re planning a **Vancouver Island wedding**, this tool was created with *you* in mind — whether you're dreaming of forest elopements, coastal celebrations, or backyard parties with your people.

We’re cheering you on from here 💛  
---  
📬 [Contact Us](https://intendedevents.ca/pages/contact-us)  
📸 [Follow on Instagram](https://instagram.com/intendedevents)
""")
