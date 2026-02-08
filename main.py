import streamlit as st
import pandas as pd
import plotly.express as px
from azure.cosmos import CosmosClient
import os
import datetime
from dotenv import load_dotenv
from azure.cosmos import CosmosClient


load_dotenv()

# --- CONFIGURATION PAGE ---
st.set_page_config(page_title="Azure Cost Monitor", layout="wide")
st.title("📊 Dashboard de Gestion des Coûts Cloud")

# --- CONNEXION DATA ---
COSMOS_URL = os.getenv("COSMOS_URL")
COSMOS_KEY = os.getenv("COSMOS_KEY")
client = CosmosClient(COSMOS_URL, COSMOS_KEY)
container = client.get_database_client("CloudCostDB").get_container_client("DailyUsage")

# Lecture des données
items = list(container.read_all_items())
df = pd.DataFrame(items)

if not df.empty:
    # --- CALCULS ---
    total_cost = df['cost'].sum()
    # Prédiction simple (exemple : +20% d'ici la fin du mois)
    forecast_cost = total_cost * 1.2 

    # --- AFFICHAGE DES KPI ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Coût Actuel", f"{total_cost:.2f} {df['currency'][0]}")
    col2.metric("Prédiction Fin de Mois", f"{forecast_cost:.2f} {df['currency'][0]}", delta="+20%")
    
    # Alerte Intelligente
    budget_max = 10.0 # Ton seuil
    if total_cost > budget_max:
        st.error(f"⚠️ ALERTE : Le budget de {budget_max} $ est dépassé !")
    else:
        st.success("✅ Budget sous contrôle")
    
    # Sidebar pour le filtrage
    st.sidebar.header("Filtres")
    selected_rg = st.sidebar.multiselect(
        "Choisir les Groupes de Ressources",
        options=df["resourceGroup"].unique(),
        default=df["resourceGroup"].unique()
    )

    # Filtrer le DataFrame
    df_filtered = df[df["resourceGroup"].isin(selected_rg)]

    # --- GRAPHIQUES ---
    st.subheader("Répartition des coûts par Groupe de Ressources")
    fig = px.pie(df_filtered, values='cost', names='resourceGroup', hole=0.4)
    st.plotly_chart(fig, use_container_width=True)
    st.sidebar.markdown("---")
    st.sidebar.subheader("💡 Optimisation")
    
    # Trouver le groupe le plus cher
    top_group = df_filtered.sort_values(by="cost", ascending=False).iloc[0]
    st.sidebar.warning(f"Le groupe **{top_group['resourceGroup']}** consomme le plus. Envisagez de réduire ses instances pour économiser.")

    # --- TABLEAU DE DÉTAILS ---
    st.subheader("Détails des instances")
    st.dataframe(df_filtered[['date', 'resourceGroup', 'cost', 'currency']])
else:
    st.info("Aucune donnée trouvée. Lancez votre script d'ingestion !")