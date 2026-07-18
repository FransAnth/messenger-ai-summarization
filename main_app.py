import json
from pathlib import Path

import pandas as pd
import streamlit as st

# Set up clean layout
st.set_page_config(page_title="Spectroplus Analytics Pipeline", layout="wide")

st.title("📊 Spectroplus CRM Analytics Pipeline")
st.markdown(
    "Filter conversations by operational category and select rows to drill down into specifics."
)

# 1. Load the enriched JSON data
json_path = Path("analysis_results.json")

if not json_path.exists():
    st.error(
        f"❌ '{json_path}' not found. Please run your analysis Python script first to generate the dataset."
    )
    st.stop()

with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# 2. Extract unique categories safely
categories = set()
for item in data:
    category = item.get("analysis", {}).get("category")
    if category:
        categories.add(category)
    else:
        categories.add("Uncategorized")

sorted_categories = sorted(list(categories))

st.markdown("---")

# 3. Create 2 columns for the same row layout (Short left column, Wide right column)
col_filter, col_table = st.columns([1, 3.5])

with col_filter:
    # Category Filter Dropdown on the left side
    selected_category = st.selectbox(
        "📂 Select CRM Category Filter:", options=sorted_categories, index=0
    )

# 4. Filter data based on selection
filtered_convs = [
    item
    for item in data
    if item.get("analysis", {}).get("category", "Uncategorized") == selected_category
]

# Initialize selection array globally so Section 6 can read it down below
selected_indices = []

with col_table:
    # 5. Display the Interactive Table on the right side
    if not filtered_convs:
        st.info(f"No conversations found matching the category: '{selected_category}'")
    else:
        st.markdown(
            f"### 🗂️ {selected_category} ({len(filtered_convs)} Conversations Found)"
        )

        # Build a clean flat dataframe list view for the table mapping
        table_rows = []
        for item in filtered_convs:
            table_rows.append(
                {
                    "Client Name": item.get("name", "Unknown"),
                    "Executive Summary": item.get("analysis", {}).get(
                        "summary", "No summary captured."
                    ),
                }
            )

        df = pd.DataFrame(table_rows)

        # Render table with built-in native row selection click listeners
        selection_event = st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            selection_mode="single-row",
            on_select="rerun",
        )

        # Catch active row index markers
        selected_indices = selection_event.get("selection", {}).get("rows", [])


# 6. Detail View Section (Triggered upon row selection click - Full Width Layout Below)
if selected_indices:
    selected_idx = selected_indices[0]
    selected_client = filtered_convs[selected_idx]

    st.markdown("---")

    # Shifted weights: Left side gets 40% width, Right side gets 60% width
    left_half, right_half = st.columns([3, 2])

    with left_half:
        st.markdown(f"## Analysis Dashboard: {selected_client.get('name', 'Unknown')}")

        analysis_data = selected_client.get("analysis", {})
        analytics = analysis_data.get("analytics", {})

        # Helper component logic for rendering ultra-clear semantic typography blocks
        # This completely avoids muddy, dark background textareas.

        # 1. Executive Summary - The Heavyweight Card
        st.markdown("### 📝 Executive Summary")
        st.markdown(
            f"""<div style="background-color: rgba(28, 131, 225, 0.1); 
                            border-left: 5px solid #1C83E1; 
                            padding: 18px; 
                            border-radius: 4px; 
                            font-size: 18px; 
                            line-height: 1.6; 
                            margin-bottom: 25px;">
                {analysis_data.get('summary', 'No summary generated.')}
            </div>""",
            unsafe_allow_html=True,
        )

        # 2. User Behavior Card
        st.markdown("### 👤 User Behavior Assessment")
        st.markdown(
            f"""<div style="border: 1px solid rgba(128, 128, 128, 0.2); 
                            padding: 15px; 
                            border-radius: 6px; 
                            font-size: 16px; 
                            line-height: 1.5; 
                            margin-bottom: 20px;">
                {analytics.get('user_behavior', 'N/A')}
            </div>""",
            unsafe_allow_html=True,
        )

        # 3. Company Performance Card
        st.markdown("### 🏢 Internal Performance Matrix")
        st.markdown(
            f"""<div style="border: 1px solid rgba(128, 128, 128, 0.2); 
                            padding: 15px; 
                            border-radius: 6px; 
                            font-size: 16px; 
                            line-height: 1.5; 
                            margin-bottom: 20px;">
                {analytics.get('company_performance', 'N/A')}
            </div>""",
            unsafe_allow_html=True,
        )

        # 4. Recommended Next Step (Green Callout for Action Items)
        st.markdown("### 🎯 Recommended Next Best Action")
        st.markdown(
            f"""<div style="background-color: rgba(46, 204, 113, 0.1); 
                            border-left: 5px solid #2ECC71; 
                            padding: 15px; 
                            border-radius: 4px; 
                            font-size: 16px; 
                            line-height: 1.5; 
                            margin-bottom: 20px;
                            font-weight: 500;">
                {analytics.get('next_best_action', 'N/A')}
            </div>""",
            unsafe_allow_html=True,
        )

    with right_half:
        st.markdown("### 💬 Conversation History")

        with st.container(height=650):
            messages = selected_client.get("messages", [])

            if not messages:
                st.info("No historical logs found for this chat file.")
            else:
                for msg in messages:
                    sender = msg.get("sender_name") or "Unknown"
                    text = msg.get("content") or ""
                    timestamp = msg.get("timestamp") or ""

                    st.markdown(f"### {sender}:")
                    st.write(text)
                    if timestamp:
                        st.caption(f"🕒 {timestamp}")
                    st.markdown("---")
