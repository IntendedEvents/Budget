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

    if wedding_date:
        discount = get_seasonal_discount(wedding_date)
        if discount > 0:
            discount_message = []
            if wedding_date.month in [11, 12, 1, 2, 3]:
                discount_message.append("off-season (November-March)")
            if wedding_date.weekday() == 6:
                discount_message.append("Sunday")
            elif wedding_date.weekday() < 5:
                discount_message.append("weekday")
            
            message = f"💰 Good news! You qualify for special pricing ({discount * 100:.0f}% off) for your "
            message += " and ".join(discount_message)
            message += " wedding!"
            st.success(message)

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
    
    # Calculate budget tiers
    scaling_factor = guest_count / 100
    seasonal_discount = get_seasonal_discount(wedding_date)
    budget_tiers = {tier: {} for tier in ["Essential", "Enhanced", "Elevated"]}
    tier_totals = {}
    category_priorities = {}

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
        if any(g in top_3 for g in goals_for_cat):
            category_priorities[cat] = "top"
        elif any(g in lowest for g in goals_for_cat):
            category_priorities[cat] = "bottom"
        else:
            category_priorities[cat] = "mid"

    # Priority weights for different tiers
    priority_weights = {
        "Essential": {
            "top": [0.2, 0.5, 0.3],
            "mid": [0.8, 0.2, 0.0],
            "bottom": [1.0, 0.0, 0.0]
        },
        "Enhanced": {
            "top": [0.0, 0.3, 0.7],
            "mid": [0.3, 0.4, 0.3],
            "bottom": [0.8, 0.2, 0.0]
        },
        "Elevated": {
            "top": [0.0, 0.1, 0.9],
            "mid": [0.2, 0.3, 0.5],
            "bottom": [0.5, 0.4, 0.1]
        }
    }

    # Calculate budgets for each tier
    for tier in ["Essential", "Enhanced", "Elevated"]:
        total = 0
        goal_spend = {goal: 0 for goal in goals}
        
        for cat in categories:
            if cat not in included_categories:
                budget_tiers[tier][cat] = 0
                continue

            # Custom logic for special categories
            if cat == "Floral Design":
                table_count = guest_count / 8
                row_count = int(np.ceil(guest_count / 6))
                focal_point_count = {"Essential": 1, "Enhanced": 2, "Elevated": 3}[tier]

                if floral_level == "Minimal":
                    centrepiece_cost = [50, 150, 300]
                    aisle_marker_cost = [50, 100, 150]
                    focal_point_unit = 300
                elif floral_level == "Medium":
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
                if venue_type == "At Home Wedding":
                    g, b, bst = 0, 2000, 4000
                elif venue_type == "Standard Venue":
                    g, b, bst = 5000, 8000, 12000
                else:  # Luxury Venue/Hotel
                    g, b, bst = 9000, 14000, 20000

            elif cat == "Stationery":
                g, b, bst = guest_count * 10, guest_count * 20, guest_count * 35

            else:
                g, b, bst = base_costs[cat]

            # Apply priority weights
            w = priority_weights[tier][category_priorities[cat]]
            value = (g * w[0] + b * w[1] + bst * w[2]) * scaling_factor

            # Apply minimum values
            if cat in category_minimums:
                value = max(value, category_minimums[cat])

            # Add tent cost if needed
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

            # Add beauty service costs
            if cat == "Hair & Makeup":
                value += (marrier_hair + wp_hair + marrier_makeup + wp_makeup) * 200

            # Add wedding party attire costs
            if cat == "Wedding Attire":
                value += dresses * 250 + suits * 200

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
        for tier in ["Essential", "Enhanced", "Elevated"]:
            st.write(f"### {tier} Budget")
            st.write(f"Total: ${tier_totals[tier]:,}")
            st.write(f"Per Guest: ${tier_totals[tier] // guest_count:,}/guest")
            
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
            ["Essential", "Enhanced", "Elevated"]
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
        for tier in ["Essential", "Enhanced", "Elevated"]:
            comparison_data.append({
                'Tier': tier,
                'Total Budget': tier_totals[tier],
                'Per Guest': tier_totals[tier] / guest_count
            })
        
        comp_df = pd.DataFrame(comparison_data)
        
        fig = go.Figure(data=[
            go.Bar(name='Total Budget', x=comp_df['Tier'], y=comp_df['Total Budget']),
            go.Bar(name='Per Guest', x=comp_df['Tier'], y=comp_df['Per Guest'])
        ])
        
        fig.update_layout(barmode='group', title='Budget Comparison by Tier')
        st.plotly_chart(fig)
    
    with tab4:
        st.subheader("Export Options")
        col1, col2 = st.columns(2)
        
        selected_tier = st.selectbox(
            "Select Tier to Export",
            ["Essential", "Enhanced", "Elevated"],
            key="export_tier"
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
                pdf.chapter_body(f"Date: {wedding_date.strftime('%B %d, %Y')}")
                pdf.chapter_body(f"Guest Count: {guest_count}")
                if seasonal_discount > 0:
                    pdf.chapter_body(f"Special Pricing Applied: {seasonal_discount * 100:.0f}% off")
                
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
                pdf.cell(45, 10, format_currency(tier_totals[selected_tier] / guest_count), 1)
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
