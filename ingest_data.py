import os
import datetime
from azure.identity import DefaultAzureCredential
from azure.mgmt.costmanagement import CostManagementClient
from azure.mgmt.costmanagement.models import QueryDefinition, QueryDataset, QueryAggregation
from azure.cosmos import CosmosClient
from dotenv import load_dotenv

load_dotenv()
# --- CONFIGURATION AZURE & COSMOS ---
# (Utilise tes identifiants de l'étape 1 et 3)
SUBSCRIPTION_ID = os.getenv("SUBSCRIPTION_ID")
COSMOS_URL = os.getenv("COSMOS_URL")
COSMOS_KEY = os.getenv("COSMOS_KEY")

# 1. Authentification Azure (Cost Management)
os.environ["AZURE_TENANT_ID"] = os.getenv("AZURE_TENANT_ID")
os.environ["AZURE_CLIENT_ID"] = os.getenv("AZURE_CLIENT_ID")
os.environ["AZURE_CLIENT_SECRET"] = os.getenv("AZURE_CLIENT_SECRET")

cost_client = CostManagementClient(credential=DefaultAzureCredential())

# 2. Connexion Cosmos DB
cosmos_client = CosmosClient(COSMOS_URL, credential=COSMOS_KEY)
container = cosmos_client.get_database_client("CloudCostDB").get_container_client("DailyUsage")

# 3. Récupération des coûts
scope = f"/subscriptions/{SUBSCRIPTION_ID}"
query_def = QueryDefinition(
    type="Usage",
    timeframe="MonthToDate",
    dataset=QueryDataset(
        aggregation={"totalCost": QueryAggregation(name="PreTaxCost", function="Sum")},
        grouping=[{"type": "Dimension", "name": "ResourceGroupName"}]
    )
)

print("Récupération des données Azure...")
usage = cost_client.query.usage(scope, query_def)

# 4. Envoi vers Cosmos DB
for row in usage.rows:
    data = {
        "id": f"{row[1]}-{datetime.date.today()}", 
        "date": str(datetime.date.today()),
        "resourceGroup": row[1],
        "cost": row[0],
        "currency": row[2]
    }
    container.upsert_item(data)
    print(f"✅ Données synchronisées pour : {row[1]} ({row[0]} {row[2]})")

print("\nIngestion terminée ! Rafraîchis ton dashboard Streamlit.")