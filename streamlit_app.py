import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
import os
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from pathlib import Path

# --- Initialize session state ---
if 'current_step' not in st.session_state:
    st.session_state.current_step = 1
if 'saved_scenarios' not in st.session_state:
    st.session_state.saved_scenarios = {}

# --- Streamlit Config ---
st.set_page_config(
    page_title="Vancouver Island Wedding Budget Estimator",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Style and Layout ---
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stProgress > div > div > div > div {
        background-color: #2e504c;
    }
    .stButton>button {
        background-color: #2e504c;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# --- Sidebar Navigation ---
with st.sidebar:
    st.title("Navigation")
    steps = {
        1: "Basic Information",
        2: "Experience Priorities",
        3: "Venue & Details",
        4: "Budget Results"
    }
    
    # Progress bar
    progress = (st.session_state.current_step - 1) / len(steps)
    st.progress(progress)
    st.markdown(f"**Current Step:** {steps[st.session_state.current_step]}")
    
    # Step navigation
    for step, name in steps.items():
        if st.button(f"Step {step}: {name}"):
            st.session_state.current_step = step
    
    # Reset button
    if st.button("🔄 Reset All Inputs"):
        for key in st.session_state.keys():
            if key not in ['current_step', 'saved_scenarios']:
                del st.session_state[key]
        st.success("All inputs have been reset!")

# --- Header ---
if os.path.exists("blk-MAIN.png"):
    logo = Image.open("blk-MAIN.png")
    st.image(logo, width=200)

st.title("💍 Vancouver Island Wedding Budget Estimator")

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
    "Officiant": [150, 600, 1500],
    "Ceremony Decor, Rentals, and AV": [500, 3000, 6000],
    "Venues (your event's backdrop & setting)": [2000, 7000, 20000],
    "Decor & Rentals (Furniture, decor, tent, etc.)": [1200, 4000, 8000],
    "Floral Design": [0, 0, 0],  # Calculated based on guest count
    "Music/Entertainment (DJ, Band, Photobooth, etc.)": [500, 3500, 6000],
    "Photography": [3000, 4500, 8000],
    "Videography": [2000, 5000, 8000],
    "Hair & Makeup": [1000, 1500, 2500],
    "Personal Florals (Bouquets, Boutonnieres, Crowns, etc.)": [800, 1500, 2500],
    "Wedding Attire": [2500, 6350, 12600],
    "Food": [10400, 15600, 27000],
    "Beverage": [4200, 6700, 13000],
    "Stationery": [0, 0, 0],  # Calculated based on guest count
    "Transportation": [800, 1800, 3000],
    "Planning Support": [1500, 2500, 4500],
    "Event Management": [1000, 2000, 3000],
    "Design Services": [1500, 3000, 6000],
    "Other (Signage, Stationery, Gifts, Favours, etc.)": [1200, 2500, 4500]
}

category_minimums = {
    "Officiant": 150,
    "Ceremony Decor, Rentals, and AV": 500,
    "Venues (your event's backdrop & setting)": 2000,
    "Decor & Rentals (Furniture, decor, tent, etc.)": 1500,
    "Photography": 1500,
    "Videography": 1500,
    "Hair & Makeup": 400,
    "Personal Florals (Bouquets, Boutonnieres, Crowns, etc.)": 400,
    "Food": 3000,
    "Beverage": 1000,
    "Stationery": 300,
    "Transportation": 300,
    "Planning Support": 1500,
    "Event Management": 1000,
    "Design Services": 1000,
    "Other (Signage, Stationery, Gifts, Favours, etc.)": 300
}

# --- Step 1: Basic Information ---
if st.session_state.current_step == 1:
    with st.expander("ℹ️ About This Tool", expanded=True):
        st.info("""
        This tool is meant to help you **start the conversation** around your wedding budget — not to be a precise quote.
        
        It uses estimated ranges based on real weddings and vendor averages across Vancouver Island, but actual prices may vary depending on:
        - 📅 Season
        - 🎨 Style
        - 📍 Location
        - 🌟 Vendor selection
        
        Take this as your planning launchpad, not your final spreadsheet 🌛
        """)
    
    st.header("Step 1: Basic Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Event Details")
        wedding_date = st.date_input(
            "Wedding Date",
            min_value=datetime.today(),
            help="Select your wedding date to account for seasonal pricing"
        )
        
        guest_count = st.number_input(
            "Guest Count",
            min_value=1,
            value=100,
            help="Enter the expected number of guests"
        )

    with col2:
        st.subheader("Wedding Party Details")
        dresses = st.number_input(
            "Wedding Party Dresses You're Paying For",
            min_value=0,
            value=0,
            help="Number of wedding party dresses you'll cover"
        )
        suits = st.number_input(
            "Wedding Party Suits You're Paying For",
            min_value=0,
            value=0,
            help="Number of wedding party suits you'll cover"
        )

    st.subheader("Beauty Services")
    col3, col4 = st.columns(2)
    
    with col3:
        marrier_hair = st.number_input(
            "Marriers Getting Hair Done",
            min_value=0,
            value=1,
            help="Number of marriers getting professional hair styling"
        )
        marrier_makeup = st.number_input(
            "Marriers Getting Makeup Done",
            min_value=0,
            value=1,
            help="Number of marriers getting professional makeup"
        )

    with col4:
        wp_hair = st.number_input(
            "Wedding Party Hair Services",
            min_value=0,
            value=0,
            help="Number of wedding party members getting hair done"
        )
        wp_makeup = st.number_input(
            "Wedding Party Makeup Services",
            min_value=0,
            value=0,
            help="Number of wedding party members getting makeup done"
        )

    if st.button("Next: Experience Priorities ➡️"):
        st.session_state.current_step = 2

# --- Step 2: Experience Priorities ---
elif st.session_state.current_step == 2:
    st.header("Step 2: Select Your Experience Priorities")
    
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

    st.markdown("### Your Wedding Experience Goals")
    for icon_title, desc in goals.items():
        st.markdown(f"**{icon_title}** — {desc}")

    top_3 = st.multiselect(
        "Select Your Top 3 Priorities",
        list(goals.keys()),
        max_selections=3,
        help="These will receive higher budget allocations"
    )
    
    lowest = st.multiselect(
        "Optional: Select Areas to Minimize",
        [g for g in goals if g not in top_3],
        help="These will receive lower budget allocations"
    )

    use_custom = st.checkbox(
        "🎛️ Advanced Customization",
        help="Customize which budget categories to include"
    )
    
    if use_custom:
        included_categories = st.multiselect(
            "Select Budget Categories to Include",
            categories,
            default=categories
        )
    else:
        included_categories = categories

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back to Basic Information"):
            st.session_state.current_step = 1
    with col2:
        if st.button("Next: Venue & Details ➡️"):
            st.session_state.current_step = 3

# --- Step 3: Venue and Floral Details ---
elif st.session_state.current_step == 3:
    st.header("Step 3: Venue and Event Details")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Venue Details")
        venue_type = st.selectbox(
            "What kind of venue are you planning?",
            ["At Home Wedding", "Standard Venue", "Luxury Venue/Hotel"],
            help="Different venue types have different base costs and requirements"
        )
        
        tent_needed = st.checkbox(
            "Will you need a tent?",
            help="Tenting can significantly impact your budget"
        )

    with col2:
        st.subheader("Design Elements")
        floral_level = st.selectbox(
            "How lush are your floral plans?",
            ["Minimal", "Medium", "Lush"],
            help="This affects both decor and personal florals budgets"
        )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back to Experience Priorities"):
            st.session_state.current_step = 2
    with col2:
        if st.button("Calculate Budget ➡️"):
            st.session_state.current_step = 4

# --- Step 4: Results ---
elif st.session_state.current_step == 4:
    st.header("Your Wedding Budget Estimate")
    
    # [Previous budget calculation logic here]
    
    # Save scenario feature
    with st.expander("💾 Save This Budget Scenario", expanded=False):
        scenario_name = st.text_input("Scenario Name", "My Wedding Budget")
        if st.button("Save Current Scenario"):
            st.session_state.saved_scenarios[scenario_name] = {
                'date': str(datetime.now()),
                'total': tier_totals,
                'breakdown': budget_tiers
            }
            st.success(f"Scenario '{scenario_name}' saved!")

    # Results tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "Summary",
        "Detailed Breakdown",
        "Visualizations",
        "Export Options"
    ])
    
    with tab1:
        st.subheader("Budget Summary")
        # [Summary content]
    
    with tab2:
        st.subheader("Detailed Cost Breakdown")
        # [Detailed breakdown content]
    
    with tab3:
        st.subheader("Budget Visualizations")
        # [Charts and graphs]
    
    with tab4:
        st.subheader("Export Options")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 Download as Excel"):
                pass  # Excel export logic
        with col2:
            if st.button("📄 Download as PDF"):
                pass  # PDF export logic

    if st.button("⬅️ Back to Venue & Details"):
        st.session_state.current_step = 3

# --- Footer ---
st.markdown("---")
st.markdown("""
<div style="text-align: center">
    <h2>Need More Help?</h2>
    <p>Book a consultation with our wedding planning experts!</p>
    <a href="https://intendedevents.ca/pages/contact-us" target="_blank">
        <button style="background-color: #2e504c; color: white; padding: 10px 20px; border: none; border-radius: 5px;">
            Contact Us
        </button>
    </a>
</div>
""", unsafe_allow_html=True) 
