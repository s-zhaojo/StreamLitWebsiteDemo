import streamlit as st
from streamlit_folium import st_folium
import folium
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="RECLAIM – Global Reservoir Tool", layout="wide")
st.title("RECLAIM – Global Reservoir Tool 🌍")

# Initialize session state
for key, default in [("lat_input", 20.0), ("lon_input", 0.0)]:
    if key not in st.session_state:
        st.session_state[key] = default

with st.sidebar:
    st.header("Reservoir Information")

    start_year = st.slider("Start Year (I1, year) *", 1900, 2025, 2000)
    end_year = st.slider("End Year (I2, year) *", 1900, 2025, 2020)
    build_year = st.slider("Build Year (I3, year) *", 1900, 2025, 2010)

    reservoir_name = st.text_input("Reservoir / Major River Basin (I4) *")

    st.number_input("Dam Latitude (I5, °) *", format="%.6f", key="lat_input")
    st.number_input("Dam Longitude (I6, °) *", format="%.6f", key="lon_input")

    I7 = st.number_input("Original Built Capacity (I7, million m³) *")
    I8 = st.number_input("Dam Height (I8, m) *")
    I9 = st.number_input("Dam Crest Length / Structural Parameter (I9) *")

    I10 = st.file_uploader("Reservoir Geometry (I10, GEOJSON/ZIP) *", type=["geojson", "zip"])
    I12 = st.file_uploader("Catchment Geometry (I12, GEOJSON/ZIP) *", type=["geojson", "zip"])

    st.subheader("Time Series Inputs (Optional)")
    I13 = st.file_uploader("Inflow (I13, CSV)", type=["csv"])
    I14 = st.file_uploader("Outflow (I14, CSV)", type=["csv"])
    I15 = st.file_uploader("Surface Area (I15, CSV)", type=["csv"])
    I16 = st.file_uploader("Evaporation (I16, CSV)", type=["csv"])
    I17 = st.file_uploader("NSSC1 (I17, CSV)", type=["csv"])
    I18 = st.file_uploader("NSSC2 (I18, CSV)", type=["csv"])

    st.subheader("Meteorology (Optional)")
    I19 = st.file_uploader("Precipitation (I19, CSV)", type=["csv"])
    I20 = st.file_uploader("Temperature Min/Max (I20, CSV)", type=["csv"])
    I21 = st.file_uploader("Wind Speed (I21, CSV)", type=["csv"])

    submitted = st.button("Submit Reservoir Data")

# Function to create map
def create_map(lat, lon, tooltip=None):
    m = folium.Map(location=[lat, lon], zoom_start=2, control_scale=True)
    folium.Marker([lat, lon], tooltip=tooltip or "Selected Location").add_to(m)
    return m

# Show map and capture click events
st.subheader("World Map 🌍 (Click to set location)")
map_data = st_folium(
    create_map(st.session_state.lat_input, st.session_state.lon_input, tooltip=reservoir_name),
    width=900, height=600
)

# Update session state if user clicks on map
if map_data and map_data.get("last_clicked"):
    st.session_state.lat_input = map_data["last_clicked"]["lat"]
    st.session_state.lon_input = map_data["last_clicked"]["lng"]

lat = st.session_state.lat_input
lon = st.session_state.lon_input

# Simple sedimentation computation
def compute_sedimentation(I7, I8, I13, I17, I18, years):
    rate = 0.25
    if I13 is not None:
        inflow = pd.read_csv(I13)
        rate += inflow.iloc[:, 0].mean() * 1e-5
    if I17 is not None:
        nssc1 = pd.read_csv(I17)
        rate += nssc1.iloc[:, 0].mean() * 1e-4
    if I18 is not None:
        nssc2 = pd.read_csv(I18)
        rate += nssc2.iloc[:, 0].mean() * 1e-4

    rate *= max(0.5, 1 - I8 / 300)
    cumulative_loss = rate * years
    remaining_capacity = I7 * (1 - cumulative_loss / 100)
    return rate, cumulative_loss, remaining_capacity

# Handle form submission
if submitted:
    required_fields = {
        "I1": start_year,
        "I2": end_year,
        "I3": build_year,
        "I4": reservoir_name,
        "I5": lat,
        "I6": lon,
        "I7": I7,
        "I8": I8,
        "I9": I9,
        "I10": bool(I10),
        "I12": bool(I12),
    }
    missing = [k for k, v in required_fields.items() if not v]
    if missing:
        st.error(f"Missing required inputs: {missing}")
    else:
        st.success("Reservoir data submitted successfully!")

        years_count = end_year - start_year
        rate, cumulative_loss, remaining_capacity = compute_sedimentation(
            I7, I8, I13, I17, I18, years_count
        )

        st.subheader("Reservoir Sedimentation Results")
        c1, c2, c3 = st.columns(3)
        c1.metric("Sedimentation Rate", f"{rate:.2f} % / year")
        c2.metric("Total Capacity Loss", f"{cumulative_loss:.2f} %")
        c3.metric("Remaining Capacity", f"{remaining_capacity:.2f} million m³")

        # Plot cumulative loss over time
        years_axis = list(range(start_year, end_year + 1))
        loss_curve = [rate * (y - start_year) for y in years_axis]

        fig, ax = plt.subplots()
        ax.plot(years_axis, loss_curve)
        ax.set_xlabel("Year")
        ax.set_ylabel("Cumulative Capacity Loss (%)")
        ax.set_title("Reservoir Sedimentation Over Time")
        st.pyplot(fig)

        # Map showing the selected location
        st.subheader("Sedimentation Estimate Map")
        st_folium(create_map(lat, lon, tooltip=f"{reservoir_name}\nSed Rate: {rate:.2f}%/yr"), width=900, height=600)

        # Input summary
        st.subheader("Input Summary (I1–I21)")
        st.json({
            "I1": start_year,
            "I2": end_year,
            "I3": build_year,
            "I4": reservoir_name,
            "I5": lat,
            "I6": lon,
            "I7": I7,
            "I8": I8,
            "I9": I9,
            "I10_uploaded": bool(I10),
            "I12_uploaded": bool(I12),
            "I13_uploaded": bool(I13),
            "I14_uploaded": bool(I14),
            "I15_uploaded": bool(I15),
            "I16_uploaded": bool(I16),
            "I17_uploaded": bool(I17),
            "I18_uploaded": bool(I18),
            "I19_uploaded": bool(I19),
            "I20_uploaded": bool(I20),
            "I21_uploaded": bool(I21),
        })
