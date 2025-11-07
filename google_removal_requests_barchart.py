# %%
"""
Google Government Removal Requests - Outcome Analysis Bar Chart
==============================================================

This script creates a horizontal stacked bar chart showing the breakdown of outcomes 
for government removal requests to Google by the top 10 countries (by total requests).

The chart displays:
- Top 10 countries by total number of removal requests (2019-2024)
- Percentage breakdown of request outcomes for each country
- Six outcome categories: Removed-Legal, Removed-Policy, Content Not Found, 
  Not Enough Information, No Action Taken, Content Already Removed

Data source: MySQL database with processed Google government removal request data
Output: High-resolution PNG chart saved as 'Outcome of Request.png'
"""

# %%
import mysql.connector
import sqlalchemy
from sqlalchemy import create_engine, text
from getpass import getpass
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# %%
# Database connection setup
user = "********"
password = getpass("MySQL password: ")
database = "********"

engine = create_engine(f"mysql+pymysql://{user}:{password}@localhost/{database}")

# Test database connection
try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT '✅ Connection successful' AS status"))
        print(result.scalar())  # Fetch the first column of first row
except Exception as e:
    print(f"❌ Connection failed: {e}")

# %%
# Load processed removal request outcome data
query = "SELECT * from request_outcome_perc"

# %%
# Read data into DataFrame
df = pd.read_sql(query, engine)

# %%
# Define the percentage outcome columns for the chart
percentage_cols = [
    '% Removed-Legal',
    '% Removed-Policy',
    '% Content Not Found',
    '% Not Enough Information',
    '% No Action Taken',
    '% Content Already Removed'
]

# %%
# Get top 10 countries by total requests and prepare data for visualization
top10 = df.nlargest(10, 'Total Requests')

country_names = top10['Country']
data_for_chart = top10[percentage_cols]

# Define distinct colors for each outcome
colors = [
    "#1a9850",  # green (Removed-Legal)
    "#9258AD",  # bright purple (distinct for Removed-Policy)
    "#A9B8A9",  # light green
    "#fee08b",  # pale yellow
    "#3288bd",  # blue
    "#d53e4f",  # red
]

# %%
# Create the horizontal stacked bar chart
fig, ax = plt.subplots(figsize=(15, 10))

# Set background colors for the chart
fig.patch.set_facecolor("#F2F8FA")   # figure background
ax.set_facecolor("#F2F8FA")   

# Reverse order for horizontal bar chart (highest at top, lowest at bottom)
country_names_rev = country_names.iloc[::-1]
data_for_chart_rev = data_for_chart.iloc[::-1].reset_index(drop=True)

# Create stacked bars and capture bar objects for annotation
bars_by_segment = []
cumulative_heights = np.zeros(len(country_names_rev))

# Plot each outcome category as a segment of the stacked bar
for i, (col, color) in enumerate(zip(percentage_cols, colors)):
    bars = ax.barh(
        country_names_rev, 
        data_for_chart_rev.iloc[:, i], 
        left=cumulative_heights, 
        label=col,
        color=color   
    )
    bars_by_segment.append(bars)
    cumulative_heights += data_for_chart_rev.iloc[:, i]

# Add percentage labels to each bar segment
for segment_idx, bars in enumerate(bars_by_segment):
    for bar_idx, bar in enumerate(bars):
        width = bar.get_width()
        if width > 0:  # Only label segments with visible width
            ax.text(
                bar.get_x() + width/2,  # x position: center of bar segment
                bar.get_y() + bar.get_height()/2,  # y position: center of bar
                f'{width:.1f}',
                ha='center',
                va='center',
                color='black',
                fontsize=13
            )


# %%
# Customize chart appearance
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.spines['bottom'].set_visible(False)

# Configure axes and labels
ax.set_xticks([])  # Hide x-axis ticks since we have percentage labels on bars
ax.set_xlim(0, 100)
ax.set_xlabel('Percentage (%)', fontsize = 14)
ax.tick_params(axis='y', labelsize=15) 
ax.set_title('Outcome of Removal Requests: Top 10 Countries', fontsize = 22)

# Add legend for outcome categories
ax.legend(
    loc='lower right',
    bbox_to_anchor=(1.35, 0.3),
    fontsize=15,
    labelspacing=1.3
)

# Save chart as high-resolution PNG
plt.savefig(
    'Outcome of Request',
    dpi=300,
    bbox_inches='tight',
    pad_inches=0.1,
    facecolor='#F2F8FA',
    transparent=False  
)

# Display the chart
plt.show()

