import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression

# Initialize session state for storing product data
if 'products' not in st.session_state:
    st.session_state['products'] = []

def prepare_data(data):
    data['Date'] = pd.to_datetime(data['Date'])
    data['DayOfYear'] = data['Date'].dt.dayofyear
    data['Year'] = data['Date'].dt.year
    data['Earnings'] = data['Quantity'] * (data['Selling Price'] - data['Cost Price'])
    return data

def train_model(data):
    # Prepare data
    data = prepare_data(data)
    X = data[['DayOfYear', 'Year']]
    y = data['Earnings']
    
    # Check for empty DataFrame
    if X.empty or y.empty:
        st.error("The data is insufficient for training the model. Please add more product data.")
        return None

    # Train-test split
    try:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    except ValueError as e:
        st.error(f"ValueError during train_test_split: {e}")
        return None

    # Train model
    model = LinearRegression()
    model.fit(X_train, y_train)

    return model

def predict_earnings(model, days_ahead, reference_earnings):
    today = datetime.today()
    future_dates = [today + timedelta(days=i) for i in range(1, days_ahead + 1)]
    future_data = pd.DataFrame({
        'Date': future_dates,
        'DayOfYear': [date.timetuple().tm_yday for date in future_dates],
        'Year': [date.year for date in future_dates]
    })
    future_data['Predicted Earnings'] = model.predict(future_data[['DayOfYear', 'Year']])
    total_predicted_earnings = future_data['Predicted Earnings'].sum()
    return total_predicted_earnings

def calculate_financials(data, quantity_col, cost_col, price_col):
    today = datetime.today().strftime("%Y-%m-%d")
    today_data = data[data['Date'] == today]
    today_data['Total'] = today_data[quantity_col] * (today_data[price_col] - today_data[cost_col])
    
    total_profit = today_data[today_data['Total'] > 0]['Total'].sum()
    total_loss = today_data[today_data['Total'] < 0]['Total'].sum()
    total_earnings = total_profit + total_loss
    
    product_earnings = today_data.groupby('Name')['Total'].sum().reset_index()
    
    return total_profit, total_loss, total_earnings, product_earnings

# Display image and title side by side
col1, col2 = st.columns([1, 3])
with col1:
    st.image("sales.jpg", use_column_width=True)
with col2:
    st.title("Product Sales Analysis")

# Add Product Data Button
add_product_button = st.button('Add Product Data')

if add_product_button:
    st.session_state['add_product'] = True

# Product addition form
if 'add_product' in st.session_state and st.session_state['add_product']:
    st.header('Add Product Details')
    
    product_id = st.number_input('Product ID', min_value=1, step=1)
    product_name = st.text_input('Product Name')
    product_description = st.text_area('Product Description')
    quantity_type = st.selectbox('Quantity Type', ['Gram', 'Kilogram', 'Litre', 'Unit'])
    sku = st.text_input('SKU')
    quantity = st.number_input('Quantity', min_value=0, step=1)
    product_cost = st.number_input('Product Cost (in rupees)', min_value=0, step=1)
    sell_price = st.number_input('Sell Price (in rupees)', min_value=0, step=1)
    selected_date = st.date_input('Select Date', datetime.today())
    
    save_details_button = st.button('Save Details')
    
    if save_details_button:
        # Save the product details to session state
        new_product = {
            'ID': product_id,
            'Name': product_name,
            'Description': product_description,
            'Quantity Type': quantity_type,
            'SKU': sku,
            'Quantity': quantity,
            'Cost Price': product_cost,
            'Selling Price': sell_price,
            'Date': selected_date.strftime("%Y-%m-%d")
        }
        st.session_state['products'].append(new_product)
        st.session_state['add_product'] = False
        st.success('Product details saved successfully!')

# Display products and generate report button
if st.session_state['products']:
    st.header('Products Added')
    for i, product in enumerate(st.session_state['products']):
        with st.expander(f"Product {i + 1}: {product['Name']}"):
            st.markdown(f"""
            <div style="background-color: #f9f9f9; padding: 10px; border-radius: 5px; color: black;">
                <strong>ID:</strong> {product['ID']}<br>
                <strong>Name:</strong> {product['Name']}<br>
                <strong>Description:</strong> {product['Description']}<br>
                <strong>Quantity Type:</strong> {product['Quantity Type']}<br>
                <strong>SKU:</strong> {product['SKU']}<br>
                <strong>Quantity:</strong> {product['Quantity']}<br>
                <strong>Cost Price:</strong> ₹{product['Cost Price']}<br>
                <strong>Selling Price:</strong> ₹{product['Selling Price']}<br>
                <strong>Date:</strong> {product['Date']}
            </div>
            """, unsafe_allow_html=True)
        
    generate_report_button = st.button('Generate Report')
    
    if generate_report_button:
        # Convert session state products to DataFrame
        df = pd.DataFrame(st.session_state['products'])

        # Ensure correct data types
        df['Quantity'] = df['Quantity'].astype(float)
        df['Cost Price'] = df['Cost Price'].astype(float)
        df['Selling Price'] = df['Selling Price'].astype(float)

        # Train a machine learning model
        model = train_model(df)
        
        if model:
            # Calculate today's earnings to use as a reference for future predictions
            _, _, today_earnings, _ = calculate_financials(df, 'Quantity', 'Cost Price', 'Selling Price')
            
            # Predict earnings for the next 30 days based on today's earnings
            earnings_month = predict_earnings(model, 30, today_earnings)
            
            # Predict earnings for the next 365 days based on the monthly prediction
            earnings_year = predict_earnings(model, 365, today_earnings)  # Adjust the input to be today's earnings
            
            # Calculate total profit, total loss, total earnings, and per-product earnings
            total_profit, total_loss, total_earnings, product_earnings = calculate_financials(df, 'Quantity', 'Cost Price', 'Selling Price')
            
            # Generate report
            st.header('Report')
            
            st.markdown("""
            <style>
            .report-section {
                background-color: #2a151a;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                color: white;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
                transition: all 0.3s ease;
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
                <p><strong>Sales after a month:</strong> ₹{earnings_month:.2f}</p>
                <p><strong>Sales after a year:</strong> ₹{earnings_year:.2f}</p>
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
                    {''.join([f"<li>{row['Name']}: ₹{row['Total']:.2f}</li>" for index, row in product_earnings.iterrows()])}
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            # Calculate top rated products and customer satisfaction
            numeric_columns = df.select_dtypes(include='number').columns
            top_products = df.groupby('Name', as_index=False)[numeric_columns].sum().sort_values(by='Quantity', ascending=False).head(5)
            
            st.markdown(f"""
            <div class="table-section">
                <h3 class="section-title">Top Rated Products & Customer Satisfaction (Top 5 Products)</h3>
                <table>
                    <tr>
                        <th>Product Name</th>
                        <th>Total Quantity Sold</th>
                    </tr>
                    {''.join([f"<tr><td>{row['Name']}</td><td>{row['Quantity']:.2f}</td></tr>" for index, row in top_products.iterrows()])}
                </table>
            </div>
            """, unsafe_allow_html=True)
