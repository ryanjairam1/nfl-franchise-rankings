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
# Tab separation
# ========================
tab1, tab2, tab3 = st.tabs(["📊 Rankings", "🏆 Playoff Simulator", "Algorithm & Scoring"])

with tab1:
    
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
    st.caption(
        "There are 3 tools on this page. An All Time Franchise Ranking table with a team's Legacy Score, a direct Franchise comparison tool, and a line graph to show how rankings have changed over time."
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

    col_rank, col_snapshot = st.columns([1, 2])

    # ========================
    # All-Time Rankings (LEFT)
    # ========================
    with col_rank:
        st.subheader("All-Time Franchise Rankings")
        st.caption(
            "Franchise rank and cumulative points through the selected year."
        )

        latest_rank = (
            filtered_ranks
                .sort_values("Year")
                .groupby("Team", as_index=False)
                .last()[["Team", "Rank"]]
        )

        master_year = master[master["Year"] == selected_year]
        team_points = master_year[["Team", "Total Team Points"]]

        all_time = latest_rank.merge(team_points, on="Team", how="left")
        all_time = all_time.sort_values("Rank")
        all_time["Total Team Points"] = (
            all_time["Total Team Points"]
            .fillna(0)
            .astype(int)
        )
        all_time = all_time.rename(
            columns={"Total Team Points": "Team Legacy Score"}
        )

        st.dataframe(
            all_time,
            use_container_width=True,
            hide_index=True
        )

    # ========================
    # Snapshot Comparison (RIGHT)
    # ========================
    with col_snapshot:
        st.subheader("Snapshot Comparison")
        st.caption(
            "Cumulative franchise achievements compared side-by-side for the selected teams."
        )

        comparison = master[master["Team"].isin(team_options)].copy()
        if selected_teams:
            comparison = comparison[comparison["Team"].isin(selected_teams)]

        if not comparison.empty:
            comparison_summary = (
                comparison.groupby("Team")
                .agg({
                    "Division": "first",
                    "SB Win": "sum",
                    "SB App": "sum",
                    "CC app": "sum",
                    "Division Title?": "sum",
                    "Playoff Appearance?": "sum",
                    "MVP": "sum"
                })
                .reset_index()
            )

            year_ranks = ranks[ranks["Year"] == selected_year][["Team", "Rank"]]
            comparison_summary = comparison_summary.merge(year_ranks, on="Team", how="left")

            numeric_cols = ["SB Win", "SB App", "CC app", "Division Title?", "Playoff Appearance?","MVP", "Rank"]
            for col in numeric_cols:
                if col in comparison_summary.columns:
                    comparison_summary[col] = comparison_summary[col].fillna(0).astype(int)

            comparison_summary = comparison_summary.rename(columns={
                "Rank": f"Rank in {selected_year}",
                "SB Win": "Super Bowl Championships",
                "SB App": "Super Bowl Appearances",
                "CC app": "Conference Championship Appearances",
                "Division Title?": "Division Titles",
                "Playoff Appearance?": "Playoff Appearances",
                "MVP": "MVPs"
            })

            comparison_summary = comparison_summary.sort_values(by=f"Rank in {selected_year}")

            ordered_stats = [
                "Division",
                f"Rank in {selected_year}",
                "Super Bowl Championships",
                "Super Bowl Appearances",
                "Conference Championship Appearances",
                "Division Titles",
                "Playoff Appearances",
                "MVPs"
            ]

            comparison_transposed = comparison_summary.set_index("Team")[ordered_stats].T

            st.dataframe(
                comparison_transposed,
                use_container_width=True
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

    st.markdown("---")
    col_division = st.container()

    # ========================
    # Division Rankings
    # ========================
    with col_division:
        st.subheader("Division Rankings")
        st.caption(
            "Total franchise points accumulated by division through the most recent year."
        )

        division_points = (
            master
                .groupby(["Division", "Team"], as_index=False)
                .agg(Team_Points=("Total Team Points", "max"))
        )

        division_summary = (
            division_points
                .groupby("Division", as_index=False)
                .agg(Division_Points=("Team_Points", "sum"))
                .sort_values("Division_Points", ascending=False)
                .reset_index(drop=True)
        )

        division_summary["Division Rank"] = (
            division_summary["Division_Points"]
                .rank(method="dense", ascending=False)
                .astype(int)
        )

        division_summary = division_summary[
            ["Division Rank", "Division", "Division_Points"]
        ]

        st.dataframe(
            division_summary,
            use_container_width=True,
            hide_index=True
        )

    division_summary["Division_Points"] = (
        division_summary["Division_Points"].astype(int)
    )

# ========================
# TAB 2 — Playoff Simulator
# ========================
with tab2:

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

    base_scores = (
        master[master["Year"] == latest_year]
        [["Team", "Total Team Points"]]
        .rename(columns={"Total Team Points": "Base Points"})
        .drop_duplicates(subset="Team")
    )

    # ========================
    # Division Winners
    # ========================
    st.subheader("Division Winners")

    division_winners = []
    divisions = sorted(teams_latest["Division"].dropna().unique())

    DIVS_PER_ROW = 4
    rows = [divisions[i:i + DIVS_PER_ROW] for i in range(0, len(divisions), DIVS_PER_ROW)]

    for row in rows:
        cols = st.columns(len(row))
        for col, div in zip(cols, row):
            teams_in_div = (
                teams_latest[teams_latest["Division"] == div]["Team"].sort_values()
            )
            selected = col.selectbox(
                div,
                options=["—"] + list(teams_in_div),
                key=f"division_{div}"
            )
            if selected != "—":
                division_winners.append(selected)

    # ---- Guard: all divisions must be selected ----
    if len(division_winners) < len(divisions):
        st.info("Select one division winner for each division to continue.")

    else:
        # ========================
        # Wild Card Teams
        # ========================
        st.subheader("Wild Card Teams")

        remaining = teams_latest[~teams_latest["Team"].isin(division_winners)].copy()
        remaining["Conference"] = remaining["Division"].str[:3]

        wildcard_teams = []
        wc_complete = True

        for conference in ["AFC", "NFC"]:
            st.markdown(f"### {conference} Wild Cards")

            conf_teams = remaining[remaining["Conference"] == conference].sort_values("Team")
            team_list = conf_teams["Team"].tolist()

            TEAMS_PER_ROW = 3
            wc_rows = [team_list[i:i + TEAMS_PER_ROW] for i in range(0, len(team_list), TEAMS_PER_ROW)]

            selected_conf = []
            for wc_row in wc_rows:
                cols = st.columns(len(wc_row))
                for col, team in zip(cols, wc_row):
                    checked = col.checkbox(team, key=f"{conference}_wc_{team}")
                    if checked:
                        selected_conf.append(team)

            if len(selected_conf) != 3:
                st.warning(f"Select exactly 3 {conference} Wild Card teams.")
                wc_complete = False
            else:
                wildcard_teams.extend(selected_conf)

        # ---- Guard: all wild cards must be selected ----
        if not wc_complete:
            pass  # warnings already shown above

        else:
            selected_playoff_teams = division_winners + wildcard_teams

            simulation = base_scores.copy()
            simulation["Bonus Points"] = 0

            simulation.loc[simulation["Team"].isin(division_winners), "Bonus Points"] += 2
            simulation.loc[simulation["Team"].isin(wildcard_teams), "Bonus Points"] += 1

            # ========================
            # Wild Card Round Winners
            # ========================
            st.subheader("Playoff Results")
            st.subheader("Wild Card Round Winners")

            playoff_teams_df = teams_latest[teams_latest["Team"].isin(selected_playoff_teams)].copy()
            playoff_teams_df["Conference"] = playoff_teams_df["Division"].str[:3]

            wc_winners = []
            wc_round_complete = True

            for conference in ["AFC", "NFC"]:
                st.markdown(f"### {conference} Wild Card Round Winners")

                conf_teams = playoff_teams_df[playoff_teams_df["Conference"] == conference].sort_values("Team")
                team_list = conf_teams["Team"].tolist()

                TEAMS_PER_ROW = 4
                wc_win_rows = [team_list[i:i + TEAMS_PER_ROW] for i in range(0, len(team_list), TEAMS_PER_ROW)]

                selected_conf = []
                for wc_win_row in wc_win_rows:
                    cols = st.columns(len(wc_win_row))
                    for col, team in zip(cols, wc_win_row):
                        checked = col.checkbox(team, key=f"{conference}_wc_win_{team}")
                        if checked:
                            selected_conf.append(team)

                if len(selected_conf) != 4:
                    st.warning(f"Select exactly 4 {conference} Wild Card winners.")
                    wc_round_complete = False
                else:
                    wc_winners.extend(selected_conf)

            if not wc_round_complete:
                pass  # warnings already shown above

            else:
                simulation.loc[simulation["Team"].isin(wc_winners), "Bonus Points"] += 2

                # ========================
                # Divisional Round Winners
                # ========================
                st.subheader("Divisional Round Winners - Conference Championship Matchups")

                wc_winners_df = teams_latest[teams_latest["Team"].isin(wc_winners)].copy()
                wc_winners_df["Conference"] = wc_winners_df["Division"].str[:3]

                div_winners = []
                div_round_complete = True

                for conference in ["AFC", "NFC"]:
                    st.markdown(f"### {conference} Divisional Round Winners")

                    conf_teams = wc_winners_df[wc_winners_df["Conference"] == conference].sort_values("Team")
                    team_list = conf_teams["Team"].tolist()

                    TEAMS_PER_ROW = 2
                    div_rows = [team_list[i:i + TEAMS_PER_ROW] for i in range(0, len(team_list), TEAMS_PER_ROW)]

                    selected_conf = []
                    for div_row in div_rows:
                        cols = st.columns(len(div_row))
                        for col, team in zip(cols, div_row):
                            checked = col.checkbox(team, key=f"{conference}_div_win_{team}")
                            if checked:
                                selected_conf.append(team)

                    if len(selected_conf) != 2:
                        st.warning(f"Select exactly 2 {conference} Divisional Round winners.")
                        div_round_complete = False
                    else:
                        div_winners.extend(selected_conf)

                if not div_round_complete:
                    pass  # warnings already shown above

                else:
                    simulation.loc[simulation["Team"].isin(div_winners), "Bonus Points"] += 4

                    # ========================
                    # Conference Champions
                    # ========================
                    st.subheader("Conference Champions – Super Bowl Matchups")

                    conf_champions = []
                    div_winners_df = teams_latest[teams_latest["Team"].isin(div_winners)].copy()
                    div_winners_df["Conference"] = div_winners_df["Division"].str[:3]

                    conf_complete = True

                    for conference in ["AFC", "NFC"]:
                        st.markdown(f"### {conference} Conference Champion")

                        conf_teams = div_winners_df[div_winners_df["Conference"] == conference].sort_values("Team")
                        team_list = conf_teams["Team"].tolist()

                        selected_conf = []
                        cols = st.columns(len(team_list))
                        for col, team in zip(cols, team_list):
                            checked = col.checkbox(team, key=f"{conference}_conf_champ_{team}")
                            if checked:
                                selected_conf.append(team)

                        if len(selected_conf) != 1:
                            st.warning(f"Select exactly 1 {conference} Conference Champion.")
                            conf_complete = False
                        else:
                            conf_champions.extend(selected_conf)

                    if not conf_complete:
                        pass  # warnings already shown above

                    else:
                        simulation.loc[simulation["Team"].isin(conf_champions), "Bonus Points"] += 11

                        # ========================
                        # Super Bowl Champion
                        # ========================
                        st.subheader("Super Bowl Champion")

                        sb_winner = st.radio(
                            "Select the Super Bowl Champion",
                            options=conf_champions,
                            horizontal=True
                        )

                        simulation.loc[simulation["Team"] == sb_winner, "Bonus Points"] += 29

                        # ========================
                        # Final Results Table
                        # ========================
                        results = (
                            master[master["Year"] == latest_year]
                            [["Team", "Total Team Points"]]
                            .rename(columns={"Total Team Points": "Base Points"})
                        )

                        results = results.merge(
                            simulation[["Team", "Bonus Points"]],
                            on="Team",
                            how="left"
                        )

                        results["Bonus Points"] = results["Bonus Points"].fillna(0)
                        results["Simulated Total Points"] = results["Base Points"] + results["Bonus Points"]

                        results = results.sort_values("Base Points", ascending=False).reset_index(drop=True)
                        results["Original Rank"] = results.index + 1

                        results = results.sort_values("Simulated Total Points", ascending=False).reset_index(drop=True)
                        results["New Rank"] = results.index + 1

                        results["Rank Change"] = results["Original Rank"] - results["New Rank"]

                        def rank_arrow(x):
                            if x > 0:
                                return "⬆️"
                            elif x < 0:
                                return "⬇️"
                            else:
                                return "➖"

                        results["Movement"] = results["Rank Change"].apply(rank_arrow)

                        st.subheader("📈 Simulated Franchise Ranking Changes")
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

# ========================
# TAB 3 — Algorithm & Scoring
# ========================
with tab3:
    st.title("Algorithm & Scoring Methodology")

    st.markdown("""
    ## How the Ranking Algorithm Works

    The ranking system assigns weighted point values to teams based on postseason success and regular season achievements.

    Each season, teams accumulate points depending on their final result.
    These yearly totals are then summed to produce:

    - Team Legacy Scores
    - All-time franchise rankings
    - Division rankings
    """)

    st.markdown("""
    Every season is worth 100 points, based on the Playoff Format effective for the 2020-2021 season with 14 playoff teams.
    A team can earn points in the following ways: 
    """)

    st.divider()

    st.subheader("Point Allocation System")

    scoring_table = {
        "Achievement": [
            "Super Bowl Champion",
            "Super Bowl Appearance",
            "Conference Championship Appearance",
            "Divisional Round Appearance",
            "Playoff Appearance",
            "Division Champion",
            "MVP",
            "OPOY",
            "DPOY"
        ],
        "Points Awarded": [
            23,
            9,
            4,
            2,
            1,
            1,
            3,
            1,
            1,
        ],
    }

    scoring_df = pd.DataFrame(scoring_table)

    st.dataframe(
        scoring_df,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    st.subheader("Team Legacy Score")

    st.markdown("""
    The **Team Legacy Score** represents the cumulative total of all points
    earned by a franchise through the selected year. As a team progresses through the playoffs,
    they collect more points through each round.

    For example, a division winner who wins the Super Bowl and has the MVP
    earns the following legacy score for a season: 

    1 Point (Winning Division) + 1 Point (Playoff Appearance) + 2 Points (Divisional Round App)
    + 4 Points (Conference Championship App) + 9 (Super Bowl Appearance) + 23 (Super Bowl Win) + 3 (MVP)
    = 43 points for the Team Legacy Score of the available 100 points to earn for the season

    Another example, a wild card team to lose in the divisional round will the following score for a season:
    1 Point (Playoff Appearance) + 2 Points (Divisional Round App) = 3 points. 
    Considering there are 8 total teams in the divisional round, this makes sense.

    
    This value dynamically updates based on the year filter and reflects
    historical performance over time.
    """)

    st.subheader("Change Over Time")
    
    st.markdown("""
    This Ranking Algorithm is based on the princple that all 
    Super Bowls are created equal. The Jet's lone Super Bowl 3 Win is worth the same as the Saints's Lone Super Bowl 44 Win
    in the grand scheme of how we look at these franchise's accomplishments. 

    The NFL has changed the playoff format over time. In the 1970 Playoffs, there were just 8 playoff teams.
    Applying the principle above, if the value of winning the Super Bowl remains the same over time but there are
    less playoff teams, there are less total points available in a season in order to preserve the value of postseason accomplishments.
    """)