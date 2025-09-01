# %%
"""
Visualize the number of government removal requests to Google per country (2019-2024)
- Connects to a MySQL database for removal requests data
- Uses Natural Earth shapefiles for world map
- Handles disputed territories and country name mismatches
- Plots a choropleth map with custom legend and annotations
"""
import mysql.connector
import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.types import Text
from sqlalchemy.dialects.mysql import LONGTEXT
from mysql.connector import Error
from getpass import getpass
import pandas as pd
import geopandas as gpd
import numpy as np
from shapely.ops import unary_union
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# %%
# Database connection setup
user = "*********"
password = getpass("MySQL password: ")
database = "*********"

engine = create_engine(f"mysql+pymysql://{user}:{password}@localhost/{database}")

try:
    with engine.connect() as conn:
        # Wrap query in text() function

        result = conn.execute(text("SELECT '✅ Connection successful' AS status"))
        print(result.scalar())  # Fetch the first column of first row
except Exception as e:
    print(f"❌ Connection failed: {e}")

# %%
# Load removal requests data from database into DataFrame
query = "SELECT * from Removal_Requests_1"

# Read all removal request records from the database into a DataFrame
df = pd.read_sql(query, engine)

# %%
# Load world country boundaries as GeoDataFrame
world = gpd.read_file(
    "https://naturalearth.s3.amazonaws.com/10m_cultural/ne_10m_admin_0_countries.zip"
)

# %%
# Ensure the table is a GeoDataFrame
world = gpd.GeoDataFrame(world, geometry="geometry")

# %%
# Load disputed areas shapefile (Natural Earth)
disputed = gpd.read_file(
    "https://naturalearth.s3.amazonaws.com/10m_cultural/ne_10m_admin_0_disputed_areas.zip"
) 

# Merge Cyprus and Northern Cyprus geometries for unified display
south_cy = world.loc[world['NAME']=='Cyprus', 'geometry']
north_cy = disputed.loc[disputed['NAME']=='N. Cyprus', 'geometry']
north_cy = north_cy.to_crs(world.crs)
full_cy = unary_union(list(south_cy) + list(north_cy))
raw_union = unary_union(list(south_cy) + list(north_cy))
closed = raw_union.buffer(0.05, join_style=1)
full_cy = closed.buffer(-0.05, join_style=1)
world.loc[world['NAME']=='Cyprus', 'geometry'] = full_cy

# Merge Somalia and Somaliland geometries for unified display
somalia = world.loc[world['NAME']=='Somalia', 'geometry']
somaliland = disputed.loc[disputed['NAME']=='Somaliland', 'geometry']
somaliland = somaliland.to_crs(world.crs)
full_somalia = unary_union(list(somalia) + list(somaliland))
world.loc[world['NAME']=='Somalia', 'geometry'] = full_somalia

# Remove Somaliland as a separate entity (already merged above)
world = world[world['NAME'] != 'Somaliland']

# %%
# Extract only the country name and geometry columns for merging
df2 = world[['NAME', 'geometry']]

# %%
# Map country names in your data to match Natural Earth names for merging
name_mapping = {
    'Bosnia & Herzegovina': 'Bosnia and Herz.',
    'Cape Verde': 'Cabo Verde',
    'Dominican Republic': 'Dominican Rep.',
    "Côte d’Ivoire": "Côte d'Ivoire",
    'Myanmar (Burma)': 'Myanmar',
    'South Sudan': 'S. Sudan',
    'United States': 'United States of America',
    'St. Vincent & Grenadines': 'St. Vin. and Gren.',
    'Trinidad & Tobago': 'Trinidad and Tobago',
    'Türkiye': 'Turkey'
}

# Standardize country names to match shapefile naming
df['country_mapped'] = df['country'].replace(name_mapping)

# %%
# Merge removal request data with world geometry by country
df_mrg = pd.merge(
    df,
    df2,
    left_on='country_mapped',
    right_on='NAME',
    how='right'
)

# Ensure the merged DataFrame is a GeoDataFrame
df_mrg = gpd.GeoDataFrame(df_mrg, geometry="geometry")

# %%
# Remove Antarctica from the merged GeoDataFrame
df_mrg = df_mrg[df_mrg['NAME'] != 'Antarctica']

# %%
# Handle Crimea: assign to Ukraine, remove from Russia
admin1 = gpd.read_file(
    "https://naturalearth.s3.amazonaws.com/10m_cultural/ne_10m_admin_1_states_provinces.zip"
)

mask = admin1['name_en'].str.contains('Crimea', case=False, na=False)
crimea_raw = admin1.loc[mask, 'geometry'].union_all()
crimea = (
    gpd.GeoSeries([crimea_raw], crs=admin1.crs)
       .to_crs(df_mrg.crs)  # match the CRS of your merged GeoDataFrame
       .iloc[0]             # extract the geometry back out
       .buffer(0)           # clean up any tiny topology errors
)

# Remove Crimea from Russia's geometry
df_mrg.loc[df_mrg['NAME']=='Russia', 'geometry'] = (
    df_mrg.loc[df_mrg['NAME']=='Russia', 'geometry']
          .apply(lambda g: g.difference(crimea).buffer(0))
)

# Add Crimea to Ukraine's geometry
df_mrg.loc[df_mrg['NAME']=='Ukraine', 'geometry'] = (
    df_mrg.loc[df_mrg['NAME']=='Ukraine', 'geometry']
          .apply(lambda g: g.union(crimea))
)

# Clean up Russia's geometry (remove small islands, etc.)
russia_parts = df_mrg.loc[df_mrg['NAME']=='Russia', 'geometry'].explode(index_parts=False)
# Keep only parts larger than a minimum area threshold (tweak as needed)
min_area = 0.10  # Minimum area threshold for Russia's parts
large_parts = [part for part in russia_parts if part.area > min_area]
clean_russia = unary_union(large_parts)
df_mrg.loc[df_mrg['NAME']=='Russia', 'geometry'] = clean_russia

# %%
# Define bins and category labels for removal requests
bins = [0, 20, 100, 1000, 10000, 100000, np.inf]
labels = ['1-20', '21-100', '101-1000', '1001-10000', '10001-100000', '100001+']

# Assign each country to a category based on the number of requests
df_mrg['requests_bin'] = pd.cut(
    df_mrg['total_requests'],
    bins=bins,
    labels=labels,
    right=True,
    include_lowest=True
)

# %%
def mark_zeros(row):
    if row['total_requests'] == 0:
        return 'zero'
    else:
        return row['requests_bin']
        
df_mrg['plot_category'] = df_mrg.apply(mark_zeros, axis=1)

# %%
df_mrg['plot_category'] = df_mrg['plot_category'].fillna('zero')
print(df_mrg['plot_category'].value_counts(dropna=False))

# %%
# Create a color map for your bins
cmap = plt.cm.get_cmap('YlGnBu', len(labels))
bin_to_color = {label: cmap(i) for i, label in enumerate(labels)}

# Add a special color for 'zero'
bin_to_color['zero'] = 'lightgrey'  # Or any color you like for zeros


# %%
# Assign a color to each country based on request bin
df_mrg['color'] = df_mrg['plot_category'].map(bin_to_color)

# Set Greenland's color to match Denmark for visualization
denmark_color_series = df_mrg.loc[df_mrg['country_mapped'] == 'Denmark', 'color']
denmark_color = denmark_color_series.iloc[0]  # Get the first (and only) value
greenland_index = df_mrg[df_mrg['NAME'] == 'Greenland'].index[0]
df_mrg.at[greenland_index, 'color'] = denmark_color

# %%
# Create the plot
fig, ax = plt.subplots(figsize=(15,10))

df_mrg.plot(
    color=df_mrg['color'],  # Use our pre-calculated colors
    linewidth=0.4,
    edgecolor='gray',
    ax=ax
)

ax.set_title('Government Removal Requests to Google (2019-2024)', fontsize=22)

legend_labels = labels[::-1] + ['0']
legend_colors = [cmap(i) for i in range(len(labels))][::-1] + ['lightgrey']

legend_handles = [
    Patch(facecolor=legend_colors[i], edgecolor='gray', label=legend_labels[i])
    for i in range(len(legend_labels))
]

ax.legend(
    handles=legend_handles,
    title='Number of\n Requests',
    title_fontproperties={'weight': 'bold', 'size' : 16},
    loc='lower left',
    bbox_to_anchor=(0.0, 0.37),
    frameon=False,
    fontsize=16
)

table_text =  r'$\bf{Top\ Countries\ by}$' + '\n'
table_text +=  r'$\bf{Removal\ Requests}$' + '\n'
table_text += '════════════════════════\n'
table_text += 'Russia      |  252,989\n'
table_text += 'South Korea |   39,514\n'
table_text += 'India       |   19,241\n'
table_text += 'Taiwan      |   13,712\n'
table_text += 'Turkey      |   12,391\n'
table_text += '──────────────────────\n'
table_text +=   r'$\bf{Total}$' + '       |  396,947'

fig.text(
    0.1, 0.32,  # Position (right-top corner)
    table_text,
    transform=ax.transAxes,
    fontfamily='DejaVu Sans Mono',  # Use monospace for proper alignment
    fontsize=14,
    verticalalignment='top',
    horizontalalignment='center',
    bbox=dict(boxstyle='round,pad=0.5', facecolor='moccasin', alpha=0.4)
)

table_text =  r'$\bf{Top\ Services}$' + '\n'
table_text +=  r'$\bf{Targeted}$' + '\n'
table_text += '═══════════════\n'
table_text += 'YouTube        \n'
table_text += 'Web Search     \n'
table_text += 'Google Images  \n'
table_text += 'Google Ads     \n'
table_text += 'Blogger        '        

fig.text(
    0.28, 0.25,  # Position (right-top corner)
    table_text,
    transform=ax.transAxes,
    fontfamily='DejaVu Sans Mono',  # Use monospace for proper alignment
    fontsize=14,
    verticalalignment='top',
    horizontalalignment='center',
    bbox=dict(boxstyle='round,pad=0.5', facecolor='slateblue', alpha=0.2)
)

table_text =  r'$\bf{Top\ Reasons}$' +'\n'
table_text += '════════════════════\n'
table_text += 'National Security   \n'
table_text += 'Copyright           \n'
table_text += 'Privacy and Security\n'
table_text += 'Regululated Goods   \n'
table_text += 'Defamation          \n'
table_text += 'Fraud               '

fig.text(
    0.45, 0.51,  # Position (right-top corner)
    table_text,
    transform=ax.transAxes,
    fontfamily='DejaVu Sans Mono',  # Use monospace for proper alignment
    fontsize=14,
    verticalalignment='top',
    horizontalalignment='center',
    bbox=dict(boxstyle='round,pad=0.5', facecolor='mediumseagreen', alpha=0.2)
)

table_text =  r'$\bf{Most\ Common\ Outcomes}$' + '\n'
table_text += '═════════════════════════════\n'
table_text += "Removed-country's laws (46%) \n"
table_text += 'No action taken (30%)        \n'
table_text += "Removed-Google's policy (8%) "

fig.text(
    0.77, 0.43,  # Position (right-top corner)
    table_text,
    transform=ax.transAxes,
    fontfamily='DejaVu Sans Mono',  # Use monospace for proper alignment
    fontsize=14,
    verticalalignment='top',
    horizontalalignment='center',
    bbox=dict(boxstyle='round,pad=0.5', facecolor='sandybrown', alpha=0.3)
)

table_text =  "→ Russia requires Google to remove links to websites that are banned \n"
table_text += "in the country. In March 2022, Russia blocked Google News.           \n"
table_text += "→ Only 1.7% of Russia's requests were removed due to Google's policy,\n"
table_text += "as opposed to South Korea's 37.7%, India's 11.7% and Taiwan's 48.2%. \n"
table_text += '→Google is totally banned in North Korea and nearly so in China.     \n'
table_text += '→Iran, Turkmenistan, Turkey and the occupied territories of Ukraine, \n'
table_text += 'have at times imposed restrictions on Google or its subsidiaries.    '

fig.text(
    0.65, 0.23,  # Position (right-top corner)
    table_text,
    transform=ax.transAxes,
    fontfamily='DejaVu Sans Mono',  # Use monospace for proper alignment
    fontsize=14,
    verticalalignment='top',
    horizontalalignment='center',
    bbox=dict(boxstyle='round,pad=0.5', facecolor='hotpink', alpha=0.1)
)

# Add source box
x, y = 0.92, 0.6  # position of text (figure coords)
text_str = "Source: Google"
bbox_props = dict(boxstyle="round,pad=0.5", edgecolor="black", facecolor="orange", alpha=0.4, linewidth=1)
fig.text(x, y, text_str, ha='center', va='center', fontsize=14, bbox=bbox_props)

ax.set_xlim(-180, 180) 
ax.set_ylim(-90, 90) 

ax.set_axis_off()
plt.tight_layout()

plt.savefig(
    'removal_requests',
    dpi=300,
    bbox_inches='tight',
    pad_inches=0.1,
    facecolor='white'
)

plt.show()
