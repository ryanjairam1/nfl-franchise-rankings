import streamlit as st
import pandas as pd
import plotly.express as px

# ========================
# Tab separation
# ========================
tab1, tab2 = st.tabs(["📊 Rankings", "🏆 Playoff Simulator"])

with tab1:
    # everything you already have


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
with tab2:
    # ========================
    # Reset Simulation
    # ========================
    if st.button("🔄 Reset Simulation"):
        for key in list(st.session_state.keys()):
            if (
                key.startswith("AFC_")
                or key.startswith("NFC_")
                or key.startswith("sb_")
            ):
                del st.session_state[key]

        st.rerun()

    st.header("🏆 Playoff Simulation")
    # ========================
    # Division Setup (No Conference)
    # ========================
    latest_year = master["Year"].max()

    teams_latest = (
        master[master["Year"] == latest_year]
        [["Team", "Division", "Total Team Points"]]
        .drop_duplicates(subset="Team")
    )
    
    teams_latest["Conference"] = teams_latest["Division"].str[:3]

    st.caption(
        "Simulate playoff outcomes by selecting division winners and wild card teams. "
        "Bonus points are applied temporarily and rankings update in real time."
    )

    # ========================
    # Base Scores (Most Recent Year ONLY — one row per team)
    # ========================
    latest_year = master["Year"].max()

    base_scores = (
        master[master["Year"] == latest_year]
        [["Team", "Total Team Points"]]
        .rename(columns={"Total Team Points": "Base Points"})
        .drop_duplicates(subset="Team")
    )

    # Division Winners
    st.subheader("Division Winners")

    division_winners = []

    divisions = sorted(teams_latest["Division"].dropna().unique())

    DIVS_PER_ROW = 4
    rows = [divisions[i:i + DIVS_PER_ROW] for i in range(0, len(divisions), DIVS_PER_ROW)]

    for row in rows:
        cols = st.columns(len(row))
        for col, div in zip(cols, row):
            teams_in_div = (
                teams_latest[teams_latest["Division"] == div]
                ["Team"]
                .sort_values()
            )

            selected = col.selectbox(
                div,
                options=["—"] + list(teams_in_div),
                key=f"division_{div}"
            )

            if selected != "—":
                division_winners.append(selected)


    if len(division_winners) < len(divisions):
        st.info("Select one division winner for each division to continue.")
        st.stop()


    ### Wild Card Teams
    st.subheader("Wild Card Teams")

    # Remaining teams after division winners
    remaining = teams_latest[
        ~teams_latest["Team"].isin(division_winners)
    ].copy()

    # Derive conference from division
    remaining["Conference"] = remaining["Division"].str[:3]

    wildcard_teams = []

    for conference in ["AFC", "NFC"]:
        st.markdown(f"### {conference} Wild Cards")

        conf_teams = (
            remaining[remaining["Conference"] == conference]
            .sort_values("Team")
        )

        team_list = conf_teams["Team"].tolist()

        # Layout: 3 per row
        TEAMS_PER_ROW = 3
        rows = [
            team_list[i:i + TEAMS_PER_ROW]
            for i in range(0, len(team_list), TEAMS_PER_ROW)
        ]

        selected_conf = []

        for row in rows:
            cols = st.columns(len(row))
            for col, team in zip(cols, row):
                checked = col.checkbox(
                    team,
                    key=f"{conference}_wc_{team}"
                )
                if checked:
                    selected_conf.append(team)

        # Validation per conference
        if len(selected_conf) != 3:
            st.warning(f"Select exactly 3 {conference} Wild Card teams.")
            st.stop()

        wildcard_teams.extend(selected_conf)


    selected_playoff_teams = division_winners + wildcard_teams

    # ========================
    # Initialize Simulation Table
    # ========================
    simulation = base_scores.copy()
    simulation["Bonus Points"] = 0

    # ========================
    # Qualification Bonuses
    # ========================
    simulation.loc[
        simulation["Team"].isin(division_winners),
        "Bonus Points"
    ] += 2

    simulation.loc[
        simulation["Team"].isin(wildcard_teams),
        "Bonus Points"
    ] += 1

    # ========================
    # Round Results
    # ========================
    st.subheader("Playoff Results")

    st.subheader("Wild Card Round Winners")

    # Build playoff team table (division winners + wild cards)
    playoff_teams_df = teams_latest[
        teams_latest["Team"].isin(selected_playoff_teams)
    ].copy()

    # Derive conference from division
    playoff_teams_df["Conference"] = playoff_teams_df["Division"].str[:3]


    ### WILD CARD ROUND WINNERS 
    wc_winners = []

    for conference in ["AFC", "NFC"]:
        st.markdown(f"### {conference} Wild Card Round Winners")

        conf_teams = (
            playoff_teams_df[playoff_teams_df["Conference"] == conference]
            .sort_values("Team")
        )

        team_list = conf_teams["Team"].tolist()

        TEAMS_PER_ROW = 4
        rows = [
            team_list[i:i + TEAMS_PER_ROW]
            for i in range(0, len(team_list), TEAMS_PER_ROW)
        ]

        selected_conf = []

        for row in rows:
            cols = st.columns(len(row))
            for col, team in zip(cols, row):
                checked = col.checkbox(
                    team,
                    key=f"{conference}_wc_win_{team}"
                )
                if checked:
                    selected_conf.append(team)

        # Validation
        if len(selected_conf) != 4:
            st.warning(f"Select exactly 4 {conference} Wild Card winners.")
            st.stop()

        wc_winners.extend(selected_conf)


    simulation.loc[
        simulation["Team"].isin(wc_winners),
        "Bonus Points"
    ] += 2

    # ========================
    ## DIVISION ROUND WINNERS 
    # ========================
    st.subheader("Divisional Round Winners - Conference Championship Matchups")

    # Build table of WC winners only
    wc_winners_df = teams_latest[
        teams_latest["Team"].isin(wc_winners)
    ].copy()

    # Derive conference from division
    wc_winners_df["Conference"] = wc_winners_df["Division"].str[:3]

    div_winners = []

    for conference in ["AFC", "NFC"]:
        st.markdown(f"### {conference} Divisional Round Winners")

        conf_teams = (
            wc_winners_df[wc_winners_df["Conference"] == conference]
            .sort_values("Team")
        )

        team_list = conf_teams["Team"].tolist()

        TEAMS_PER_ROW = 2
        rows = [
            team_list[i:i + TEAMS_PER_ROW]
            for i in range(0, len(team_list), TEAMS_PER_ROW)
        ]

        selected_conf = []

        for row in rows:
            cols = st.columns(len(row))
            for col, team in zip(cols, row):
                checked = col.checkbox(
                    team,
                    key=f"{conference}_div_win_{team}"
                )
                if checked:
                    selected_conf.append(team)

        # Validation
        if len(selected_conf) != 2:
            st.warning(f"Select exactly 2 {conference} Divisional Round winners.")
            st.stop()

        div_winners.extend(selected_conf)


    simulation.loc[
        simulation["Team"].isin(div_winners),
        "Bonus Points"
    ] += 4

    # ========================
    # CONFERENCE CHAMPIONS
    # ========================
    st.subheader("Conference Champions – Super Bowl Matchups")

    conf_champions = []

    # Build DF from divisional round winners only
    div_winners_df = teams_latest[
        teams_latest["Team"].isin(div_winners)
    ].copy()

    # Derive conference from division
    div_winners_df["Conference"] = div_winners_df["Division"].str[:3]

    for conference in ["AFC", "NFC"]:
        st.markdown(f"### {conference} Conference Champion")

        conf_teams = (
            div_winners_df[div_winners_df["Conference"] == conference]
            .sort_values("Team")
        )

        team_list = conf_teams["Team"].tolist()

        selected_conf = []

        cols = st.columns(len(team_list))
        for col, team in zip(cols, team_list):
            checked = col.checkbox(
                team,
                key=f"{conference}_conf_champ_{team}"
            )
            if checked:
                selected_conf.append(team)

        # Validation
        if len(selected_conf) != 1:
            st.warning(f"Select exactly 1 {conference} Conference Champion.")
            st.stop()

        # ✅ CRITICAL: extend inside loop
        conf_champions.extend(selected_conf)

    # Apply bonus
    simulation.loc[
        simulation["Team"].isin(conf_champions),
        "Bonus Points"
    ] += 11


    # ==============================
    # SUPER BOWL CHAMPION
    # ==============================
    st.subheader("Super Bowl Champion")

    if len(conf_champions) != 2:
        st.warning("You must select exactly 2 Conference Champions.")
        st.stop()

    sb_winner = st.radio(
        "Select the Super Bowl Champion",
        options=conf_champions,
        horizontal=True
    )

    # Apply Super Bowl bonus
    simulation.loc[
        simulation["Team"] == sb_winner,
        "Bonus Points"
    ] += 29


    # ========================
    # One Row Per Team (Most Recent Year)
    # ========================
    latest_year = master["Year"].max()

    base_scores = (
        master[master["Year"] == latest_year]
        [["Team", "Total Team Points"]]
        .rename(columns={"Total Team Points": "Base Points"})
    )

    # ========================
    # Merge Bonuses
    # ========================
    simulation = base_scores.merge(
        simulation[["Team", "Bonus Points"]],
        on="Team",
        how="left"
    )

    simulation["Bonus Points"] = simulation["Bonus Points"].fillna(0)

    # ========================
    # Original Rankings
    # ========================
    original = (
        simulation
        .sort_values("Base Points", ascending=False)
        .reset_index(drop=True)
    )

    #original["Original Rank"] = original.index + 1

    # ========================
    # Simulated Rankings
    # ========================
    simulation["Simulated Total Points"] = (
        simulation["Base Points"] + simulation["Bonus Points"]
    )

    simulated = (
        simulation
        .sort_values("Simulated Total Points", ascending=False)
        .reset_index(drop=True)
    )

    #simulated["New Rank"] = simulated.index + 1

    # ========================
    # Rank Change Table
    # ========================
    #rank_changes = (
    #    original[["Team", "Original Rank"]]
    #    .merge(
    #        simulated[["Team", "New Rank"]],
    #        on="Team"
    #    )
    #)

    #rank_changes["Rank Change"] = (
    #    rank_changes["Original Rank"] - rank_changes["New Rank"]
    #)

    # ========================
    # RANK CHANGE RESULTS
    # ========================
    st.subheader("📈 Simulated Franchise Ranking Changes")

    # 1. Base points (most recent year)
    latest_year = master["Year"].max()

    results = (
        master[master["Year"] == latest_year]
        [["Team", "Total Team Points"]]
        .rename(columns={"Total Team Points": "Base Points"})
    )

    # 2. Merge simulation bonuses
    results = results.merge(
        simulation[["Team", "Bonus Points"]],
        on="Team",
        how="left"
    )

    results["Bonus Points"] = results["Bonus Points"].fillna(0)

    # 3. Simulated totals
    results["Simulated Total Points"] = (
        results["Base Points"] + results["Bonus Points"]
    )

    # 4. Original ranks
    results = results.sort_values(
        "Base Points",
        ascending=False
    ).reset_index(drop=True)

    results["Original Rank"] = results.index + 1

    # 5. New ranks
    results = results.sort_values(
        "Simulated Total Points",
        ascending=False
    ).reset_index(drop=True)

    results["New Rank"] = results.index + 1

    # 6. Rank change
    results["Rank Change"] = (
        results["Original Rank"] - results["New Rank"]
    )

    # 7. Directional arrows
    def rank_arrow(x):
        if x > 0:
            return "⬆️"
        elif x < 0:
            return "⬇️"
        else:
            return "➖"

    results["Movement"] = results["Rank Change"].apply(rank_arrow)

    # 8. Display
    st.dataframe(
        results[[
            "Team",
            "Original Rank",
            "New Rank",
            "Rank Change",
            "Movement"
        ]],
        use_container_width=True,
        hide_index=True
    )

