import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression

# Initialize session state for storing product and sales data
if 'products' not in st.session_state:
    st.session_state['products'] = []

if 'sales' not in st.session_state:
    st.session_state['sales'] = []

def prepare_data(data):
    data['Sale Date'] = pd.to_datetime(data['Sale Date'])
    data['DayOfYear'] = data['Sale Date'].dt.dayofyear
    data['Year'] = data['Sale Date'].dt.year
    return data

def train_model(data):
    data = prepare_data(data)
    X = data[['DayOfYear', 'Year']]
    y = data['Earnings']
    
    if X.empty or y.empty:
        st.error("The data is insufficient for training the model. Please add more product data.")
        return None

    if len(data) < 5:
        st.warning("Insufficient data for train-test split. Training on entire dataset.")
        model = LinearRegression()
        model.fit(X, y)
    else:
        try:
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        except ValueError as e:
            st.error(f"ValueError during train_test_split: {e}")
            return None

        model = LinearRegression()
        model.fit(X_train, y_train)

    return model

def predict_earnings_simple(today_earnings, days_ahead):
    daily_earnings_rate = today_earnings
    total_predicted_earnings = daily_earnings_rate * days_ahead
    return total_predicted_earnings

def calculate_financials(data, sales_data):
    today = datetime.today().strftime("%Y-%m-%d")
    today_sales = pd.DataFrame(sales_data)
    today_sales['Date'] = pd.to_datetime(today_sales['Date'])
    today_data = today_sales[today_sales['Date'] == today]
    today_data['Profit'] = today_data['Quantity Sold'] * (today_data['Selling Price'] - data.set_index('Name').loc[today_data['Product Name']]['Cost Price'].values)

    total_profit = today_data[today_data['Profit'] > 0]['Profit'].sum()
    total_loss = today_data[today_data['Profit'] < 0]['Profit'].sum()
    total_earnings = total_profit + total_loss

    product_earnings = today_data.groupby('Product Name')['Profit'].sum().reset_index()

    return total_profit, total_loss, total_earnings, product_earnings

# Display image and title side by side
col1, col2 = st.columns([1, 3])
with col1:
    st.image("sales.jpg", use_column_width=True)
with col2:
    st.title("Product Sales Analysis")

add_product_button = st.button('Add Product Data')

if add_product_button:
    st.session_state['add_product'] = True

if 'add_product' in st.session_state and st.session_state['add_product']:
    st.header('Add Product Details')
    with st.form(key='product_form'):
        product_id = st.number_input('Product ID', min_value=1, step=1)
        product_name = st.text_input('Product Name')
        cost_price = st.number_input('Cost Price', min_value=0.0, step=0.01)
        quantity_available = st.number_input('Quantity Available', min_value=0, step=1)
        
        if st.form_submit_button('Save Product'):
            product_data = {
                'ID': product_id,
                'Name': product_name,
                'Cost Price': cost_price,
                'Quantity Available': quantity_available
            }
            st.session_state['products'].append(product_data)
            st.success('Product added successfully!')
            st.session_state['add_product'] = False

add_sales_button = st.button('Add Sales Data')

if add_sales_button:
    st.session_state['add_sales'] = True

if 'add_sales' in st.session_state and st.session_state['add_sales']:
    st.header('Add Sales Details')
    with st.form(key='sales_form'):
        sale_date = st.date_input('Sale Date', value=datetime.today())
        product_name = st.selectbox('Product Name', options=[p['Name'] for p in st.session_state['products']])
        quantity_sold = st.number_input('Quantity Sold', min_value=1, step=1)
        selling_price = st.number_input('Selling Price', min_value=0.0, step=0.01)
        
        if st.form_submit_button('Save Sale'):
            sales_data = {
                'Date': sale_date,
                'Product Name': product_name,
                'Quantity Sold': quantity_sold,
                'Selling Price': selling_price
            }
            st.session_state['sales'].append(sales_data)
            st.success('Sale added successfully!')
            st.session_state['add_sales'] = False

if st.button('Generate Report'):
    df_products = pd.DataFrame(st.session_state['products'])
    df_sales = pd.DataFrame(st.session_state['sales'])
    
    if not df_sales.empty:
        total_profit, total_loss, total_earnings, product_earnings = calculate_financials(df_products, df_sales)
        
        st.markdown("""
        <style>
        .report-section {
            background-color: #162447;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            transition: all 0.3s ease;
            color: white;
        }
        .report-section:hover {
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3);
        }
        .report-section h3 {
            color: #ffab40;
            font-size: 24px;
        }
        .report-section p {
            color: white;
            font-size: 18px;
        }
        .table-section {
            background-color: #1b1b2f;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            transition: all 0.3s ease;
            color: white;
        }
        .table-section:hover {
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3);
        }
        .table-section table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        .table-section th, .table-section td {
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        .table-section th {
            background-color: #162447;
            color: #ffab40;
        }
        .table-section td {
            background-color: #1b1b2f;
            color: white;
        }
        .table-section tr:nth-child(even) {
            background-color: #1b1b2f;
        }
        .table-section tr:hover {
            background-color: #162447;
        }
        .section-title {
            font-size: 26px;
            color: #ffab40;
            margin-bottom: 20px;
        }
        .card {
            background-color: #162447;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            transition: all 0.3s ease;
            margin-bottom: 20px;
            color: white;
            text-align: center;
            font-size: 20px;
        }
        .card:hover {
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3);
        }
        .card h4 {
            color: #ffab40;
            font-size: 22px;
        }
        .card p {
            color: white;
            font-size: 18px;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="card">
            <h4>Sales Prediction</h4>
            <p><strong>Sales after a month:</strong> ₹{predict_earnings_simple(total_earnings, 30):.2f}</p>
            <p><strong>Sales after a year:</strong> ₹{predict_earnings_simple(total_earnings, 365):.2f}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="card">
            <h4>Financials</h4>
            <p><strong>Today's Total Profit:</strong> ₹{total_profit:.2f}</p>
            <p><strong>Today's Total Loss:</strong> ₹{total_loss:.2f}</p>
            <p><strong>Today's Total Earnings:</strong> ₹{total_earnings:.2f}</p>
            <p><strong>Per Product Earnings:</strong></p>
            <ul>
                {''.join([f"<li>{row['Product Name']}: ₹{row['Profit']:.2f}</li>" for index, row in product_earnings.iterrows()])}
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        total_quantity_sold = df_sales.groupby('Product Name')['Quantity Sold'].sum().reset_index().sort_values(by='Quantity Sold', ascending=False).head(5)
        
        st.markdown(f"""
        <div class="table-section">
            <h3 class="section-title">Top Rated Products & Customer Satisfaction (Top 5 Products)</h3>
            <table>
                <tr>
                    <th>Product Name</th>
                    <th>Total Quantity Sold</th>
                </tr>
                {''.join([f"<tr><td>{row['Product Name']}</td><td>{row['Quantity Sold']:.2f}</td></tr>" for index, row in total_quantity_sold.iterrows()])}
            </table>
        </div>
        """, unsafe_allow_html=True)
