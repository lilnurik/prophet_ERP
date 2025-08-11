#!/usr/bin/env python3
"""
Demo script showing the complete Prophet ERP system functionality.
This script demonstrates:
1. Adding sales data
2. Adding inventory data
3. Getting AI-powered forecasts
4. Getting production recommendations
"""

import requests
import json
import time
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:5000"
SKU = "DEMO_PRODUCT"

def pretty_print(title, data):
    """Pretty print JSON response."""
    print(f"\n{'='*50}")
    print(f"📊 {title}")
    print(f"{'='*50}")
    print(json.dumps(data, indent=2))

def demo_sales_data():
    """Add sample sales data for demonstration."""
    print("🔄 Adding sample sales data...")
    
    # Generate 30 days of sales data with an upward trend
    base_date = datetime(2024, 1, 1)
    for i in range(30):
        date = base_date + timedelta(days=i)
        # Simulate growing demand with some variability
        quantity = 50 + i * 2 + (i % 7) * 3  # Growing trend with weekly pattern
        
        data = {
            "sku": SKU,
            "date": date.strftime("%Y-%m-%d"),
            "quantity": quantity
        }
        
        response = requests.post(f"{BASE_URL}/sales", json=data)
        if response.status_code == 201:
            print(f"  ✅ Added sales: {date.strftime('%Y-%m-%d')} -> {quantity} units")
        else:
            print(f"  ❌ Failed to add sales: {response.status_code}")
            
    print(f"✅ Added 30 days of sales data for {SKU}")

def demo_inventory_data():
    """Add current inventory level."""
    print("\n🔄 Setting current inventory...")
    
    data = {
        "sku": SKU,
        "date": "2024-01-31",
        "quantity": 200  # Current stock level
    }
    
    response = requests.post(f"{BASE_URL}/inventory", json=data)
    if response.status_code == 201:
        result = response.json()
        pretty_print("Inventory Updated", result)
    else:
        print(f"❌ Failed to update inventory: {response.status_code}")

def demo_forecast():
    """Get AI-powered demand forecast."""
    print("\n🔄 Generating AI forecast...")
    
    response = requests.get(f"{BASE_URL}/forecast/{SKU}?days_ahead=14")
    if response.status_code == 200:
        result = response.json()
        pretty_print("AI Demand Forecast (14 days)", result)
        
        # Show forecast summary
        forecast_data = result['forecast_data']
        total_demand = sum(item['forecast'] for item in forecast_data)
        avg_daily = total_demand / len(forecast_data)
        
        print(f"\n📈 FORECAST SUMMARY:")
        print(f"  • Forecast Period: {len(forecast_data)} days")
        print(f"  • Total Predicted Demand: {total_demand:.1f} units")
        print(f"  • Average Daily Demand: {avg_daily:.1f} units")
        print(f"  • Range: {forecast_data[0]['forecast']:.1f} - {forecast_data[-1]['forecast']:.1f} units")
        
    else:
        print(f"❌ Failed to get forecast: {response.status_code}")
        print(response.text)

def demo_recommendations():
    """Get production recommendations."""
    print("\n🔄 Getting production recommendations...")
    
    response = requests.get(f"{BASE_URL}/recommendations/{SKU}?days_ahead=14")
    if response.status_code == 200:
        result = response.json()
        pretty_print("Production Recommendations", result)
        
        # Show recommendation summary
        print(f"\n🏭 PRODUCTION RECOMMENDATION:")
        print(f"  • Recommended Production: {result['recommended_quantity']} units")
        print(f"  • Current Stock: {result['current_stock']} units")
        print(f"  • Forecasted Demand: {result['forecasted_demand']} units")
        print(f"  • Safety Stock: {result['safety_stock']} units")
        print(f"  • Reasoning: {result['reasoning']}")
        
    else:
        print(f"❌ Failed to get recommendations: {response.status_code}")
        print(response.text)

def check_health():
    """Check system health."""
    print("🔄 Checking system health...")
    
    response = requests.get(f"{BASE_URL}/status")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ System Status: {result['status'].upper()}")
        print(f"  Message: {result['message']}")
    else:
        print(f"❌ Health check failed: {response.status_code}")

def main():
    """Run the complete demo."""
    print("🚀 Prophet ERP System Demo")
    print("=" * 50)
    
    try:
        # Check if server is running
        check_health()
        
        # Add sample data
        demo_sales_data()
        demo_inventory_data()
        
        # Wait a moment for data to be processed
        time.sleep(1)
        
        # Get AI insights
        demo_forecast()
        demo_recommendations()
        
        print("\n" + "=" * 50)
        print("🎉 Demo completed successfully!")
        print("=" * 50)
        print("\nNext steps:")
        print("1. View models created in ./models/ directory")
        print("2. Try different SKUs and date ranges")
        print("3. Experiment with the API endpoints")
        print("4. Deploy using docker-compose for production")
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to the server.")
        print("Please make sure the Flask app is running on http://localhost:5000")
        print("\nTo start the server:")
        print("  cd /path/to/prophet_ERP")
        print("  export DATABASE_URL='sqlite:///prophet_erp.db'")
        print("  python init_db.py")
        print("  python app/main.py")
        
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")

if __name__ == "__main__":
    main()