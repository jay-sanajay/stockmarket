# JayQuant Stock Analyzer

A comprehensive stock market analysis platform with AI-powered insights, technical analysis, and portfolio management tools. Built with FastAPI (Python) backend and React (Vite) frontend, specifically designed for Indian stock markets.

## Features

### Core Analysis
- **AI-Powered Stock Analysis**: Leverages Google Gemini API for intelligent stock recommendations
- **Technical Indicators**: RSI, MACD, Moving Averages, and custom signal scoring
- **News Sentiment Analysis**: Real-time news integration with sentiment scoring
- **Entry/Exit Zones**: AI-generated entry zones, stop-loss levels, and target prices
- **Verdict History**: Track past analysis and recommendations

### Portfolio Management
- **Watchlists**: Create and manage multiple stock watchlists
- **Portfolio Tracking**: Monitor holdings with P&L calculations
- **Price Alerts**: Set custom alerts for price movements
- **Daily Dashboard**: Market overview with cached summaries

### Advanced Strategies
- **Breakout Strategy**: Automated breakout detection with configurable parameters
- **Intraday Scanner**: Real-time scanning for trading opportunities
- **Stock Prediction**: ML-based price prediction engine
- **Backtesting**: Test strategies against historical data

### Core Prediction Features
- **Single Stock Prediction**: Detailed analysis for individual stocks with ML verdicts
- **Batch Analysis**: Compare multiple stocks simultaneously with comparative metrics
- **Market Scanner**: Scan Nifty 50 stocks for high-confidence opportunities
- **Top Picks**: Curated stock selections by category (buy, sell, momentum, value)
- **Multi-Timeframe Support**: 1D, 1W, 1M prediction horizons

### Advanced Analysis
- **Technical Indicators**: RSI, MACD, Bollinger Bands, Moving Averages
- **Momentum Analysis**: Price momentum, volume momentum, trend strength
- **Sentiment Analysis**: Market sentiment indicators and news sentiment
- **Risk Assessment**: Stop-loss levels, target prices, risk/reward ratios
- **Confidence Scoring**: AI-generated confidence levels for each prediction

### User Features
- **Portfolio Management**: Track holdings, performance, and P&L
- **Watchlist Management**: Create and monitor custom stock lists
- **Alerts System**: Set price and technical alerts for monitored stocks
- **Intraday Scanner**: Real-time scanning for intraday trading opportunities
- **Breakout Strategies**: Pre-built trading strategies with backtesting

## 🏗️ Technical Architecture

### Backend Stack
- **Framework**: FastAPI (Python 3.10+)
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: JWT (JSON Web Tokens) with bcrypt password hashing
- **Data Processing**: Pandas, NumPy for data manipulation
- **ML Models**: Custom ensemble prediction engine
- **API Documentation**: Automatic OpenAPI/Swagger documentation

### Frontend Stack
- **Framework**: React 18 with Vite
- **State Management**: React Context API
- **HTTP Client**: Axios for API communication
- **Real-time Updates**: WebSocket integration
- **Styling**: Custom CSS with responsive design
- **Routing**: React Router for navigation

### Data Sources
- **Market Data**: Yahoo Finance API integration
- **Technical Indicators**: Custom calculation engine
- **Sentiment Data**: News and social sentiment analysis
- **Historical Data**: Comprehensive historical price data

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Prediction   │  │ Portfolio    │  │ Watchlist    │      │
│  │ Engine       │  │ Manager      │  │ Manager      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                           ↕ HTTP/WS
┌─────────────────────────────────────────────────────────────┐
│                  Backend (FastAPI)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Prediction   │  │ Auth         │  │ Data         │      │
│  │ Service      │  │ Service      │  │ Service      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ ML Engine    │  │ Technical    │  │ WebSocket    │      │
│  │              │  │ Indicators   │  │ Handler      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                           ↕
┌─────────────────────────────────────────────────────────────┐
│              Database & External Services                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ SQLite DB    │  │ Yahoo Finance│  │ News API     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.10 or higher
- Node.js 18 or higher
- npm or yarn package manager

### Backend Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd stockmarket
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

4. **Initialize database**
```bash
python -c "from database.db_setup import init_db; init_db()"
```

5. **Start the backend server**
```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Backend will be available at: `http://127.0.0.1:8000`

### Frontend Setup

1. **Install Node dependencies**
```bash
npm install
```

2. **Start the development server**
```bash
npm run dev
```

Frontend will be available at: `http://localhost:5173`

### Default Test Credentials
- **Email**: `testuser@example.com`
- **Password**: `test12345`

## 📚 API Documentation

Once the backend is running, access the interactive API documentation at:
- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

### Key API Endpoints

#### Authentication
- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `GET /auth/me` - Get current user info

#### Prediction
- `POST /prediction/predict/{symbol}` - Single stock prediction
- `POST /prediction/predict-batch` - Batch stock analysis
- `GET /prediction/market-scan` - Market scanner
- `GET /prediction/top-picks` - Get curated stock picks

#### Portfolio & Watchlist
- `GET /portfolio/summary` - Portfolio overview
- `POST /portfolio/holdings` - Add/update holdings
- `GET /watchlist/lists` - Get watchlists
- `POST /watchlist/items` - Add stock to watchlist

## 🎨 Usage Guide

### Making Stock Predictions

1. **Login** to the platform using your credentials
2. Navigate to the **Prediction** page
3. **Single Stock Prediction**:
   - Enter stock symbol (e.g., RELIANCE, TCS)
   - Select timeframe (1D, 1W, 1M)
   - Click "Predict Stock" to get analysis

4. **Batch Analysis**:
   - Enter multiple symbols separated by commas
   - Select timeframe
   - Click "Analyze Batch" for comparative analysis

5. **Market Scanner**:
   - Set minimum confidence threshold
   - Optionally filter by verdict type
   - Click "Scan Market" to find opportunities

### Understanding Prediction Results

Each prediction includes:
- **Verdict**: STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL
- **Confidence**: AI confidence score (0-100%)
- **Target Price**: Expected price target
- **Stop Loss**: Recommended stop-loss level
- **Risk/Reward Ratio**: Calculated risk-reward metric
- **Analysis Scores**: Technical, momentum, volume, sentiment scores
- **Key Indicators**: Important technical indicators
- **Risk Factors**: Identified risks
- **Opportunities**: Potential opportunities

## 🔒 Security Features

- **JWT Authentication**: Secure token-based authentication
- **Password Hashing**: bcrypt for secure password storage
- **API Rate Limiting**: Protection against abuse
- **Input Validation**: Comprehensive input sanitization
- **SQL Injection Protection**: ORM-based database operations
- **CORS Configuration**: Proper cross-origin resource sharing

## 🚀 Deployment

### Production Deployment Considerations

1. **Environment Variables**:
   - Set `JWT_SECRET` to a strong random value
   - Configure database connection strings
   - Set up proper CORS origins

2. **Database**:
   - Migrate from SQLite to PostgreSQL for production
   - Set up regular backups
   - Configure connection pooling

3. **Frontend**:
   - Build production bundle: `npm run build`
   - Serve with nginx or similar
   - Enable HTTPS

4. **Backend**:
   - Use production ASGI server (Gunicorn + Uvicorn)
   - Enable HTTPS
   - Set up monitoring and logging

## 🧪 Testing

### Backend Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_prediction.py

# Run with coverage
pytest --cov=.
```

### Frontend Tests
```bash
# Run unit tests
npm test

# Run e2e tests
npm run test:e2e
```

## 📈 Performance Metrics

- **API Response Time**: < 500ms for single predictions
- **Batch Processing**: 50 stocks in < 10 seconds
- **Database Queries**: Optimized with indexing
- **Frontend Load Time**: < 2 seconds initial load
- **Real-time Updates**: WebSocket latency < 100ms

## 🔮 Future Enhancements

- [ ] Deep Learning models for improved accuracy
- [ ] Integration with more data sources (NSE/BSE APIs)
- [ ] Mobile application (React Native)
- [ ] Advanced backtesting framework
- [ ] Social trading features
- [ ] Automated trading integration
- [ ] Multi-language support
- [ ] Advanced charting and visualization

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes with proper tests
4. Submit a pull request with detailed description

## 📄 License

This project is proprietary software. All rights reserved.

## 👨‍💻 Developer Information

**Project Name**: JayQuant - AI Stock Prediction Engine
**Version**: 1.0.0
**Last Updated**: May 2026

## 🎓 Interview Talking Points

### Technical Challenges Solved
1. **Real-time Data Processing**: Implemented efficient WebSocket handling for live market data
2. **ML Model Integration**: Created ensemble prediction engine combining multiple analysis methods
3. **Authentication Flow**: Secure JWT implementation with proper token management
4. **Performance Optimization**: Caching strategies and database query optimization
5. **Error Handling**: Comprehensive error handling and user feedback systems

### Architecture Decisions
1. **FastAPI for Backend**: Chosen for async support, automatic API docs, and performance
2. **React for Frontend**: Component-based architecture, rich ecosystem, and fast development
3. **SQLite for Development**: Easy setup, zero configuration, suitable for MVP
4. **JWT Authentication**: Stateless, scalable, and industry-standard
5. **WebSocket Integration**: Real-time updates without polling overhead

### Key Learnings
1. **Full-Stack Development**: Experience with both frontend and backend technologies
2. **API Design**: RESTful API design with proper documentation
3. **Database Design**: Normalized schema design with proper relationships
4. **Security Best Practices**: Authentication, authorization, and data protection
5. **Performance Optimization**: Caching, indexing, and efficient algorithms

### Project Impact
- Demonstrates ability to build production-ready applications
- Shows understanding of modern web development practices
- Proves capability to integrate complex systems (ML, real-time data, APIs)
- Highlights problem-solving skills and technical decision-making

---

**Built with ❤️ for the Indian Stock Market**
