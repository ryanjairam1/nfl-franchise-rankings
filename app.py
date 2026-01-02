import streamlit as st
import pandas as pd
import plotly.express as px

# ========================
# App Config
# ========================
st.set_page_config(
    page_title="NFL Franchise Rankings",
    layout="wide"
)

# ========================
# Load Data
# ========================
@st.cache_data
def load_data():
    xls = pd.ExcelFile("data/nfl_data.xlsm")

    master = pd.read_excel(xls, "Master Sheet")
    ranks_raw = pd.read_excel(xls, "Rank by Year")
    winrank_raw = pd.read_excel(xls, "Winning % Rank Over Time")
    winpct_raw = pd.read_excel(xls, "Winning % Over Time")

    def melt_year_team(df, value_name):
        year_col = df.columns[0]
        return (
            df.melt(
                id_vars=[year_col],
                var_name="Team",
                value_name=value_name
            )
            .rename(columns={year_col: "Year"})
            .dropna(subset=[value_name])
        )

    ranks = melt_year_team(ranks_raw, "Rank")
    winrank = melt_year_team(winrank_raw, "Winning % Rank")
    winpct = melt_year_team(winpct_raw, "Winning %")

    return master, ranks, winrank, winpct


master, ranks, winrank, winpct = load_data()

# ========================
# Header
# ========================
st.title("🏈 NFL Franchise Rankings Dashboard")
st.caption(
    "This is a Super Bowl Era Franchise Ranking system. It is based off a custom franchise performance algorithm using historical results through from 1966 (Super Bowl I), to the most recent Super Bowl."
)


# ========================
# Filters
# ========================
st.subheader("Filters")
st.caption(
    "Use the controls below to filter teams, divisions, and the maximum season included in the rankings."
)

col1, col2, col3 = st.columns(3)

with col1:
    divisions = sorted(master["Division"].dropna().unique())
    selected_divisions = st.multiselect(
        "Division",
        options=divisions
    )

with col2:
    if selected_divisions:
        team_options = (
            master[master["Division"].isin(selected_divisions)]
            ["Team"]
            .sort_values()
            .unique()
        )
    else:
        team_options = master["Team"].sort_values().unique()

    selected_teams = st.multiselect(
        "Team",
        options=team_options
    )

with col3:
    selected_year = st.slider(
        "Through Year",
        min_value=1966,
        max_value=int(ranks["Year"].max()),
        value=int(ranks["Year"].max())
    )

# ========================
# Filtered Rank Data
# ========================
filtered_ranks = ranks[
    (ranks["Year"] <= selected_year) &
    (ranks["Team"].isin(selected_teams if selected_teams else team_options))
]

if selected_teams:
    filtered_ranks = filtered_ranks[
        filtered_ranks["Team"].isin(selected_teams)
    ]

# ========================
# All-Time Rankings Table
# ========================
st.subheader("All-Time Franchise Rankings")
st.caption(
    "Each franchise's overall rank as of the selected year."
)

all_time = (
    filtered_ranks
        .sort_values("Year")
        .groupby("Team", as_index=False)
        .last()
        .sort_values("Rank")
)

st.dataframe(
    all_time[["Team", "Rank"]],
    use_container_width=True,
    hide_index=True
)

# ========================
# Rank Over Time Chart
# ========================
st.subheader("Rank Over Time")
st.caption(
    "Tracks how each franchise's ranking has evolved over time. Lower values indicate better performance."
)

fig_rank = px.line(
    filtered_ranks,
    x="Year",
    y="Rank",
    color="Team",
    markers=True
)

fig_rank.update_yaxes(
    autorange="reversed",
    title="Rank (1 = Best)"
)

st.plotly_chart(fig_rank, use_container_width=True)

# ========================
# Snapshot Comparison Table
# ========================
st.subheader("Snapshot Comparison")
st.caption(
    "Cumulative franchise achievements compared side-by-side for the selected teams, "
    "with rankings shown as of the selected year."
)

# 1. Filter the master stats data
comparison = master[master["Team"].isin(team_options)].copy()
if selected_teams:
    comparison = comparison[comparison["Team"].isin(selected_teams)]

if not comparison.empty:
    # 2. Group by Team and sum the stats
    # We use .reset_index() so 'Team' remains a column for merging
    comparison_summary = (
        comparison.groupby("Team")
        .agg({
            "Division": "first",
            "SB Win": "sum",
            "SB App": "sum",
            "CC app": "sum",
            "Division Title?": "sum",
            "MVP": "sum"
        })
        .reset_index()
    )

    # 3. Pull the Rank for the specific selected year
    year_ranks = ranks[ranks["Year"] == selected_year][["Team", "Rank"]]
    
    # Merge the Rank into our summary table
    comparison_summary = comparison_summary.merge(year_ranks, on="Team", how="left")

    # 4. Formatting: Convert numeric stats to whole numbers (integers)
    # This removes the .0 decimal points from the display
    numeric_cols = ["SB Win", "SB App", "CC app", "Division Title?", "MVP", "Rank"]
    for col in numeric_cols:
        if col in comparison_summary.columns:
            comparison_summary[col] = comparison_summary[col].fillna(0).astype(int)

    # 5. Rename columns for the final display
    rename_dict = {
        "Rank": f"Rank in {selected_year}",
        "Division": "Division",
        "SB Win": "Super Bowl Championships",
        "SB App": "Conference Championships",
        "CC app": "Conference Championship Appearances",
        "Division Title?": "Division Titles",
        "MVP": "MVPs"
    }
    comparison_summary = comparison_summary.rename(columns=rename_dict)

    # 6. Sort by Rank (1 is the best, so we sort ascending)
    comparison_summary = comparison_summary.sort_values(by=f"Rank in {selected_year}")

    # 7. Define the vertical order of rows (Rank at the very top)
    ordered_stats = [
        "Division", 
        f"Rank in {selected_year}",
        "Super Bowl Championships", 
        "Conference Championships", 
        "Conference Championship Appearances", 
        "Division Titles", 
        "MVPs"
    ]

    # 8. Set Team as the index and Transpose (.T)
    # The teams will now appear as columns, ordered by their rank
    comparison_transposed = comparison_summary.set_index("Team")[ordered_stats].T

    # 9. Display the table
    st.dataframe(
        comparison_transposed,
        use_container_width=True
    )
else:
    st.info("No data available for the current selection.")