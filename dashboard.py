import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import requests

# Load data gabungan
@st.cache_data
def load_data():
    df = pd.read_csv('dataset/combined_dashboard_dataset.csv')
    df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'])
    return df

df = load_data()

# Judul
st.title("📊 E-Commerce Dashboard")
st.markdown("Menampilkan analisis dari transaksi dan metode pembayaran berdasarkan data yang telah dibersihkan.")

# Sidebar navigasi
option = st.sidebar.selectbox("Pilih Analisis", 
                              ("Pertanyaan 1: Tren Bulanan", 
                               "Pertanyaan 2: Metode Pembayaran",
                               "Pertanyaan 3: RFM per State"))

# === PERTANYAAN 1 ===
if option == "Pertanyaan 1: Tren Bulanan":
    df['order_month'] = df['order_purchase_timestamp'].dt.to_period('M').astype(str)
    monthly = df.groupby('order_month').agg({
        'order_id': 'nunique',
        'payment_value': 'sum'
    }).reset_index().rename(columns={
        'order_id': 'total_orders',
        'payment_value': 'total_revenue'
    })
    monthly['month'] = pd.to_datetime(monthly['order_month']).dt.month
    monthly['year'] = pd.to_datetime(monthly['order_month']).dt.year
    pivot_orders = monthly.pivot(index='month', columns='year', values='total_orders')
    pivot_revenue = monthly.pivot(index='month', columns='year', values='total_revenue')
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    x = range(1, 13)

    fig, ax1 = plt.subplots(figsize=(10, 5))
    width = 0.35
    ax1.bar([i - width/2 for i in x], pivot_orders[2017], width=width, label='Orders 2017', color='#add8e6')
    ax1.bar([i + width/2 for i in x], pivot_orders[2018], width=width, label='Orders 2018', color='#4682b4')
    ax1.set_xticks(x)
    ax1.set_xticklabels(months)
    ax1.set_xlabel('Bulan')
    ax1.set_ylabel('Jumlah Pesanan')
    ax1.legend(loc='upper left')

    ax2 = ax1.twinx()
    ax2.plot(x, pivot_revenue[2017], color='darkred', marker='o', label='Revenue 2017')
    ax2.plot(x, pivot_revenue[2018], color='orange', marker='o', label='Revenue 2018')
    ax2.set_ylabel('Total Revenue (R$)')
    ax2.legend(loc='upper right')

    st.pyplot(fig)

# === PERTANYAAN 2 ===
elif option == "Pertanyaan 2: Metode Pembayaran":
    payment_summary = df.groupby('payment_type').agg({
        'payment_type': 'count',
        'payment_value': 'sum'
    }).rename(columns={
        'payment_type': 'total_transactions',
        'payment_value': 'total_payment'
    }).sort_values(by='total_transactions', ascending=False).reset_index()

    fig, ax = plt.subplots(1, 2, figsize=(14, 5))

    ax[0].bar(payment_summary['payment_type'], payment_summary['total_transactions'], color='#4682b4')
    ax[0].set_title("Jumlah Transaksi per Metode")
    ax[0].tick_params(axis='x', rotation=45)

    ax[1].bar(payment_summary['payment_type'], payment_summary['total_payment'], color='#5dade2')
    ax[1].set_title("Total Pembayaran per Metode")
    ax[1].tick_params(axis='x', rotation=45)

    st.pyplot(fig)

elif option == "Pertanyaan 3: RFM per State":
    st.markdown("### Visualisasi Total RFM per State (Brazil)")

    # Hitung ulang RFM berdasarkan customer_id
    df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'])
    latest_date = df['order_purchase_timestamp'].max()

    rfm = df.groupby('customer_state').agg({
        'order_purchase_timestamp': lambda x: (latest_date - x.max()).days,
        'order_id': 'nunique',
        'price': 'sum'
    }).reset_index()
    rfm.columns = ['customer_state', 'Recency', 'Frequency', 'Monetary']

    # Load GeoJSON
    @st.cache_data
    def load_geojson():
        url = 'https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson'
        return requests.get(url).json()

    geojson = load_geojson()

    # Pilihan metrik
    metric = st.selectbox("Pilih metrik yang ingin divisualisasikan:", ['Recency', 'Frequency', 'Monetary'])

    # Plot peta interaktif
    fig = px.choropleth(
        rfm,
        geojson=geojson,
        locations='customer_state',
        color=metric,
        featureidkey='properties.sigla',
        hover_name='customer_state',
        hover_data={'Recency': True, 'Frequency': True, 'Monetary': True},
        color_continuous_scale='Blues',
        title=f'Total {metric} per State di Brazil'
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r":0,"t":50,"l":0,"b":0})

    st.plotly_chart(fig, use_container_width=True)
