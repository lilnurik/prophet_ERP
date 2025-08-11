# Prophet ERP - AI-Powered Backend Application

An AI-powered backend application built with Flask that provides demand forecasting and production recommendations using Facebook Prophet.

## Features

- **Sales, Production, and Inventory Management**: Store and track business data in PostgreSQL
- **AI-Powered Forecasting**: Uses Facebook Prophet to predict demand for each SKU
- **Production Recommendations**: Calculates optimal production quantities using EOQ and safety stock formulas
- **RESTful API**: Clean JSON API endpoints for all operations
- **Docker Support**: Complete containerization with docker-compose

## Tech Stack

- **Backend**: Flask with SQLAlchemy ORM
- **Database**: PostgreSQL
- **AI/ML**: Facebook Prophet, pandas, numpy, scikit-learn
- **Validation**: Pydantic
- **Deployment**: Docker & docker-compose
- **Testing**: pytest

## Project Structure

```
prophet_ERP/
├── app/
│   ├── main.py              # Application factory and entry point
│   ├── config.py            # Configuration settings
│   ├── database.py          # Database initialization
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic validation schemas
│   ├── routes/
│   │   └── __init__.py      # API route definitions
│   └── services/
│       └── forecasting.py   # Prophet forecasting service
├── models/                  # Stored Prophet models (one per SKU)
├── sample_data/            # Sample CSV data for testing
├── tests/                  # Unit tests
├── Dockerfile              # Container definition
├── docker-compose.yml      # Multi-service deployment
├── requirements.txt        # Python dependencies
└── init_db.py             # Database initialization script
```

## Installation

### Option 1: Docker (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd prophet_ERP
```

2. Start the services:
```bash
docker-compose up -d
```

3. The API will be available at `http://localhost:5000`

### Option 2: Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up PostgreSQL database and update environment variables:
```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/prophet_erp"
export SECRET_KEY="your-secret-key"
```

3. Initialize the database:
```bash
python init_db.py
```

4. Run the application:
```bash
python app/main.py
```

## API Endpoints

### Data Input

#### Add Sales Record
```bash
curl -X POST http://localhost:5000/sales \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "PROD001",
    "date": "2024-01-01",
    "quantity": 50
  }'
```

#### Add Production Record
```bash
curl -X POST http://localhost:5000/production \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "PROD001",
    "date": "2024-01-01",
    "quantity": 100
  }'
```

#### Update Inventory
```bash
curl -X POST http://localhost:5000/inventory \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "PROD001",
    "date": "2024-01-01",
    "quantity": 150
  }'
```

### Forecasting & Recommendations

#### Get Demand Forecast
```bash
curl "http://localhost:5000/forecast/PROD001?days_ahead=30"
```

Response includes:
- Raw predictions with confidence intervals
- Chart-ready data arrays
- Forecast period information

#### Get Production Recommendations
```bash
curl "http://localhost:5000/recommendations/PROD001?days_ahead=30"
```

Response includes:
- Recommended production quantity
- Current stock levels
- Forecasted demand
- Safety stock calculation
- Reasoning explanation

#### Health Check
```bash
curl http://localhost:5000/status
```

## Loading Sample Data

Load the provided sample data for testing:

```python
import pandas as pd
import requests

# Load sales data
sales_df = pd.read_csv('sample_data/sales_data.csv')
for _, row in sales_df.iterrows():
    response = requests.post('http://localhost:5000/sales', json={
        'sku': row['sku'],
        'date': row['date'],
        'quantity': row['quantity']
    })

# Load inventory data
inventory_df = pd.read_csv('sample_data/inventory_data.csv')
for _, row in inventory_df.iterrows():
    response = requests.post('http://localhost:5000/inventory', json={
        'sku': row['sku'],
        'date': row['date'],
        'quantity': row['quantity']
    })
```

## How to Retrain Models

Models are automatically trained when:
1. A forecast is requested for a SKU with no existing model
2. You can manually trigger retraining by deleting the model file in `/models/{sku}_prophet_model.pkl`

Models are stored in the `models/` directory with the naming convention: `{SKU}_prophet_model.pkl`

## AI Forecasting Details

The forecasting module (`app/services/forecasting.py`) implements:

- **Prophet Model Training**: Automatically trains time series models on historical sales data
- **Model Persistence**: Saves/loads trained models to reduce computation time
- **Demand Forecasting**: Predicts future demand with confidence intervals
- **Safety Stock Calculation**: Uses historical demand variability to calculate safety stock
- **Production Recommendations**: Combines forecast, current stock, and safety stock to recommend production quantities

### Forecasting Algorithm

1. **Data Preparation**: Aggregates sales data by date for each SKU
2. **Model Training**: Uses Facebook Prophet with yearly and weekly seasonality
3. **Prediction**: Generates forecasts for specified time horizon
4. **Safety Stock**: Calculates using Z-score (95% service level) and demand variability
5. **Production Recommendation**: `Forecasted Demand + Safety Stock - Current Stock`

## Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-flask

# Run tests
pytest tests/ -v
```

Tests cover:
- Forecasting service functionality
- API endpoint validation
- Data model operations
- Error handling scenarios

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: Flask secret key for session management

## Troubleshooting

### Common Issues

1. **Database Connection Error**: Ensure PostgreSQL is running and connection details are correct
2. **Prophet Installation Issues**: May require additional system dependencies on some platforms
3. **Model Training Failures**: Ensure sufficient historical data (minimum 2 data points, recommended 30+)

### Logs

Application logs include:
- Model training status
- API request/response details
- Error messages with stack traces

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

[Add your license information here]