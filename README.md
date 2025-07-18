# PowerBI-GetDatasetTables

# 📊 Power BI Dataset Metadata Extractor (Python + XMLA + SQL)

This project enables automatic extraction of **tables**, **columns**, and **data source information** from datasets hosted in a Power BI Premium or PPU workspace using the **XMLA Endpoint**.

It connects to the dataset using **DMV (Dynamic Management Views)** queries via XMLA, retrieves metadata, and optionally writes it to a **SQL Server** database.

---

## 🚀 Features

✅ Connects to Power BI XMLA Endpoint  
✅ Lists all tables in the dataset  
✅ Retrieves column names and data types  
✅ Extracts data source information (SQL, Excel, Dataflow, etc.)  
✅ Optionally writes metadata to SQL Server  

---

## ⚙️ Requirements

- Python 3.8+
- Power BI Premium or Premium Per User (PPU) Workspace
- Azure AD App Registration
- Python libraries:

```bash
pip install -r requirements.txt

<img width="795" height="415" alt="image" src="https://github.com/user-attachments/assets/f0538922-ea01-47e8-80ab-4b091bd6105f" />

