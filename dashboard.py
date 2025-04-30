import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import MultipleLocator
import json
import requests

# Load data
@st.cache_data
def load_data():
    combined = pd.read_csv('dataset/combined_dataset.csv', parse_dates=['order_purchase_timestamp'])
    payments = pd.read_csv('dataset/payment_clean.csv')
    return combined, payments

combined, payments = load_data()

@st.cache_data
def load_brazil_geojson():
    url = 'https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson'
    response = requests.get(url)
    return response.json()

brazil_geojson = load_brazil_geojson()


# Mapping kode state ke nama lengkap state
state_mapping = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas", "BA": "Bahia",
    "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás", "MA": "Maranhão",
    "MT": "Mato Grosso", "MS": "Mato Grosso do Sul", "MG": "Minas Gerais", "PA": "Pará", "PB": "Paraíba",
    "PR": "Paraná", "PE": "Pernambuco", "PI": "Piauí", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
    "RS": "Rio Grande do Sul", "RO": "Rondônia", "RR": "Roraima", "SC": "Santa Catarina", "SP": "São Paulo",
    "SE": "Sergipe", "TO": "Tocantins"
}

combined['year'] = combined['order_purchase_timestamp'].dt.year
combined['month'] = combined['order_purchase_timestamp'].dt.month
combined['customer_state_full'] = combined['customer_state'].map(state_mapping)
combined['product_category_name_english'] = combined['product_category_name_english'].str.replace('_', ' ')

def get_quarter(month):
    if month in [1, 2, 3]: return "Q1"
    elif month in [4, 5, 6]: return "Q2"
    elif month in [7, 8, 9]: return "Q3"
    else: return "Q4"

combined['quarter'] = combined['month'].apply(get_quarter)

# Sidebar filters
st.sidebar.header("Filter")
year_filter = st.sidebar.multiselect("Tahun", [2017, 2018], default=None)
quarter_filter = st.sidebar.multiselect("Kuartal", ["Q1", "Q2", "Q3", "Q4"], default=None)
all_states = sorted(combined['customer_state_full'].dropna().unique())
selected_states = st.sidebar.multiselect("Provinsi", all_states, default=None)
product_categories = sorted(combined['product_category_name_english'].dropna().unique())
selected_categories = st.sidebar.multiselect("Kategori Produk", product_categories, default=None)

year = year_filter if year_filter else combined['year'].unique().tolist()
quarter = quarter_filter if quarter_filter else ['Q1', 'Q2', 'Q3', 'Q4']
states = selected_states if selected_states else combined['customer_state_full'].unique().tolist()
categories = selected_categories if selected_categories else combined['product_category_name_english'].unique().tolist()

combined_filtered = combined[
    (combined['year'].isin(year)) &
    (combined['quarter'].isin(quarter)) &
    (combined['customer_state_full'].isin(states)) &
    (combined['product_category_name_english'].isin(categories))
]

payments_filtered = payments[payments['order_id'].isin(combined_filtered['order_id'].unique())]

visual = st.radio("Pilih Visualisasi", ["Pendapatan Bulanan", "Metode Pembayaran", "Peta RFM per State"])

if visual == "Pendapatan Bulanan":
    st.subheader("Visualisasi 1: Total Pendapatan per Bulan")

    monthly_revenue = combined_filtered.groupby(['year', 'month']).agg({'total_price': 'sum'}).reset_index()
    pivot_revenue = monthly_revenue.pivot(index='month', columns='year', values='total_price').fillna(0)

    months_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    available_months = pivot_revenue.index.tolist()
    month_names = [months_labels[m-1] for m in available_months]
    width = 0.35

    total_line_2017 = pivot_revenue[2017] if 2017 in pivot_revenue.columns else None
    total_line_2018 = pivot_revenue[2018] if 2018 in pivot_revenue.columns else None

    if (total_line_2017 is None or total_line_2017.sum() == 0) and (total_line_2018 is None or total_line_2018.sum() == 0):
        st.warning("Data tidak tersedia untuk kombinasi filter yang dipilih.")
    else:
        fig, ax = plt.subplots(figsize=(15,7))

        if total_line_2017 is not None:
            ax.bar(np.array(available_months) - width/2, total_line_2017, width=width, label='2017', color='#87CEFA')
            ax.plot(available_months, total_line_2017, color='#4682B4', marker='o', linewidth=2, label='Trend 2017')

        if total_line_2018 is not None:
            ax.bar(np.array(available_months) + width/2, total_line_2018, width=width, label='2018', color='#1E90FF')
            ax.plot(available_months, total_line_2018, color='#00008B', marker='o', linewidth=2, label='Trend 2018')

        ax.set_xticks(available_months)
        ax.set_xticklabels(month_names)
        ax.set_xlabel('Bulan', fontsize=13)
        ax.set_ylabel('Total Pendapatan (x$100,000)', fontsize=13)
        ax.set_title('Total Pendapatan per Bulan dan Tren Pertumbuhan', fontsize=16)

        max_y = pivot_revenue.max().max() / 100000
        if pd.notna(max_y):
            max_y = int(np.ceil(max_y / 2) * 2)
            ax.set_yticks(np.arange(0, (max_y + 2), 2) * 100000)
            ax.set_yticklabels([str(i) for i in range(0, (max_y + 2), 2)])

        ax.grid(axis='y', linestyle='--', alpha=0.7)
        ax.legend()

        plt.tight_layout()
        st.pyplot(fig)

elif visual == "Metode Pembayaran":
    st.subheader("Visualisasi 2: Frekuensi Penggunaan Metode Pembayaran")

    # Gabungkan informasi dari combined_filtered ke payments_filtered
    payments_joined = payments_filtered.merge(
        combined_filtered[['order_id', 'year', 'quarter', 'customer_state_full', 'product_category_name_english']],
        on='order_id',
        how='inner'
    )

    # Ambil pasangan unik (order_id, payment_type)
    payment_unique = payments_joined[['order_id', 'payment_type']].drop_duplicates()

    # Hitung jumlah penggunaan tiap metode pembayaran
    payment_counts = payment_unique['payment_type'].value_counts().reset_index()
    payment_counts.columns = ['payment_type', 'count']

    # Plot bar chart horizontal
    if payment_counts.empty:
        st.warning("Data tidak tersedia untuk kombinasi filter yang dipilih.")
    else:
        fig, ax = plt.subplots(figsize=(10,6))
        ax.barh(payment_counts['payment_type'], payment_counts['count'], color='#1E90FF')
        ax.set_xlabel('Jumlah Pengguna', fontsize=13)
        ax.set_ylabel('Tipe Pembayaran', fontsize=13)
        ax.set_title('Frekuensi Metode Pembayaran Berdasarkan Unik Order', fontsize=16)
        ax.grid(axis='x', linestyle='--', alpha=0.7)

        for i in range(len(payment_counts)):
            ax.text(payment_counts['count'][i] + 5, i, payment_counts['count'][i], va='center', fontsize=10)

        plt.tight_layout()
        st.pyplot(fig)

elif visual == "Peta RFM per State":
    st.subheader("Visualisasi 3: Peta RFM Berdasarkan Provinsi")
    def_date = combined['order_purchase_timestamp'].max()
    rfm_metric = st.radio("Pilih Metrik yang Ditampilkan", ["Recency", "Frequency", "Monetary"])
    recency_date = st.date_input(f"Tanggal Acuan untuk {rfm_metric}", def_date)
    

    rfm_df = combined_filtered.copy()

    # Hitung Recency
    recency_data = rfm_df.groupby('customer_state')['order_purchase_timestamp'].max().reset_index()
    recency_data.rename(columns={'customer_state': 'state_code'}, inplace=True)
    recency_data['Recency'] = (pd.to_datetime(recency_date) - recency_data['order_purchase_timestamp']).dt.days.clip(lower=0)

    # Hitung Frequency
    frequency_data = rfm_df.groupby('customer_state')['order_id'].nunique().reset_index()
    frequency_data.columns = ['state_code', 'Frequency']

    # Hitung Monetary
    monetary_data = rfm_df.groupby('customer_state')['total_price'].sum().reset_index()
    monetary_data.columns = ['state_code', 'Monetary']

    # Gabungkan semua ke satu tabel
    rfm_state = recency_data.merge(frequency_data, on='state_code').merge(monetary_data, on='state_code')
    rfm_state['customer_state_full'] = rfm_state['state_code'].map(state_mapping)


    # Konversi ke format geo choropleth
    def format_hover(row):
        if rfm_metric == "Recency":
            return f"<b>{row['customer_state_full']}</b><br>{row['Recency']} hari sejak pembelian terakhir"
        elif rfm_metric == "Frequency":
            return f"<b>{row['customer_state_full']}</b><br>{row['Frequency']} x pembelian"
        else:
            return f"<b>{row['customer_state_full']}</b><br>${row['Monetary']:,.0f} total pembelian"

    rfm_state['hover_text'] = rfm_state.apply(format_hover, axis=1)

    color_col = rfm_metric
    reverse_color = True if rfm_metric == "Recency" else False

    fig = px.choropleth(
        rfm_state,
        geojson=brazil_geojson,
        locations="state_code",
        featureidkey="properties.sigla",
        color=color_col,
        color_continuous_scale='Blues',
        hover_name="customer_state_full",
        custom_data=["hover_text"]
    )

    fig.update_traces(
        hovertemplate='%{customdata[0]}<extra></extra>',
        marker_line_width=0.5
    )

    fig.update_geos(fitbounds="locations", visible=False)

    fig.update_layout(
        title_text=f"Peta {rfm_metric} Berdasarkan Provinsi",
        geo=dict(showframe=False, showcoastlines=False)
    )

    st.plotly_chart(fig, use_container_width=True)
