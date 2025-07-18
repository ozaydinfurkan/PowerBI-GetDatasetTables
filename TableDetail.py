import os, sys
import requests, msal
import clr
import time
from pathlib import Path
from dotenv import load_dotenv
from System.Reflection import Assembly
from System import DateTime
import pyodbc
import ssl

# ─── ENVIRONMENT & .ENV LOAD ─────────────────────
current_dir = Path(__file__).resolve().parent
env_path = current_dir / ".env"
if not env_path.exists():
    env_path = current_dir.parent / ".env"

print(f"Loading .env from: {env_path}")
load_dotenv(dotenv_path=env_path)


load_dotenv(dotenv_path, override=True)
# Env Variables
CLIENT_ID     = os.getenv("CLIENT_ID")
TENANT_ID     = os.getenv("TENANT_ID")
WORKSPACE_ID  = os.getenv("MANUEL_WORKSPACE_ID")
WORKSPACE_NAME= os.getenv("MANUEL_WORKSPACE_NAME")

server        = os.getenv("DB_SERVER")
database      = os.getenv("DB_NAME")
username      = os.getenv("DB_USERNAME")
password      = os.getenv("DB_PASSWORD")

# Validation
if not all([CLIENT_ID, TENANT_ID, WORKSPACE_ID, WORKSPACE_NAME]):
    sys.exit("❌ Missing critical .env variables.")

# ─── ADOMD.NET DLL LOAD ─────────────────────────
adomd_root = Path(r"C:\Program Files\Microsoft.NET\ADOMD.NET")
for ver in ("160","150","140","130"):
    native_dir = adomd_root / ver
    if native_dir.is_dir():
        os.add_dll_directory(str(native_dir))
        # print(f"✅ ADOMD.NET DLL loaded from: {native_dir}")
        managed_dll = native_dir / "Microsoft.AnalysisServices.AdomdClient.dll"
        break
else:
    sys.exit("❌ ADOMD.NET directory not found.")

if not managed_dll.is_file():
    sys.exit(f"❌ ADOMD.NET assembly missing: {managed_dll}")

Assembly.LoadFrom(str(managed_dll))
clr.AddReference("Microsoft.AnalysisServices.AdomdClient")
from Microsoft.AnalysisServices.AdomdClient import AdomdConnection

# ─── AUTHENTICATION ────────────────────────────

authority = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE     = ["https://analysis.windows.net/powerbi/api/.default"]

if CLIENT_SECRET:
    app = msal.ConfidentialClientApplication(
        CLIENT_ID, authority=authority, client_credential=CLIENT_SECRET
    )
    token_resp = app.acquire_token_for_client(scopes=SCOPE)
else:
    app = msal.PublicClientApplication(CLIENT_ID, authority=authority)
    flow = app.initiate_device_flow(scopes=SCOPE)
    if "user_code" not in flow:
        sys.exit(f"❌ Device flow error: {flow}")
    print(flow["message"])
    token_resp = app.acquire_token_by_device_flow(flow)

if "access_token" not in token_resp:
    sys.exit(f"❌ Token acquisition failed: {token_resp.get('error_description', token_resp)}")

token = token_resp["access_token"]
HEADERS = {"Authorization": f"Bearer {token}"}
print("✅ Token alındı")


# ─── WORKSPACE INFO ────────────────────────
resp = requests.get(f"https://api.powerbi.com/v1.0/myorg/groups/{WORKSPACE_ID}", headers=HEADERS)
if resp.status_code != 200:
    sys.exit(f"❌ Workspace bilgisi alınamadı: {resp.text}")
workspace_name = resp.json().get("name")
print(f"✅ Workspace: {workspace_name}")

# ─── DATASET LIST ────────────────────────
ds_resp = requests.get(f"https://api.powerbi.com/v1.0/myorg/groups/{WORKSPACE_ID}/datasets", headers=HEADERS)
if ds_resp.status_code != 200:
    sys.exit(f"❌ Datasets alınamadı: {ds_resp.text}")
datasets = ds_resp.json().get("value", [])
print(f"✅ {len(datasets)} dataset bulundu")

# ─── SQL SERVER CONNECTION ─────────────────────
ssl_context = ssl.create_default_context()
conn_str_db = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
conn_db = pyodbc.connect(conn_str_db)
cursor = conn_db.cursor()

# ─── XMLA QUERY AND INSERT FOR EACH DATASETS─────

cursor.execute("SELECT DISTINCT dataset_id FROM [your_database_name].[dbo].[SemanticModelDetail]")
existing_ids = [row[0] for row in cursor.fetchall()]

print(f"✅ Mevcut {len(existing_ids)} dataset_id found")


exclude_datasets = ["Usage Metrics Report", "Report Usage Metrics Model", "Dashboard Usage Metrics Model","DataflowsStagingLakehouse","DataflowsStagingWarehouse"]
only_dataset = ""  # if you want to take any dataset you can entered the dataset name

for ds in datasets:
    ds_name = ds.get("name")
    dataset_id = ds.get("id")
    dataset_name = ds.get("name")

    if only_dataset and ds_name != only_dataset:
        continue    
    if ds_name in exclude_datasets:
        print(f"⛔️ Skipped: {ds_name}")
        continue 
    print(f"\n📦 Dataset: {ds_name}")

    time.sleep(1)

    conn_str = (
        f"Provider=MSOLAP;"
        f"Data Source=powerbi://api.powerbi.com/v1.0/myorg/{WORKSPACE_NAME};"
        f"Initial Catalog={ds_name};"
        f"Integrated Security=ClaimsToken;"
        f"Connect Timeout=60;"
        f"Password={token};"
    )

    try:
        conn = AdomdConnection(conn_str)
        conn.Open()
    except Exception as e:
        print(f"❌ {ds_name} XMLA connection error :")
        continue

    # Load the XMLA query from file            
    with open('Query_TableDetail.xmla', 'r', encoding='utf-8') as file:
        xmla_query = file.read()
    
    cmd = conn.CreateCommand()
    cmd.CommandText = xmla_query

    try:
        rdr = cmd.ExecuteReader()
    except Exception as e:
        print(f"❌ {ds_name} query error: ")
        conn.Close()
        continue

    column_names = [rdr.GetName(i) for i in range(rdr.FieldCount)]
    
    insert_query = f"""
        INSERT INTO [your_database_name].[dbo].[SemanticModelDetail]
        ([workspace_id],[workspace_name], [dataset_id],[dataset_name], {",".join(column_names)})
        VALUES ({','.join('?' for _ in range(len(column_names) + 4))})
    """
   
    while rdr.Read():
        values = [WORKSPACE_ID,WORKSPACE_NAME, dataset_id,dataset_name]
        for i in range(rdr.FieldCount):
            val = rdr.GetValue(i)
            if isinstance(val, DateTime):
                val = val.ToString("yyyy-MM-dd HH:mm:ss")
            elif val is None:
                val = None
            values.append(val)

        try:
            cursor.execute(insert_query, values)
        except Exception as e:
            print(f"❌ Insert error: {e} → {values}")

    conn_db.commit()
    print(f"✅ {ds_name} inserted")

    rdr.Close()
    conn.Close()

    dedup_query = """
WITH CTE_Duplicates AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (
            PARTITION BY workspace_id, dataset_id, TableName
            ORDER BY ETLDATE DESC
        ) AS rn
    FROM [your_database_name].[dbo].[SemanticModelDetail]
)
DELETE FROM CTE_Duplicates
WHERE rn > 1
"""

try:
    cursor.execute(dedup_query)
    conn_db.commit()
    print("✅ dublicated records deleted")
except Exception as e:
    print(f"❌ error during deleted {e}")

# ─── CLEANING ──────────────────────────────────
conn_db.close()
print("🎉 completed")
