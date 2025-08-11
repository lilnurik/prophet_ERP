import os
import pickle
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from prophet import Prophet
from sqlalchemy import func
from typing import Optional, Dict, List, Tuple
import logging

from app.models import Sales, Inventory
from app.database import db

logger = logging.getLogger(__name__)

class ForecastingService:
    def __init__(self, models_dir: str = "models"):
        self.models_dir = models_dir
        os.makedirs(models_dir, exist_ok=True)
    
    def _get_model_path(self, sku: str) -> str:
        """Get the file path for a SKU's model."""
        return os.path.join(self.models_dir, f"{sku}_prophet_model.pkl")
    
    def _prepare_data(self, sku: str) -> Optional[pd.DataFrame]:
        """Prepare sales data for Prophet training."""
        try:
            # Query sales data for the SKU
            sales_data = db.session.query(Sales).filter(Sales.sku == sku).all()
            
            if not sales_data:
                logger.warning(f"No sales data found for SKU: {sku}")
                return None
            
            # Convert to DataFrame
            data = []
            for sale in sales_data:
                data.append({
                    'ds': sale.date,
                    'y': sale.quantity
                })
            
            df = pd.DataFrame(data)
            
            # Aggregate by date (sum quantities for same date)
            df = df.groupby('ds')['y'].sum().reset_index()
            
            # Sort by date
            df = df.sort_values('ds').reset_index(drop=True)
            
            logger.info(f"Prepared {len(df)} data points for SKU: {sku}")
            return df
            
        except Exception as e:
            logger.error(f"Error preparing data for SKU {sku}: {str(e)}")
            return None
    
    def train_model(self, sku: str) -> bool:
        """Train a Prophet model for the given SKU."""
        try:
            df = self._prepare_data(sku)
            if df is None or len(df) < 2:
                logger.warning(f"Insufficient data to train model for SKU: {sku}")
                return False
            
            # Initialize and train Prophet model
            model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=False,
                changepoint_prior_scale=0.05
            )
            
            model.fit(df)
            
            # Save the model
            self.save_model(sku, model)
            
            logger.info(f"Successfully trained model for SKU: {sku}")
            return True
            
        except Exception as e:
            logger.error(f"Error training model for SKU {sku}: {str(e)}")
            return False
    
    def save_model(self, sku: str, model: Prophet) -> None:
        """Save a trained Prophet model to disk."""
        try:
            model_path = self._get_model_path(sku)
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
            logger.info(f"Model saved for SKU: {sku}")
        except Exception as e:
            logger.error(f"Error saving model for SKU {sku}: {str(e)}")
            raise
    
    def load_model(self, sku: str) -> Optional[Prophet]:
        """Load a trained Prophet model from disk."""
        try:
            model_path = self._get_model_path(sku)
            if not os.path.exists(model_path):
                logger.warning(f"Model file not found for SKU: {sku}")
                return None
            
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            
            logger.info(f"Model loaded for SKU: {sku}")
            return model
            
        except Exception as e:
            logger.error(f"Error loading model for SKU {sku}: {str(e)}")
            return None
    
    def forecast(self, sku: str, days_ahead: int = 30) -> Optional[Dict]:
        """Generate forecast for the given SKU."""
        try:
            # Try to load existing model
            model = self.load_model(sku)
            
            # If no model exists, train one
            if model is None:
                logger.info(f"No existing model for SKU {sku}, training new model...")
                if not self.train_model(sku):
                    return None
                model = self.load_model(sku)
                
            if model is None:
                return None
            
            # Create future dates
            future = model.make_future_dataframe(periods=days_ahead)
            
            # Generate forecast
            forecast = model.predict(future)
            
            # Prepare response data
            forecast_data = []
            chart_data = {
                'dates': [],
                'forecast': [],
                'lower_bound': [],
                'upper_bound': []
            }
            
            # Get only future predictions
            future_forecast = forecast.tail(days_ahead)
            
            for _, row in future_forecast.iterrows():
                forecast_data.append({
                    'date': row['ds'].strftime('%Y-%m-%d'),
                    'forecast': max(0, row['yhat']),  # Ensure non-negative
                    'lower_bound': max(0, row['yhat_lower']),
                    'upper_bound': max(0, row['yhat_upper'])
                })
                
                chart_data['dates'].append(row['ds'].strftime('%Y-%m-%d'))
                chart_data['forecast'].append(max(0, row['yhat']))
                chart_data['lower_bound'].append(max(0, row['yhat_lower']))
                chart_data['upper_bound'].append(max(0, row['yhat_upper']))
            
            return {
                'sku': sku,
                'forecast_data': forecast_data,
                'chart_data': chart_data,
                'days_ahead': days_ahead
            }
            
        except Exception as e:
            logger.error(f"Error generating forecast for SKU {sku}: {str(e)}")
            return None
    
    def _get_current_stock(self, sku: str) -> float:
        """Get current stock level for a SKU."""
        try:
            latest_inventory = db.session.query(Inventory).filter(
                Inventory.sku == sku
            ).order_by(Inventory.date.desc()).first()
            
            return latest_inventory.quantity if latest_inventory else 0.0
        except Exception as e:
            logger.error(f"Error getting current stock for SKU {sku}: {str(e)}")
            return 0.0
    
    def _calculate_safety_stock(self, sku: str, lead_time_days: int = 7) -> float:
        """Calculate safety stock using historical demand variability."""
        try:
            # Get historical sales data
            sales_data = db.session.query(Sales).filter(Sales.sku == sku).all()
            
            if len(sales_data) < 10:  # Need sufficient data
                return 0.0
            
            # Calculate daily demand variability
            daily_demands = [sale.quantity for sale in sales_data]
            demand_std = np.std(daily_demands)
            avg_demand = np.mean(daily_demands)
            
            # Safety stock = Z-score * std_dev * sqrt(lead_time)
            # Using Z-score of 1.65 for 95% service level
            safety_stock = 1.65 * demand_std * np.sqrt(lead_time_days)
            
            return max(0, safety_stock)
            
        except Exception as e:
            logger.error(f"Error calculating safety stock for SKU {sku}: {str(e)}")
            return 0.0
    
    def recommend_production(self, sku: str, days_ahead: int = 30) -> Optional[Dict]:
        """Calculate recommended production quantity based on forecast and current stock."""
        try:
            # Get forecast
            forecast_result = self.forecast(sku, days_ahead)
            if not forecast_result:
                return {
                    'sku': sku,
                    'recommended_quantity': 0.0,
                    'current_stock': None,
                    'forecasted_demand': None,
                    'safety_stock': None,
                    'reasoning': 'Unable to generate forecast'
                }
            
            # Get current stock
            current_stock = self._get_current_stock(sku)
            
            # Calculate total forecasted demand
            total_forecasted_demand = sum([
                item['forecast'] for item in forecast_result['forecast_data']
            ])
            
            # Calculate safety stock
            safety_stock = self._calculate_safety_stock(sku)
            
            # Calculate recommended production
            # Production = Forecasted Demand + Safety Stock - Current Stock
            recommended_quantity = max(0, total_forecasted_demand + safety_stock - current_stock)
            
            reasoning = f"Based on {days_ahead}-day forecast of {total_forecasted_demand:.2f} units, "
            reasoning += f"current stock of {current_stock:.2f} units, "
            reasoning += f"and safety stock of {safety_stock:.2f} units."
            
            return {
                'sku': sku,
                'recommended_quantity': round(recommended_quantity, 2),
                'current_stock': current_stock,
                'forecasted_demand': round(total_forecasted_demand, 2),
                'safety_stock': round(safety_stock, 2),
                'reasoning': reasoning
            }
            
        except Exception as e:
            logger.error(f"Error calculating production recommendation for SKU {sku}: {str(e)}")
            return None