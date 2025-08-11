from flask import Blueprint, request, jsonify
from datetime import datetime
import logging

from app.models import Sales, Production, Inventory
from app.database import db
from app.schemas import SalesRequest, ProductionRequest, InventoryRequest

logger = logging.getLogger(__name__)

# Create blueprints
data_bp = Blueprint('data', __name__)
forecast_bp = Blueprint('forecast', __name__)
main_bp = Blueprint('main', __name__)

# Initialize forecasting service - will be imported when needed
forecasting_service = None

def get_forecasting_service():
    """Lazy import forecasting service to avoid dependency issues."""
    global forecasting_service
    if forecasting_service is None:
        try:
            from app.services.forecasting import ForecastingService
            forecasting_service = ForecastingService()
        except ImportError as e:
            logger.error(f"Failed to import forecasting service: {e}")
            return None
    return forecasting_service

@data_bp.route('/sales', methods=['POST'])
def add_sales():
    """Add a new sales record."""
    try:
        data = request.get_json()
        
        # Validate data
        try:
            sales_request = SalesRequest(**data)
        except Exception as e:
            return jsonify({'error': f'Validation error: {str(e)}'}), 400
        
        # Create new sales record
        sales_record = Sales(
            sku=sales_request.sku,
            date=sales_request.date,
            quantity=sales_request.quantity
        )
        
        db.session.add(sales_record)
        db.session.commit()
        
        logger.info(f"Added sales record: SKU={sales_request.sku}, qty={sales_request.quantity}")
        
        return jsonify({
            'message': 'Sales record added successfully',
            'data': sales_record.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding sales record: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@data_bp.route('/production', methods=['POST'])
def add_production():
    """Add a new production record."""
    try:
        data = request.get_json()
        
        # Validate data
        try:
            production_request = ProductionRequest(**data)
        except Exception as e:
            return jsonify({'error': f'Validation error: {str(e)}'}), 400
        
        # Create new production record
        production_record = Production(
            sku=production_request.sku,
            date=production_request.date,
            quantity=production_request.quantity
        )
        
        db.session.add(production_record)
        db.session.commit()
        
        logger.info(f"Added production record: SKU={production_request.sku}, qty={production_request.quantity}")
        
        return jsonify({
            'message': 'Production record added successfully',
            'data': production_record.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding production record: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@data_bp.route('/inventory', methods=['POST'])
def update_inventory():
    """Update inventory stock."""
    try:
        data = request.get_json()
        
        # Validate data
        try:
            inventory_request = InventoryRequest(**data)
        except Exception as e:
            return jsonify({'error': f'Validation error: {str(e)}'}), 400
        
        # Create new inventory record
        inventory_record = Inventory(
            sku=inventory_request.sku,
            date=inventory_request.date,
            quantity=inventory_request.quantity
        )
        
        db.session.add(inventory_record)
        db.session.commit()
        
        logger.info(f"Updated inventory: SKU={inventory_request.sku}, qty={inventory_request.quantity}")
        
        return jsonify({
            'message': 'Inventory updated successfully',
            'data': inventory_record.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating inventory: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@forecast_bp.route('/forecast/<string:sku>', methods=['GET'])
def get_forecast(sku):
    """Get forecast for a specific SKU."""
    try:
        forecasting_service = get_forecasting_service()
        if forecasting_service is None:
            return jsonify({
                'error': 'Forecasting service not available',
                'message': 'Prophet dependencies not installed'
            }), 503
        
        # Get days_ahead parameter (default: 30)
        days_ahead = request.args.get('days_ahead', 30, type=int)
        
        if days_ahead <= 0 or days_ahead > 365:
            return jsonify({'error': 'days_ahead must be between 1 and 365'}), 400
        
        # Generate forecast
        forecast_result = forecasting_service.forecast(sku, days_ahead)
        
        if forecast_result is None:
            return jsonify({
                'error': f'Unable to generate forecast for SKU: {sku}',
                'message': 'Insufficient data or model training failed'
            }), 404
        
        logger.info(f"Generated forecast for SKU={sku}, days_ahead={days_ahead}")
        
        return jsonify(forecast_result), 200
        
    except Exception as e:
        logger.error(f"Error generating forecast for SKU {sku}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@forecast_bp.route('/recommendations/<string:sku>', methods=['GET'])
def get_recommendations(sku):
    """Get production recommendations for a specific SKU."""
    try:
        forecasting_service = get_forecasting_service()
        if forecasting_service is None:
            return jsonify({
                'error': 'Forecasting service not available',
                'message': 'Prophet dependencies not installed'
            }), 503
        
        # Get days_ahead parameter (default: 30)
        days_ahead = request.args.get('days_ahead', 30, type=int)
        
        if days_ahead <= 0 or days_ahead > 365:
            return jsonify({'error': 'days_ahead must be between 1 and 365'}), 400
        
        # Generate recommendations
        recommendation_result = forecasting_service.recommend_production(sku, days_ahead)
        
        if recommendation_result is None:
            return jsonify({
                'error': f'Unable to generate recommendations for SKU: {sku}',
                'message': 'Insufficient data or model training failed'
            }), 404
        
        logger.info(f"Generated recommendations for SKU={sku}")
        
        return jsonify(recommendation_result), 200
        
    except Exception as e:
        logger.error(f"Error generating recommendations for SKU {sku}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@main_bp.route('/status', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        # Simple database connectivity check
        db.session.execute('SELECT 1')
        
        return jsonify({
            'status': 'healthy',
            'message': 'Service is running and database is accessible',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'message': 'Database connection failed',
            'timestamp': datetime.utcnow().isoformat()
        }), 503