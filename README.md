{\rtf1\ansi\ansicpg1252\cocoartf2709
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 # NFL Franchise Rankings App\
\
An interactive data visualization app that ranks NFL franchises and compares historical performance across eras.\
\
Built with **Python, Pandas, and Streamlit**, this app allows users to explore team rankings, cumulative performance snapshots, and rank trends over time \'97 all filtered dynamically by season.\
\
---\
\
## \uc0\u55357 \u56960  Features\
\
- **All-Time Franchise Rankings**\
  - View team ranks as of any selected year\
  - Rankings sourced from season-specific ranking data\
\
- **Snapshot Comparison**\
  - Compare cumulative franchise statistics *through a selected year*\
  - Ensures historical accuracy (no future-season leakage)\
\
- **Rank Over Time Visualization**\
  - Track how each franchise\'92s rank evolves across seasons\
\
- **Dynamic Filters**\
  - Year selector\
  - Team multi-select\
\
---\
\
## \uc0\u55357 \u56522  Data Structure\
\
The app uses an Excel file with the following sheets:\
\
### `Master Sheet`\
Contains per-season franchise statistics:\
- `Year`\
- `Team`\
- `Wins`\
- `Losses`\
- `Playoff Appearances`\
- `Division Titles`\
- `Conference Titles`\
- `Championships`\
- (Other cumulative stats as needed)\
\
### `Ranks`\
Contains season-specific rankings:\
- `Year`\
- `Team`\
- `Rank`\
\
> \uc0\u9888 \u65039  Rankings are **not inferred** from stats \'97 they are explicitly provided per season.\
\
---\
\
## \uc0\u55358 \u56800  Methodology\
\
- All statistics shown are **cumulative through the selected year**\
- Rankings reflect **only the selected season**\
- Snapshot comparisons and charts are always derived from the same filtered dataset to ensure consistency\
\
---\
\
## \uc0\u55357 \u57056  Tech Stack\
\
- Python 3.10+\
- Pandas\
- Streamlit\
- OpenPyXL (Excel ingestion)\
\
---\
\
## \uc0\u55357 \u56550  Installation (Local)\
\
```bash\
git clone https://github.com/your-username/nfl-rankings-app.git\
cd nfl-rankings-app\
python -m venv venv\
source venv/bin/activate  # macOS/Linux\
pip install -r requirements.txt\
streamlit run app.py\
}