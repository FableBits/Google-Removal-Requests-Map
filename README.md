
# Google Content Removal Requests Choropleth Map (2019-2024)

This project visualizes the number of government content removal requests made to Google by country from 2019 to 2024. It produces a choropleth world map, coloring each country based on the total number of requests submitted to Google during this period.

## Features
- Connects to a MySQL database containing removal request data
- Handles country name mismatches and disputed territories for accurate mapping
- Merges and adjusts geometries for special cases (e.g., Cyprus, Somaliland, Crimea)
- Bins countries by request volume and colors them accordingly
- Annotates the map with top countries, services, reasons, and outcomes
- Saves the final map as a high-resolution image

## Requirements
- Python 3.7+
- MySQL database with a `Removal_Requests_1` table containing country and request data
- Internet connection (to download Natural Earth shapefiles)

## Installation
1. Clone this repository:
   ```powershell
   git clone <repository-url>
   cd "removal requests"
   ```
2. (Optional) Create and activate a virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```
3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

## Usage
1. Ensure your MySQL database is running and accessible. Update the database credentials in `google_removal_requests.py`.
2. Run the script:
   ```powershell
   python google_removal_requests.py
   ```
3. The script will prompt for your MySQL password and generate a file named `removal_requests.png` with the choropleth map.

## Data Sources
- Government removal request data: Your MySQL database
- Country boundaries and disputed areas: [Natural Earth](https://www.naturalearthdata.com/)

## Customization
- Adjust bin ranges or color schemes in the script as needed
- Update annotation text for different years or additional insights

## Example Output
The resulting map highlights countries by the number of requests, with annotations for top requesters, targeted Google services, common reasons, and outcomes.

## License
This project is licensed under the MIT License.
