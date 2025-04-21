import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import requests

# Load orders data
@st.cache_data
def load_orders_data():
    df = pd.read_csv("dataset/orders_merged.csv")
    df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])
    return df

# Load payments data
@st.cache_data
def load_payment_data():
    df = pd.read_csv("dataset/payment_clean.csv")
    return df

orders_df = load_orders_data()
payments_df = load_payment_data()

st.title("📊 E-Commerce Dashboard")

option = st.sidebar.selectbox("Pilih Analisis", [
    "Pertanyaan 1: Tren Bulanan",
    "Pertanyaan 2: Metode Pembayaran",
    "Pertanyaan 3: RFM per Kota/Provinsi"
])

# --- PERTANYAAN 1 ---
if option == "Pertanyaan 1: Tren Bulanan":
    orders_df['order_month'] = orders_df['order_purchase_timestamp'].dt.to_period('M')
    orders_df['year'] = orders_df['order_purchase_timestamp'].dt.year
    orders_df['month'] = orders_df['order_purchase_timestamp'].dt.month

    monthly_summary = orders_df.groupby('order_month').agg({
        'order_id': 'nunique',
        'total_revenue': 'sum'
    }).reset_index().rename(columns={'order_id': 'total_orders'})

    monthly_summary['year'] = monthly_summary['order_month'].dt.year
    monthly_summary['month'] = monthly_summary['order_month'].dt.month

    pivot_orders = monthly_summary.pivot(index='month', columns='year', values='total_orders')
    pivot_revenue = monthly_summary.pivot(index='month', columns='year', values='total_revenue')

    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    x = range(1, 13)
    width = 0.35

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

    orders_2017 = (pivot_orders[2017] / 1000).round(2)
    orders_2018 = (pivot_orders[2018] / 1000).round(2)

    bars_2017 = ax1.bar([i - width/2 for i in x], orders_2017, width=width, label='2017', color='#add8e6')
    bars_2018 = ax1.bar([i + width/2 for i in x], orders_2018, width=width, label='2018', color='#4682b4')
    ax1.set_ylabel('Jumlah Pesanan (x1000)')
    ax1.set_title('Jumlah Pesanan per Bulan (2017–2018)')
    ax1.legend()
    ax1.set_xticks(x)
    ax1.set_xticklabels(months)

    for bar in bars_2017:
        ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.01, f'{bar.get_height():.1f}', ha='center')
    for bar in bars_2018:
        ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.01, f'{bar.get_height():.1f}', ha='center')

    revenue_2017 = (pivot_revenue[2017] / 100000).round(2)
    revenue_2018 = (pivot_revenue[2018] / 100000).round(2)

    bars_rev_2017 = ax2.bar([i - width/2 for i in x], revenue_2017, width=width, label='2017', color='#add8e6')
    bars_rev_2018 = ax2.bar([i + width/2 for i in x], revenue_2018, width=width, label='2018', color='#4682b4')
    ax2.set_ylabel('Pendapatan (x100.000 R$)')
    ax2.set_title('Total Pendapatan per Bulan (2017–2018)')
    ax2.legend()
    ax2.set_xticks(x)
    ax2.set_xticklabels(months)

    for bar in bars_rev_2017:
        ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.01, f'{bar.get_height():.1f}', ha='center')
    for bar in bars_rev_2018:
        ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.01, f'{bar.get_height():.1f}', ha='center')

    plt.tight_layout()
    st.pyplot(fig)

# --- PERTANYAAN 2 ---
elif option == "Pertanyaan 2: Metode Pembayaran":
    payment_summary = payments_df.groupby('payment_type').agg({
        'order_id': 'count',
        'payment_value': 'sum'
    }).reset_index().rename(columns={
        'order_id': 'total_transactions',
        'payment_value': 'total_payment'
    })
    payment_summary = payment_summary.sort_values(by='total_payment', ascending=False)


    fig, ax = plt.subplots(1, 2, figsize=(16, 6))

    ax[0].bar(payment_summary['payment_type'],
              (payment_summary['total_transactions'] / 10000).round(2), color='#4682b4')
    ax[0].set_title("Jumlah Transaksi (x10.000)")
    ax[0].set_ylabel("Transaksi")
    for bar in ax[0].containers[0]:
        height = bar.get_height()
        ax[0].text(bar.get_x() + bar.get_width()/2., height + 0.1, f'{height:.2f}', ha='center')

    ax[1].bar(payment_summary['payment_type'],
              (payment_summary['total_payment'] / 1000000).round(2), color='#5dade2')
    ax[1].set_title("Total Pembayaran (x1.000.000 R$)")
    ax[1].set_ylabel("Total")
    for bar in ax[1].containers[0]:
        height = bar.get_height()
        ax[1].text(bar.get_x() + bar.get_width()/2., height + 0.1, f'{height:.2f}', ha='center')

    st.pyplot(fig)

# --- PERTANYAAN 3 ---
elif option == "Pertanyaan 3: RFM per Kota/Provinsi":
    st.subheader("Analisis RFM Berdasarkan Kota & Provinsi")
    latest_date = orders_df['order_purchase_timestamp'].max()

    rfm_by_location = orders_df.groupby(['customer_city', 'customer_state']).agg({
        'order_purchase_timestamp': lambda x: int((latest_date - x.max()).total_seconds() / 86400),
        'order_id': 'nunique',
        'total_revenue': 'sum'
    }).reset_index()

    rfm_by_location.columns = ['city', 'state', 'Recency', 'Frequency', 'Monetary']
    rfm_by_location['location'] = rfm_by_location['city'] + ', ' + rfm_by_location['state']

    top_rfm = st.selectbox("Pilih Metode RFM:", ["Recency", "Frequency", "Monetary"])
    rfm_top = rfm_by_location.sort_values(
        by=top_rfm if top_rfm != "Recency" else "Recency",
        ascending=(top_rfm == "Recency")
    ).head(10)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.barh(rfm_top['location'], rfm_top[top_rfm], color='#4682b4')
    ax.invert_yaxis()
    ax.set_title(f"Top 10 {top_rfm} Berdasarkan Lokasi")
    ax.set_xlabel(top_rfm)
    ax.set_xlim(left=0, right=rfm_top[top_rfm].max() + 5)

    for i, v in enumerate(rfm_top[top_rfm]):
        label = f'{v:.2f}' if top_rfm == "Monetary" else f'{int(v)}'
        ax.text(v + 0.5, i, label, va='center')

    st.pyplot(fig)

    # Tambahkan catatan jika Recency dipilih
    if top_rfm == "Recency":
        st.caption("💡 *Catatan: Nilai Recency '0' menunjukkan pelanggan di kota tersebut melakukan transaksi terakhirnya pada hari yang sama dengan tanggal referensi (paling baru).*")

