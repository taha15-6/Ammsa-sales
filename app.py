import matplotlib
matplotlib.use('Agg')  # Required for generating plots on a server without a screen

from flask import Flask, render_template
import pandas as pd
import io
import base64
import seaborn as sns
import matplotlib.pyplot as plt

app = Flask(__name__)

# Global configuration for plots
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)

def load_data():
    """Loads and cleans the dataset."""
    try:
        # Ensure Ammsa_Sales.csv is in the same directory
        df = pd.read_csv('Ammsa_Sales.csv')
        
        # Clean numeric columns removing currency symbols or commas
        cols_to_clean = ['Total Price', 'Total Cost', 'Expense Amount', 'Outstanding Balance']
        for col in cols_to_clean:
            if col in df.columns and df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.replace(',', '').astype(float)
        
        # Convert dates
        if 'Order Date' in df.columns:
            df['Order Date'] = pd.to_datetime(df['Order Date'])
            df['Month_Year'] = df['Order Date'].dt.to_period('M').astype(str)
            
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame()

def create_plot(plot_func, df):
    """Helper to render a matplotlib plot to a base64 string."""
    img = io.BytesIO()
    plt.figure()
    plot_func(df)
    plt.tight_layout()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()
    return f"data:image/png;base64,{plot_url}"

# --- Visualization Functions ---

def plot_monthly_trend(df):
    monthly_sales = df.groupby('Month_Year')['Total Price'].sum().reset_index()
    sns.lineplot(x='Month_Year', y='Total Price', data=monthly_sales, marker='o', color='blue')
    plt.title('Monthly Revenue Trend')
    plt.ylabel('Revenue')
    plt.xticks(rotation=45)

def plot_top_products(df):
    top_products = df.groupby('Product')['Total Price'].sum().nlargest(10).reset_index()
    sns.barplot(x='Total Price', y='Product', data=top_products, palette='viridis')
    plt.title('Top 10 Products by Revenue')

def plot_city_balance(df):
    city_balance = df.groupby('City')['Outstanding Balance'].sum().nlargest(10).reset_index()
    sns.barplot(x='City', y='Outstanding Balance', data=city_balance, palette='Reds_r')
    plt.title('Highest Outstanding Balance by City')
    plt.xticks(rotation=45)

def plot_expense_dist(df):
    expense_data = df.groupby('Expense Type')['Expense Amount'].sum()
    plt.pie(expense_data, labels=expense_data.index, autopct='%1.1f%%', startangle=140, colors=sns.color_palette('pastel'))
    plt.title('Expense Type Distribution')

@app.route('/')
def dashboard():
    df = load_data()
    
    if df.empty:
        return "Error: Could not load Ammsa_Sales.csv. Please ensure the file is in the root directory."

    # Calculate KPIs
    total_revenue = df['Total Price'].sum()
    total_outstanding = df['Outstanding Balance'].sum()
    net_profit = total_revenue - df['Total Cost'].sum()
    top_city = df.groupby('City')['Total Price'].sum().idxmax()

    # Generate Plots
    viz_trend = create_plot(plot_monthly_trend, df)
    viz_products = create_plot(plot_top_products, df)
    viz_balance = create_plot(plot_city_balance, df)
    viz_expenses = create_plot(plot_expense_dist, df)

    return render_template('dashboard.html', 
                           revenue=f"{total_revenue:,.0f}",
                           outstanding=f"{total_outstanding:,.0f}",
                           profit=f"{net_profit:,.0f}",
                           top_city=top_city,
                           plot_trend=viz_trend,
                           plot_products=viz_products,
                           plot_balance=viz_balance,
                           plot_expenses=viz_expenses)

if __name__ == '__main__':
    app.run(debug=True)