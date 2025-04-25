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
from io import BytesIO
from fpdf import FPDF
import calendar

# Define goals dictionary
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

# Initialize session state variables
if 'current_step' not in st.session_state:
    st.session_state.current_step = 1
if 'saved_scenarios' not in st.session_state:
    st.session_state.saved_scenarios = {}
if 'wedding_date' not in st.session_state:
    st.session_state.wedding_date = datetime.today()
if 'guest_count' not in st.session_state:
    st.session_state.guest_count = 100
if 'dresses' not in st.session_state:
    st.session_state.dresses = 0
if 'suits' not in st.session_state:
    st.session_state.suits = 0
if 'marrier_hair' not in st.session_state:
    st.session_state.marrier_hair = 1
if 'marrier_makeup' not in st.session_state:
    st.session_state.marrier_makeup = 1
if 'wp_hair' not in st.session_state:
    st.session_state.wp_hair = 0
if 'wp_makeup' not in st.session_state:
    st.session_state.wp_makeup = 0
if 'top_3' not in st.session_state:
    st.session_state.top_3 = []
if 'lowest' not in st.session_state:
    st.session_state.lowest = []
if 'included_categories' not in st.session_state:
    st.session_state.included_categories = None
if 'venue_type' not in st.session_state:
    st.session_state.venue_type = "Standard Venue"
if 'tent_needed' not in st.session_state:
    st.session_state.tent_needed = False
if 'floral_level' not in st.session_state:
    st.session_state.floral_level = "Medium"
if 'last_modified' not in st.session_state:
    st.session_state.last_modified = datetime.now().isoformat()
if 'button_clicked' not in st.session_state:
    st.session_state.button_clicked = False

# --- State Management ---
DEFAULT_VALUES = {
    'current_step': 1,
    'saved_scenarios': {},
    'wedding_date': datetime.today(),
    'guest_count': 100,
    'dresses': 0,
    'suits': 0,
    'marrier_hair': 1,
    'marrier_makeup': 1,
    'wp_hair': 0,
    'wp_makeup': 0,
    'top_3': [],
    'lowest': [],
    'included_categories': None,  # Will be set after categories are defined
    'venue_type': "Standard Venue",
    'tent_needed': False,
    'floral_level': "Medium",
    'last_modified': datetime.now().isoformat()
}

def initialize_session_state():
    """Initialize or reset session state with default values."""
    for key, value in DEFAULT_VALUES.items():
        if key not in st.session_state:
            st.session_state[key] = value

def reset_session_state():
    """Reset all session state values to defaults."""
    for key, value in DEFAULT_VALUES.items():
        st.session_state[key] = value
    st.session_state.last_modified = datetime.now().isoformat()

def save_current_state():
    """Save current state as a scenario."""
    current_state = {
        key: st.session_state[key] 
        for key in DEFAULT_VALUES.keys() 
        if key not in ['current_step', 'saved_scenarios']
    }
    return current_state

def load_state(saved_state):
    """Load a saved state into session state."""
    for key, value in saved_state.items():
        if key in DEFAULT_VALUES:
            st.session_state[key] = value
    st.session_state.last_modified = datetime.now().isoformat()

def handle_save_scenario(location):
    """Handle saving a scenario and prevent double-clicks"""
    if not st.session_state.button_clicked:
        st.session_state.button_clicked = True
        scenario_name = st.session_state[f"{location}_scenario_name"]
        if location == "sidebar":
            current_state = save_current_state()
            st.session_state.saved_scenarios[scenario_name] = {
                'date': datetime.now().isoformat(),
                'state': current_state
            }
        else:  # results
            st.session_state.saved_scenarios[scenario_name] = {
                'date': str(datetime.now()),
                'total': tier_totals,
                'breakdown': budget_tiers
            }
        st.success(f"Scenario '{scenario_name}' saved!")
        st.session_state.button_clicked = False

# --- Pricing Adjustments ---
def get_seasonal_discount(date):
    """Calculate seasonal discount based on month and day of week."""
    month = date.month
    day_of_week = date.weekday()  # Monday = 0, Sunday = 6
    
    base_discount = 0
    
    # Off-season discount (November through March)
    if month in [11, 12, 1, 2, 3]:
        base_discount += 0.10  # 10% off for off-season
    
    # Day of week discount
    if day_of_week == 6:  # Sunday
        base_discount += 0.10  # 10% off for Sunday
    elif day_of_week < 5:  # Monday through Thursday
        base_discount += 0.10  # 10% off for weekdays
    
    # Cap total discount at 20%
    return min(base_discount, 0.20)

def format_currency(amount):
    """Format amount as currency string."""
    return f"${amount:,.2f}"

class WeddingBudgetPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        
    def header(self):
        # Add logo if exists
        if os.path.exists("blk-MAIN.png"):
            self.image("blk-MAIN.png", 10, 8, 33)
        self.set_font('Arial', 'B', 20)
        self.cell(0, 10, 'Wedding Budget Summary', 0, 1, 'C')
        self.ln(10)
        
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
        
    def chapter_title(self, title):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(4)
        
    def chapter_body(self, body):
        self.set_font('Arial', '', 12)
        self.multi_cell(0, 10, body)
        self.ln()

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
    
    st.markdown("---")
    
    # Scenario Management
    st.subheader("💾 Scenario Management")
    
    # Save current scenario in sidebar
    scenario_name = st.text_input("Scenario Name", "My Wedding Budget", key="sidebar_scenario_name")
    if st.button("Save Current Scenario", key="sidebar_save_button", on_click=handle_save_scenario, args=("sidebar",)):
        pass  # The actual saving is handled in the callback
    
    # Load saved scenario
    if st.session_state.saved_scenarios:
        st.markdown("### Load Saved Scenario")
        scenario_to_load = st.selectbox(
            "Select a scenario to load",
            options=list(st.session_state.saved_scenarios.keys()),
            key="load_scenario_select"
        )
        if st.button("Load Selected Scenario", key="load_scenario_button"):
            saved_data = st.session_state.saved_scenarios[scenario_to_load]
            if 'state' in saved_data:  # Sidebar format
                load_state(saved_data['state'])
            else:  # Results format - need to convert to state format
                state_data = {
                    'wedding_date': st.session_state.wedding_date,
                    'guest_count': st.session_state.guest_count,
                    'dresses': st.session_state.dresses,
                    'suits': st.session_state.suits,
                    'marrier_hair': st.session_state.marrier_hair,
                    'marrier_makeup': st.session_state.marrier_makeup,
                    'wp_hair': st.session_state.wp_hair,
                    'wp_makeup': st.session_state.wp_makeup,
                    'top_3': st.session_state.top_3,
                    'lowest': st.session_state.lowest,
                    'included_categories': st.session_state.included_categories,
                    'venue_type': st.session_state.venue_type,
                    'tent_needed': st.session_state.tent_needed,
                    'floral_level': st.session_state.floral_level,
                    'last_modified': saved_data['date']
                }
                load_state(state_data)
            st.success(f"Loaded scenario: {scenario_to_load}")
            st.rerun()  # Rerun to update all calculations with new state
        
        if st.button("Delete Selected Scenario", key="delete_scenario_button"):
            del st.session_state.saved_scenarios[scenario_to_load]
            st.success(f"Deleted scenario: {scenario_to_load}")
    
    st.markdown("---")
    
    # Reset options
    st.subheader("🔄 Reset Options")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Reset All"):
            reset_session_state()
            st.success("All inputs have been reset!")
    with col2:
        if st.button("Clear Scenarios"):
            st.session_state.saved_scenarios = {}
            st.success("All saved scenarios cleared!")

    # Show last modified time
    st.markdown("---")
    last_modified = datetime.fromisoformat(st.session_state.last_modified)
    st.caption(f"Last modified: {last_modified.strftime('%Y-%m-%d %H:%M:%S')}")

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

# Update DEFAULT_VALUES with categories
DEFAULT_VALUES['included_categories'] = categories.copy()

# Initialize session state
initialize_session_state()

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
        st.session_state.wedding_date = st.date_input(
            "Wedding Date",
            value=st.session_state.wedding_date,
            min_value=datetime.today(),
            help="Select your wedding date to account for seasonal pricing"
        )
        
        st.session_state.guest_count = st.number_input(
            "Guest Count",
            min_value=1,
            value=st.session_state.guest_count,
            help="Enter the expected number of guests"
        )

    with col2:
        st.subheader("Wedding Party Details")
        st.session_state.dresses = st.number_input(
            "Wedding Party Dresses You're Paying For",
            min_value=0,
            value=st.session_state.dresses,
            help="Number of wedding party dresses you'll cover"
        )
        st.session_state.suits = st.number_input(
            "Wedding Party Suits You're Paying For",
            min_value=0,
            value=st.session_state.suits,
            help="Number of wedding party suits you'll cover"
        )

    st.subheader("Beauty Services")
    col3, col4 = st.columns(2)
    
    with col3:
        st.session_state.marrier_hair = st.number_input(
            "Marriers Getting Hair Done",
            min_value=0,
            value=st.session_state.marrier_hair,
            help="Number of marriers getting professional hair styling"
        )
        st.session_state.marrier_makeup = st.number_input(
            "Marriers Getting Makeup Done",
            min_value=0,
            value=st.session_state.marrier_makeup,
            help="Number of marriers getting professional makeup"
        )

    with col4:
        st.session_state.wp_hair = st.number_input(
            "Wedding Party Hair Services",
            min_value=0,
            value=st.session_state.wp_hair,
            help="Number of wedding party members getting hair done"
        )
        st.session_state.wp_makeup = st.number_input(
            "Wedding Party Makeup Services",
            min_value=0,
            value=st.session_state.wp_makeup,
            help="Number of wedding party members getting makeup done"
        )

    if st.session_state.wedding_date:
        discount = get_seasonal_discount(st.session_state.wedding_date)
        if discount > 0:
            reasons = []
            if st.session_state.wedding_date.month in [11, 12, 1, 2, 3]:
                reasons.append("off-season (November-March)")
            if st.session_state.wedding_date.weekday() == 6:
                reasons.append("Sunday")
            elif st.session_state.wedding_date.weekday() < 5:
                reasons.append("weekday")
            
            message = f"💰 {discount * 100:.0f}% off has been applied based on potential {' and '.join(reasons)} savings"
            st.info(message)

    if st.button("Next: Experience Priorities ➡️"):
        st.session_state.current_step = 2

# --- Step 2: Experience Priorities ---
elif st.session_state.current_step == 2:
    st.header("Step 2: Select Your Experience Priorities")
    
    st.markdown("### Your Wedding Experience Goals")
    for icon_title, desc in goals.items():
        st.markdown(f"**{icon_title}** — {desc}")

    st.session_state.top_3 = st.multiselect(
        "Select Your Top 3 Priorities",
        list(goals.keys()),
        default=st.session_state.top_3,
        max_selections=3,
        help="These will receive higher budget allocations"
    )
    
    st.session_state.lowest = st.multiselect(
        "Optional: Select Areas to Minimize",
        [g for g in goals if g not in st.session_state.top_3],
        default=st.session_state.lowest,
        help="These will receive lower budget allocations"
    )

    use_custom = st.checkbox(
        "🎛️ Advanced Customization",
        help="Customize which budget categories to include"
    )
    
    if use_custom:
        st.session_state.included_categories = st.multiselect(
            "Select Budget Categories to Include",
            categories,
            default=st.session_state.included_categories
        )
    else:
        st.session_state.included_categories = categories

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
        st.session_state.venue_type = st.selectbox(
            "What kind of venue are you planning?",
            ["At Home Wedding", "Standard Venue", "Luxury Venue/Hotel"],
            index=["At Home Wedding", "Standard Venue", "Luxury Venue/Hotel"].index(st.session_state.venue_type),
            help="Different venue types have different base costs and requirements",
            key="venue_type_select"
        )
        
        st.session_state.tent_needed = st.checkbox(
            "Will you need a tent?",
            value=st.session_state.tent_needed,
            help="Tenting can significantly impact your budget"
        )

    with col2:
        st.subheader("Design Elements")
        st.session_state.floral_level = st.selectbox(
            "How lush are your floral plans?",
            ["Minimal", "Medium", "Lush"],
            index=["Minimal", "Medium", "Lush"].index(st.session_state.floral_level),
            help="This affects both decor and personal florals budgets",
            key="floral_level_select"
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
    
    # Calculate budget tiers
    scaling_factor = st.session_state.guest_count / 100
    seasonal_discount = get_seasonal_discount(st.session_state.wedding_date)
    budget_tiers = {tier: {} for tier in ["Essentials Only", "Balanced", "Luxe"]}
    tier_totals = {}
    category_priorities = {}

    # Priority weights for different tiers
    priority_weights = {
        "Essentials Only": {  # Previously "Budget"
            "top": [0.8, 0.2, 0.0],  # Even top priorities stay mostly in minimum range
            "mid": [1.0, 0.0, 0.0],  # Mid priorities at minimum
            "bottom": [1.0, 0.0, 0.0]  # Bottom priorities at minimum
        },
        "Balanced": {  # Previously "Essential"
            "top": [0.2, 0.6, 0.2],  # More emphasis on medium range
            "mid": [0.7, 0.3, 0.0],  # Some medium range for mid priorities
            "bottom": [1.0, 0.0, 0.0]  # Keep low priorities at minimum
        },
        "Luxe": {  # Combines best of Enhanced/Elevated
            "top": [0.0, 0.2, 0.8],  # Heavy emphasis on high-end for priorities
            "mid": [0.3, 0.4, 0.3],  # Balanced for mid-range items
            "bottom": [0.7, 0.3, 0.0]  # Keep low priorities modest
        }
    }

    # Determine category priorities based on goals
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
        "Transportation": ["🛋️ A Comfortable, Seamless Experience"],
        "Planning Support": ["🧘 Stress-Free Planning"],
        "Event Management": ["🧘 Stress-Free Planning", "🛋️ A Comfortable, Seamless Experience"],
        "Design Services": ["🎨 A Wedding That Feels and Flows Beautifully"],
        "Other (Signage, Stationery, Gifts, Favours, etc.)": ["✨ A Unique and Personalized Experience"]
    }

    for cat in categories:
        goals_for_cat = category_to_goals.get(cat, [])
        if any(g in st.session_state.top_3 for g in goals_for_cat):
            category_priorities[cat] = "top"
        elif any(g in st.session_state.lowest for g in goals_for_cat):
            category_priorities[cat] = "bottom"
        else:
            category_priorities[cat] = "mid"

    # Calculate budgets for each tier
    for tier in ["Essentials Only", "Balanced", "Luxe"]:
        total = 0
        goal_spend = {goal: 0 for goal in goals}
        
        for cat in categories:
            if cat not in st.session_state.included_categories:
                budget_tiers[tier][cat] = 0
                continue

            # Custom logic for special categories
            if cat == "Floral Design":
                table_count = st.session_state.guest_count / 8
                row_count = int(np.ceil(st.session_state.guest_count / 6))
                focal_point_count = {
                    "Essentials Only": 1,
                    "Balanced": 2,
                    "Luxe": 3
                }[tier]

                if st.session_state.floral_level == "Minimal":
                    centrepiece_cost = [50, 150, 300]
                    aisle_marker_cost = [50, 100, 150]
                    focal_point_unit = 300
                elif st.session_state.floral_level == "Medium":
                    centrepiece_cost = [100, 350, 600]
                    aisle_marker_cost = [100, 250, 400]
                    focal_point_unit = 800
                else:  # Lush
                    centrepiece_cost = [200, 500, 800]
                    aisle_marker_cost = [200, 500, 800]
                    focal_point_unit = 1500

                g = table_count * centrepiece_cost[0] + row_count * aisle_marker_cost[0] + focal_point_count * focal_point_unit
                b = table_count * centrepiece_cost[1] + row_count * aisle_marker_cost[1] + focal_point_count * focal_point_unit
                bst = table_count * centrepiece_cost[2] + row_count * aisle_marker_cost[2] + focal_point_count * focal_point_unit

            elif cat == "Venues (your event's backdrop & setting)":
                if st.session_state.venue_type == "At Home Wedding":
                    g, b, bst = 0, 2000, 4000
                elif st.session_state.venue_type == "Standard Venue":
                    g, b, bst = 5000, 8000, 12000
                else:  # Luxury Venue/Hotel
                    g, b, bst = 9000, 14000, 20000

            elif cat == "Stationery":
                g, b, bst = st.session_state.guest_count * 10, st.session_state.guest_count * 20, st.session_state.guest_count * 35

            else:
                g, b, bst = base_costs[cat]

            # Apply priority weights
            w = priority_weights[tier][category_priorities[cat]]
            value = (g * w[0] + b * w[1] + bst * w[2]) * scaling_factor

            # Apply minimum values
            if cat in category_minimums:
                value = max(value, category_minimums[cat])

            # Add tent cost if needed
            if cat == "Decor & Rentals (Furniture, decor, tent, etc.)" and st.session_state.tent_needed:
                sqft = st.session_state.guest_count * 12.5
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

            # Add beauty service costs
            if cat == "Hair & Makeup":
                value += (st.session_state.marrier_hair + st.session_state.wp_hair + st.session_state.marrier_makeup + st.session_state.wp_makeup) * 200

            # Add wedding party attire costs
            if cat == "Wedding Attire":
                value += st.session_state.dresses * 250 + st.session_state.suits * 200

            # Apply seasonal discount if applicable
            if cat not in ["Food", "Beverage"]:  # Don't discount food and beverage
                value = value * (1 - seasonal_discount)

            # Store the calculated value
            value = round(value)
            budget_tiers[tier][cat] = value
            total += value

            # Add to goal spending
            for goal in category_to_goals.get(cat, []):
                goal_spend[goal] += value

        tier_totals[tier] = total
        budget_tiers[tier]["_goal_spend"] = goal_spend

    # Save scenario feature in expander
    with st.expander("💾 Save This Budget Scenario", expanded=False):
        scenario_name = st.text_input("Scenario Name", "My Wedding Budget", key="results_scenario_name")
        if st.button("Save Current Scenario", key="results_save_button", on_click=handle_save_scenario, args=("results",)):
            pass  # The actual saving is handled in the callback

    # Results tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "Summary",
        "Detailed Breakdown",
        "Visualizations",
        "Export Options"
    ])
    
    with tab1:
        st.subheader("Budget Summary")
        
        # Add budget optimization tips
        with st.expander("💡 Budget Optimization Tips", expanded=True):
            st.markdown("### Tips to Optimize Your Budget")
            
            # General tips
            st.markdown("""
            **General Cost-Saving Strategies:**
            - 📅 Consider an off-season or weekday wedding (can save up to 20%)
            - 👥 Be strategic with guest count - each guest impacts multiple budget categories
            - 🎯 Focus spending on your top priorities and minimize others
            """)
            
            # Priority-specific tips
            st.markdown("### Tips Based on Your Priorities")
            for priority in st.session_state.top_3:
                if priority == "🌿 A Beautiful Atmosphere":
                    st.markdown("""
                    - Choose a naturally beautiful venue to reduce decor needs
                    - Focus on key focal points rather than decorating every space
                    - Consider renting decor items instead of purchasing
                    - Use seasonal flowers to reduce floral costs
                    """)
                elif priority == "💍 A Meaningful Ceremony":
                    st.markdown("""
                    - Invest in a great officiant but keep ceremony decor simple
                    - Consider an outdoor ceremony in a beautiful natural setting
                    - Focus on personal touches rather than elaborate decorations
                    """)
                elif priority == "🍽️ Incredible Food & Drink":
                    st.markdown("""
                    - Consider a lunch or brunch reception for lower food costs
                    - Opt for passed appetizers over stationed hors d'oeuvres
                    - Choose a venue that allows outside catering
                    - Consider a limited bar rather than full open bar
                    """)
                elif priority == "📸 Memories that Last Forever":
                    st.markdown("""
                    - Book a great photographer but maybe skip videography
                    - Consider a shorter coverage time with key moments prioritized
                    - Ask about small wedding packages or off-season rates
                    """)
                elif priority == "🛋️ A Comfortable, Seamless Experience":
                    st.markdown("""
                    - Focus on essential rentals and skip purely decorative items
                    - Consider all-inclusive venues to reduce coordination needs
                    - Invest in day-of coordination but maybe skip full planning
                    """)
                elif priority == "🎶 A Great Party & Vibe":
                    st.markdown("""
                    - Choose a DJ over a band for lower entertainment costs
                    - Create your own playlist for cocktail hour/dinner
                    - Skip extra entertainment add-ons like photo booths
                    """)
                elif priority == "💄 Looking and Feeling Your Best":
                    st.markdown("""
                    - Consider having hair OR makeup done professionally, not both
                    - Look for sample sales or pre-owned attire
                    - Limit the number of wedding party members needing services
                    """)
                elif priority == "🧘 Stress-Free Planning":
                    st.markdown("""
                    - Consider a month-of coordinator instead of full planning
                    - Use online planning tools and templates
                    - Choose vendors who are easy to work with, even if slightly more expensive
                    """)
                elif priority == "🎨 A Wedding That Feels and Flows Beautifully":
                    st.markdown("""
                    - Focus on a strong color palette that ties everything together
                    - Choose a venue that already matches your style
                    - DIY simple design elements but outsource complex ones
                    """)
                elif priority == "✨ A Unique and Personalized Experience":
                    st.markdown("""
                    - Focus on a few impactful personal touches rather than many small ones
                    - DIY personalized elements that don't require special skills
                    - Digital invitations or simple printed ones with personal touches
                    """)

        # Display budget summary
        for tier in ["Essentials Only", "Balanced", "Luxe"]:
            st.write(f"### {tier} Budget")
            st.write(f"Total: ${tier_totals[tier]:,}")
            st.write(f"Per Guest: ${tier_totals[tier] // st.session_state.guest_count:,}/guest")
            
            # Create pie chart
            df = pd.DataFrame.from_dict(
                {k: v for k, v in budget_tiers[tier].items() if k != "_goal_spend"},
                orient='index',
                columns=['Amount']
            )
            df = df[df['Amount'] > 0]
            
            chart = px.pie(
                df,
                values='Amount',
                names=df.index,
                title=f"{tier} Budget Breakdown",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(chart)
    
    with tab2:
        st.subheader("Detailed Cost Breakdown")
        selected_tier = st.selectbox(
            "Select Budget Tier",
            ["Essentials Only", "Balanced", "Luxe"],
            key="breakdown_tier_select"
        )
        
        df = pd.DataFrame.from_dict(
            {k: v for k, v in budget_tiers[selected_tier].items() if k != "_goal_spend"},
            orient='index',
            columns=['Amount']
        )
        df['Percentage'] = (df['Amount'] / tier_totals[selected_tier] * 100).round(1)
        df = df.sort_values('Amount', ascending=False)
        
        st.dataframe(
            df.style.format({
                'Amount': '${:,.0f}',
                'Percentage': '{:.1f}%'
            })
        )
    
    with tab3:
        st.subheader("Budget Visualizations")
        
        # Bar chart comparing tiers
        comparison_data = []
        for tier in ["Essentials Only", "Balanced", "Luxe"]:
            comparison_data.append({
                'Tier': tier,
                'Total Budget': tier_totals[tier],
                'Per Guest': tier_totals[tier] / st.session_state.guest_count
            })
        
        comp_df = pd.DataFrame(comparison_data)
        
        # Total budget comparison
        fig1 = px.bar(
            comp_df,
            x='Tier',
            y='Total Budget',
            title='Total Budget by Tier',
            color='Tier',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig1)
        
        # Per guest comparison
        fig2 = px.bar(
            comp_df,
            x='Tier',
            y='Per Guest',
            title='Cost Per Guest by Tier',
            color='Tier',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig2)
    
    with tab4:
        st.subheader("Export Options")
        col1, col2 = st.columns(2)
        
        selected_tier = st.selectbox(
            "Select Tier to Export",
            ["Essentials Only", "Balanced", "Luxe"],
            key="export_tier_select"
        )
        
        with col1:
            if st.button("📥 Download as Excel"):
                df = pd.DataFrame.from_dict(
                    {k: v for k, v in budget_tiers[selected_tier].items() if k != "_goal_spend"},
                    orient='index',
                    columns=['Amount']
                )
                df['Percentage'] = (df['Amount'] / tier_totals[selected_tier] * 100).round(1)
                
                # Create Excel file
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='Budget Breakdown')
                
                st.download_button(
                    label="Click to Download Excel",
                    data=output.getvalue(),
                    file_name=f"wedding_budget_{selected_tier.lower()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        
        with col2:
            if st.button("📄 Download as PDF"):
                pdf = WeddingBudgetPDF()
                
                # Add first page with summary
                pdf.add_page()
                pdf.chapter_title("Wedding Budget Summary")
                pdf.chapter_body(f"Date: {st.session_state.wedding_date.strftime('%B %d, %Y')}")
                pdf.chapter_body(f"Guest Count: {st.session_state.guest_count}")
                
                # Add pricing notes
                if seasonal_discount > 0:
                    reasons = []
                    if st.session_state.wedding_date.month in [11, 12, 1, 2, 3]:
                        reasons.append("off-season (November-March)")
                    if st.session_state.wedding_date.weekday() == 6:
                        reasons.append("Sunday")
                    elif st.session_state.wedding_date.weekday() < 5:
                        reasons.append("weekday")
                    pdf.chapter_body(f"Pricing Note: {seasonal_discount * 100:.0f}% off has been applied based on potential {' and '.join(reasons)} savings")
                
                # Add priorities
                if st.session_state.top_3:
                    pdf.chapter_body("\nTop Priorities:")
                    for priority in st.session_state.top_3:
                        pdf.chapter_body(f"• {priority}")
                
                # Add budget breakdown
                pdf.add_page()
                pdf.chapter_title(f"{selected_tier} Budget Breakdown")
                
                df = pd.DataFrame.from_dict(
                    {k: v for k, v in budget_tiers[selected_tier].items() if k != "_goal_spend"},
                    orient='index',
                    columns=['Amount']
                )
                df['Percentage'] = (df['Amount'] / tier_totals[selected_tier] * 100).round(1)
                df = df.sort_values('Amount', ascending=False)
                
                # Add table headers
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(100, 10, 'Category', 1)
                pdf.cell(45, 10, 'Amount', 1)
                pdf.cell(45, 10, 'Percentage', 1)
                pdf.ln()
                
                # Add table rows
                pdf.set_font('Arial', '', 12)
                for idx, row in df.iterrows():
                    pdf.cell(100, 10, str(idx), 1)
                    pdf.cell(45, 10, format_currency(row['Amount']), 1)
                    pdf.cell(45, 10, f"{row['Percentage']:.1f}%", 1)
                    pdf.ln()
                
                # Add totals
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(100, 10, 'Total', 1)
                pdf.cell(45, 10, format_currency(tier_totals[selected_tier]), 1)
                pdf.cell(45, 10, '100%', 1)
                pdf.ln()
                
                # Add per guest calculation
                pdf.cell(100, 10, 'Per Guest', 1)
                pdf.cell(45, 10, format_currency(tier_totals[selected_tier] / st.session_state.guest_count), 1)
                pdf.cell(45, 10, '', 1)
                
                # Save PDF
                pdf_output = BytesIO()
                pdf.output(pdf_output)
                
                st.download_button(
                    label="Click to Download PDF",
                    data=pdf_output.getvalue(),
                    file_name=f"wedding_budget_{selected_tier.lower()}.pdf",
                    mime="application/pdf"
                )

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
