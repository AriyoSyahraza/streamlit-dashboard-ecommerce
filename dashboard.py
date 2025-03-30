import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Load data gabungan
@st.cache_data
def load_data():
    df = pd.read_csv('dataset/cleaned_ecommerce_data.csv')
    df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'])
    return df

df = load_data()

# Judul
st.title("📊 E-Commerce Dashboard")
st.markdown("Menampilkan analisis dari transaksi dan metode pembayaran berdasarkan data yang telah dibersihkan.")

# Sidebar navigasi
option = st.sidebar.selectbox("Pilih Analisis", 
                              ("Pertanyaan 1: Tren Bulanan", 
                               "Pertanyaan 2: Metode Pembayaran"))

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
