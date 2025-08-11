import pytest
import sys
import os
from datetime import date, datetime
import pandas as pd

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.services.forecasting import ForecastingService
from app.models import Sales, Inventory
from app.database import db
from app.main import create_app

@pytest.fixture
def app():
    """Create a Flask app for testing."""
    # Set testing configuration to use SQLite
    import os
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    
    app = create_app()
    app.config['TESTING'] = True
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()

@pytest.fixture
def forecasting_service(app):
    """Create a forecasting service for testing."""
    with app.app_context():
        return ForecastingService(models_dir='/tmp/test_models')

class TestForecastingService:
    
    def test_prepare_data_no_sales(self, app, forecasting_service):
        """Test _prepare_data with no sales data."""
        with app.app_context():
            result = forecasting_service._prepare_data('NONEXISTENT_SKU')
            assert result is None
    
    def test_prepare_data_with_sales(self, app, forecasting_service):
        """Test _prepare_data with existing sales data."""
        with app.app_context():
            # Add sample sales data
            sales1 = Sales(sku='TEST_SKU', date=date(2024, 1, 1), quantity=10)
            sales2 = Sales(sku='TEST_SKU', date=date(2024, 1, 2), quantity=20)
            sales3 = Sales(sku='TEST_SKU', date=date(2024, 1, 1), quantity=5)  # Same date
            
            db.session.add_all([sales1, sales2, sales3])
            db.session.commit()
            
            result = forecasting_service._prepare_data('TEST_SKU')
            
            assert result is not None
            assert len(result) == 2  # Two unique dates
            assert result.iloc[0]['y'] == 15  # Aggregated quantity for 2024-01-01
            assert result.iloc[1]['y'] == 20  # Quantity for 2024-01-02
    
    def test_get_current_stock_no_inventory(self, app, forecasting_service):
        """Test _get_current_stock with no inventory data."""
        with app.app_context():
            result = forecasting_service._get_current_stock('NONEXISTENT_SKU')
            assert result == 0.0
    
    def test_get_current_stock_with_inventory(self, app, forecasting_service):
        """Test _get_current_stock with existing inventory data."""
        with app.app_context():
            # Add sample inventory data
            inventory1 = Inventory(sku='TEST_SKU', date=date(2024, 1, 1), quantity=100)
            inventory2 = Inventory(sku='TEST_SKU', date=date(2024, 1, 2), quantity=150)  # Latest
            
            db.session.add_all([inventory1, inventory2])
            db.session.commit()
            
            result = forecasting_service._get_current_stock('TEST_SKU')
            assert result == 150.0  # Should return the latest inventory
    
    def test_calculate_safety_stock_insufficient_data(self, app, forecasting_service):
        """Test _calculate_safety_stock with insufficient data."""
        with app.app_context():
            # Add minimal sales data (less than 10 records)
            sales = Sales(sku='TEST_SKU', date=date(2024, 1, 1), quantity=10)
            db.session.add(sales)
            db.session.commit()
            
            result = forecasting_service._calculate_safety_stock('TEST_SKU')
            assert result == 0.0
    
    def test_calculate_safety_stock_sufficient_data(self, app, forecasting_service):
        """Test _calculate_safety_stock with sufficient data."""
        with app.app_context():
            # Add sufficient sales data
            for i in range(15):
                sales = Sales(sku='TEST_SKU', date=date(2024, 1, i+1), quantity=10 + i)
                db.session.add(sales)
            db.session.commit()
            
            result = forecasting_service._calculate_safety_stock('TEST_SKU')
            assert result >= 0.0  # Should calculate a positive safety stock
    
    def test_train_model_insufficient_data(self, app, forecasting_service):
        """Test train_model with insufficient data."""
        with app.app_context():
            # Add only one sales record (insufficient for training)
            sales = Sales(sku='TEST_SKU', date=date(2024, 1, 1), quantity=10)
            db.session.add(sales)
            db.session.commit()
            
            result = forecasting_service.train_model('TEST_SKU')
            assert result is False
    
    def test_train_model_sufficient_data(self, app, forecasting_service):
        """Test train_model with sufficient data."""
        with app.app_context():
            # Add sufficient sales data for training
            for i in range(30):
                sales = Sales(sku='TEST_SKU', date=date(2024, 1, i+1), quantity=10 + (i % 5))
                db.session.add(sales)
            db.session.commit()
            
            result = forecasting_service.train_model('TEST_SKU')
            assert result is True
    
    def test_forecast_no_model_no_data(self, app, forecasting_service):
        """Test forecast with no model and no data."""
        with app.app_context():
            result = forecasting_service.forecast('NONEXISTENT_SKU')
            assert result is None
    
    def test_recommend_production_no_data(self, app, forecasting_service):
        """Test recommend_production with no data."""
        with app.app_context():
            result = forecasting_service.recommend_production('NONEXISTENT_SKU')
            assert result is not None
            assert result['recommended_quantity'] == 0.0
            assert 'Unable to generate forecast' in result['reasoning']

class TestAPI:
    
    def test_health_check(self, client):
        """Test the health check endpoint."""
        response = client.get('/status')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
    
    def test_add_sales_valid_data(self, client):
        """Test adding sales with valid data."""
        sales_data = {
            'sku': 'TEST_SKU',
            'date': '2024-01-01',
            'quantity': 10.5
        }
        
        response = client.post('/sales', json=sales_data)
        assert response.status_code == 201
        data = response.get_json()
        assert data['message'] == 'Sales record added successfully'
        assert data['data']['sku'] == 'TEST_SKU'
    
    def test_add_sales_invalid_data(self, client):
        """Test adding sales with invalid data."""
        sales_data = {
            'sku': '',  # Invalid: empty SKU
            'date': '2024-01-01',
            'quantity': -10  # Invalid: negative quantity
        }
        
        response = client.post('/sales', json=sales_data)
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_add_production_valid_data(self, client):
        """Test adding production with valid data."""
        production_data = {
            'sku': 'TEST_SKU',
            'date': '2024-01-01',
            'quantity': 100
        }
        
        response = client.post('/production', json=production_data)
        assert response.status_code == 201
        data = response.get_json()
        assert data['message'] == 'Production record added successfully'
    
    def test_update_inventory_valid_data(self, client):
        """Test updating inventory with valid data."""
        inventory_data = {
            'sku': 'TEST_SKU',
            'date': '2024-01-01',
            'quantity': 50
        }
        
        response = client.post('/inventory', json=inventory_data)
        assert response.status_code == 201
        data = response.get_json()
        assert data['message'] == 'Inventory updated successfully'
    
    def test_get_forecast_no_data(self, client):
        """Test getting forecast for SKU with no data."""
        response = client.get('/forecast/NONEXISTENT_SKU')
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
    
    def test_get_recommendations_no_data(self, client):
        """Test getting recommendations for SKU with no data."""
        response = client.get('/recommendations/NONEXISTENT_SKU')
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data