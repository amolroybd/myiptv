from pathlib import Path
import pandas as pd

# ==========================================================
# Paths
# ==========================================================
ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = ROOT / "data" / "channels.xlsx"
OUTPUT_FILE = ROOT / "output" / "playlist.m3u"

# Leave blank if you don't have an EPG yet
EPG_URL = ""

# ==========================================================
# Read Excel
# ==========================================================
df = pd.read_excel(INPUT_FILE).fillna("")

# Remove spaces from column names
df.columns = df.columns.str.strip()

# ==========================================================
# Status
# Blank = Active
# ==========================================================
if "Status" in df.columns:
    status = (
        df["Status"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    df = df[
        (status == "") |
        (status == "active")
    ]

# ==========================================================
# Use Backup URL if Stream URL is empty
# ==========================================================
if "Backup URL" in df.columns:

    df["Stream URL"] = df.apply(
        lambda r: r["Backup URL"]
        if str(r.get("Stream URL", "")).strip() == ""
        else r["Stream URL"],
        axis=1
    )

# ==========================================================
# Remove empty rows
# ==========================================================
df = df[
    (df["Channel Name"].astype(str).str.strip() != "") &
    (df["Stream URL"].astype(str).str.strip() != "")
]

# ==========================================================
# Remove duplicate URLs
# ==========================================================
df = df.drop_duplicates(subset=["Stream URL"])

# ==========================================================
# Group
# Empty group becomes "Other"
# ==========================================================
if "Group" not in df.columns:
    df["Group"] = "Other"

df["Group"] = (
    df["Group"]
    .fillna("")
    .astype(str)
    .str.strip()
)

df.loc[df["Group"] == "", "Group"] = "Other"

# ==========================================================
# Sort
# ==========================================================
df = df.sort_values(
    by=["Group", "Channel Name"]
)

# ==========================================================
# Output folder
# ==========================================================
OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

# ==========================================================
# Header
# ==========================================================
if EPG_URL:
    lines = [f'#EXTM3U x-tvg-url="{EPG_URL}"']
else:
    lines = ["#EXTM3U"]

# ==========================================================
# Build playlist
# ==========================================================
for _, row in df.iterrows():

    name = str(row.get("Channel Name", "")).strip()
    url = str(row.get("Stream URL", "")).strip()

    attrs = []

    # tvg-id
    epg = str(row.get("EPG ID", "")).strip()
    if epg:
        attrs.append(f'tvg-id="{epg}"')

    # tvg-name
    attrs.append(f'tvg-name="{name}"')

    # Logo
    logo = str(row.get("Logo", "")).strip()
    if logo:
        attrs.append(f'tvg-logo="{logo}"')

    # Group
    group = str(row.get("Group", "")).strip().title()
    attrs.append(f'group-title="{group}"')

    # Country
    country = str(row.get("Country", "")).strip()
    if country:
        attrs.append(f'tvg-country="{country}"')

    # Language
    language = str(row.get("Language", "")).strip()
    if language:
        attrs.append(f'tvg-language="{language}"')

    # Resolution / Quality
    resolution = str(row.get("Resolution", "")).strip()

    if not resolution:
        resolution = str(row.get("Quality", "")).strip()

    if resolution:
        attrs.append(f'tvg-resolution="{resolution}"')

    extinf = "#EXTINF:-1"

    if attrs:
        extinf += " " + " ".join(attrs)

    extinf += f",{name}"

    lines.append(extinf)
    lines.append(url)

# ==========================================================
# Save
# ==========================================================
OUTPUT_FILE.write_text(
    "\n".join(lines),
    encoding="utf-8"
)

# ==========================================================
# Statistics
# ==========================================================
print("=" * 60)
print("Playlist created successfully")
print(f"Channels : {len(df)}")
print(f"Saved to : {OUTPUT_FILE}")
print("=" * 60)
