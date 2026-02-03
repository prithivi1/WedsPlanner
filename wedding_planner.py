import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- CONFIGURATION & SETUP ---
st.set_page_config(page_title="Wedding Planner", layout="wide", page_icon="💍")
DB_FILE = 'guest_list.csv'

# Defined Columns (The Master Schema)
COLUMNS = [
    "Name",
    "Category",  # Family, Friend, Office...
    "City",  # Coimbatore, Chennai...
    "Mobile",
    "Event",  # Reception, Wedding, Both
    "Headcount",  # Number of people
    "Rooms Required",  # Number of rooms needed (0, 1, 2...)
    "Invite Given",  # Boolean
    "Notes"
]


# --- DATA FUNCTIONS ---
def load_data():
    """Loads data, handles migration from old versions, and ensures type safety."""
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)

        # --- MIGRATION LOGIC (Preserve Old Data) ---
        # If user has old "Accommodation Needed" (True/False) but no "Rooms Required"
        if "Accommodation Needed" in df.columns and "Rooms Required" not in df.columns:
            df["Rooms Required"] = df["Accommodation Needed"].apply(lambda x: 1 if x == True else 0)

        # Ensure all standard columns exist
        for col in COLUMNS:
            if col not in df.columns:
                if col == "Headcount":
                    df[col] = 1
                elif col == "Rooms Required":
                    df[col] = 0
                elif col == "Invite Given":
                    df[col] = False
                else:
                    df[col] = ""
    else:
        df = pd.DataFrame(columns=COLUMNS)

    # --- TYPE SAFETY (Prevents Crashes) ---
    # Force text columns to Strings
    text_cols = ["Name", "Category", "City", "Mobile", "Event", "Notes"]
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str)

    # Force numeric columns
    if "Headcount" in df.columns:
        df["Headcount"] = df["Headcount"].fillna(1).astype(int)
    if "Rooms Required" in df.columns:
        df["Rooms Required"] = df["Rooms Required"].fillna(0).astype(int)

    # Force boolean columns
    if "Invite Given" in df.columns:
        df["Invite Given"] = df["Invite Given"].fillna(False).astype(bool)

    # Return only the columns we want, in the right order
    return df[COLUMNS]


def save_data(df):
    """Saves the DataFrame to the local CSV file."""
    df.to_csv(DB_FILE, index=False)


def convert_df(df):
    """Converts dataframe to CSV for download."""
    return df.to_csv(index=False).encode('utf-8')


# Load data into session state
if 'data' not in st.session_state:
    st.session_state.data = load_data()

df = st.session_state.data

# --- SIDEBAR: ADD GUEST ---
with st.sidebar:
    st.header("📝 Add Guest")
    with st.form("add_guest_form", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        with col_a:
            name = st.text_input("Name*")
            category = st.selectbox("Category", ["Family", "Friend", "Office", "Neighbors", "VIP", "Others"])
            city = st.text_input("City", placeholder="e.g. Coimbatore")
        with col_b:
            mobile = st.text_input("Mobile", placeholder="98765...")
            event = st.selectbox("Event", ["Reception", "Wedding (Mugurtham)", "Both"])
            headcount = st.number_input("Pax (People)", min_value=1, value=1)

        st.markdown("---")
        c1, c2 = st.columns(2)
        rooms = c1.number_input("Rooms Needed", min_value=0, value=0, help="Enter 0 if no stay needed")
        invite_given = c2.checkbox("Invite Given?")
        notes = st.text_area("Notes")

        submitted = st.form_submit_button("Add Guest", type="primary")

        if submitted and name:
            new_entry = pd.DataFrame([{
                "Name": name, "Category": category, "City": city, "Mobile": mobile,
                "Event": event, "Headcount": headcount, "Rooms Required": rooms,
                "Invite Given": invite_given, "Notes": notes
            }])
            st.session_state.data = pd.concat([st.session_state.data, new_entry], ignore_index=True)
            save_data(st.session_state.data)
            st.toast(f"✅ Added {name}!")
            st.rerun()

    st.divider()
    csv = convert_df(st.session_state.data)
    st.download_button("⬇️ Download CSV", csv, "wedding_guests.csv", "text/csv")

# --- MAIN APP UI ---
st.title("Vignesh Wedding Planner 💍")

# Tabs
tab1, tab2, tab3 = st.tabs(["📊 Dashboard & Logistics", "🍽️ Catering & Rooms", "📋 Master Guest List"])

# --- TAB 1: OVERVIEW DASHBOARD ---
with tab1:
    if df.empty:
        st.info("Start adding guests from the sidebar!")
    else:
        # ROW 1: TOP METRICS
        total_pax = df["Headcount"].sum()
        total_families = len(df)
        invites_sent = len(df[df["Invite Given"] == True])
        pending = total_families - invites_sent

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Guests (Pax)", total_pax)
        m2.metric("Families", total_families)
        m3.metric("Invites Sent", invites_sent)
        m4.metric("Pending", pending, delta_color="inverse")

        st.divider()

        # ROW 2: CHARTS
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🌍 Guests by City")
            city_counts = df.groupby("City")["Headcount"].sum().reset_index().sort_values("Headcount", ascending=False)
            fig_city = px.bar(city_counts, x="City", y="Headcount", text="Headcount", color="Headcount")
            st.plotly_chart(fig_city, use_container_width=True)

        with c2:
            st.subheader("👥 Category Split")
            cat_counts = df.groupby("Category")["Headcount"].sum().reset_index()
            fig_cat = px.pie(cat_counts, values="Headcount", names="Category", hole=0.4)
            st.plotly_chart(fig_cat, use_container_width=True)

# --- TAB 2: CATERING & LOGISTICS ---
with tab2:
    if df.empty:
        st.write("No data.")
    else:
        # 1. CATERING ESTIMATES
        st.subheader("🍽️ Catering Estimates")
        # Logic: "Both" counts for Reception AND Wedding
        reception_total = df[df["Event"].isin(["Reception", "Both"])]["Headcount"].sum()
        wedding_total = df[df["Event"].isin(["Wedding (Mugurtham)", "Both"])]["Headcount"].sum()

        kpi1, kpi2 = st.columns(2)
        kpi1.info(f"**Reception Plates:** {reception_total}")
        kpi2.success(f"**Wedding Breakfast:** {wedding_total}")

        st.divider()

        # 2. ACCOMMODATION
        st.subheader("🏨 Accommodation Logistics")
        total_rooms = df["Rooms Required"].sum()

        col_metrics, col_table = st.columns([1, 2])

        with col_metrics:
            st.metric("Total Rooms to Book", total_rooms)
            st.caption("Based on 'Rooms Required' column")

        with col_table:
            st.write("**Who needs rooms?**")
            room_df = df[df["Rooms Required"] > 0][["Name", "City", "Rooms Required", "Mobile"]]
            if not room_df.empty:
                st.dataframe(
                    room_df,
                    hide_index=True,
                    use_container_width=True,
                    column_config={"Rooms Required": st.column_config.NumberColumn("Rooms", format="%d 🛏️")}
                )
            else:
                st.write("No rooms needed yet.")

# --- TAB 3: MASTER EDITOR ---
with tab3:
    st.subheader("✏️ Master Guest List")
    st.write("Edit any detail below. Changes save automatically.")

    column_cfg = {
        "Invite Given": st.column_config.CheckboxColumn("Sent?", width="small"),
        "Rooms Required": st.column_config.NumberColumn("Rooms 🛏️", min_value=0, max_value=10, width="small"),
        "Category": st.column_config.SelectboxColumn("Category",
                                                     options=["Family", "Friend", "Office", "VIP", "Others"],
                                                     width="medium"),
        "Event": st.column_config.SelectboxColumn("Event", options=["Reception", "Wedding (Mugurtham)", "Both"],
                                                  width="medium"),
        "Headcount": st.column_config.NumberColumn("Pax", min_value=1, max_value=20, format="%d"),
        "Mobile": st.column_config.TextColumn("Mobile", validate="^[0-9+]*$"),
        "City": st.column_config.TextColumn("City"),
        "Notes": st.column_config.TextColumn("Notes", width="large"),
    }

    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        column_config=column_cfg,
        use_container_width=True,
        hide_index=True,
        key="editor_ultimate"
    )

    if not df.equals(edited_df):
        st.session_state.data = edited_df
        save_data(edited_df)
        st.rerun()