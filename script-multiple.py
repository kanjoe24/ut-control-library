import requests
import pandas as pd

# 🔹 GitHub Credentials
REPO_OWNER = "kanjoe24"
REPO_NAME = "ut-control-library"
BASE_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents"


# 📌 Step 1: Get all top-level folders
response = requests.get(BASE_URL)
if response.status_code != 200:
    print("Failed to fetch repository contents:", response.text)
    exit()

# Extract all top-level directories (e.g., Element_Teone, Pioneer_x3_UHD, etc.)
folders = [item["name"] for item in response.json() if item["type"] == "dir"]
print("Top-level folders found:", folders)

# 📌 Step 2: Process Each Folder Separately
folder_graphs = {}

for folder in folders:
    print(f"🔍 Processing folder: {folder}")

    # Get all timestamped subfolders inside this folder
    folder_url = f"{BASE_URL}/{folder}"
    folder_response = requests.get(folder_url)

    if folder_response.status_code != 200:
        print(f"❌ Skipping {folder}: Cannot fetch contents.")
        continue  # Skip if we can't fetch folder contents

    subfolders = [f"{folder}/{item['name']}" for item in folder_response.json() if item["type"] == "dir"]
    print(f"📂 Found subfolders in {folder}: {subfolders}")

    release_dates = []
    memory_values = []

    for subfolder in subfolders:
        subfolder_url = f"{BASE_URL}/{subfolder}"
        subfolder_response = requests.get(subfolder_url)

        if subfolder_response.status_code != 200:
            print(f"⚠️ Skipping {subfolder}: Cannot fetch contents.")
            continue  # Skip if subfolder contents can't be retrieved

        # 🔹 Find the "vend-mem-release.csv" file inside this subfolder
        files = [f"{subfolder}/{item['name']}" for item in subfolder_response.json() if item["type"] == "file"]
        csv_file = next((f for f in files if f.endswith("vend-mem-release.csv")), None)

        if not csv_file:
            print(f"⚠️ No matching CSV file found in {subfolder}. Skipping...")
            continue  # Skip if no matching CSV found

        print(f"✅ Found CSV in {subfolder}: {csv_file}")

        # 🔹 Fetch CSV Data
        csv_url = f"{BASE_URL}/{csv_file}"
        csv_response = requests.get(csv_url)

        if csv_response.status_code != 200:
            print(f"❌ Error fetching CSV {csv_file}. Skipping...")
            continue

        csv_content = requests.get(csv_response.json()["download_url"]).text
        df = pd.read_csv(pd.io.common.StringIO(csv_content))
        df.columns = df.columns.str.strip()  # Normalize column names

        if "ReleaseDate" not in df.columns or "Avaialable Memory" not in df.columns:
            print(f"⚠️ CSV in {subfolder} does not have required columns. Skipping...")
            continue

        # 🔹 Extract Release Date & Memory Data
        latest_date = df["ReleaseDate"].dropna().iloc[-1]  # Latest release date
        avg_memory = df["Avaialable Memory"].mean()  # Average available memory

        release_dates.append(latest_date)
        memory_values.append(int(avg_memory))

    if not release_dates or not memory_values:
        print(f"⚠️ No valid data for {folder}. Skipping...")
        continue

    # 🔹 Step 3: Generate Mermaid Graph for this folder
    mermaid_graph = "```mermaid\n"
    mermaid_graph += "xychart-beta\n"
    mermaid_graph += f'    title "{folder} Memory Availability Trend"\n'
    mermaid_graph += f'    x-axis "Release Date" [{", ".join(release_dates)}]\n'
    mermaid_graph += f'    y-axis "Memory Available" {memory_values[-1]} --> {memory_values[0]}\n'
    mermaid_graph += f'    bar [{", ".join(map(str, memory_values))}]\n'
    mermaid_graph += f'    line [{", ".join(map(str, memory_values))}]\n'
    mermaid_graph += "```\n"

    folder_graphs[folder] = mermaid_graph

# 📌 Step 4: Regenerate README.md with Fixed Header
readme_content = "# L4-vendor-memory-test-results\n\n"

for folder, graph in folder_graphs.items():
    readme_content += f"## {folder}\n\n{graph}\n\n"

# Write updated README.md
readme_path = "README.md"
with open(readme_path, "w", encoding="utf-8") as f:
    f.write(readme_content)

print("✅ README.md fully regenerated. Commit & push to apply changes.")

