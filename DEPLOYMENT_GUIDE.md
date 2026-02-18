# Harris Farm Hub - Weekend Build & Deployment Guide

## 🎯 What We're Building

**The Hub**: AI Centre of Excellence for Harris Farm Markets
- Natural language database queries
- Multi-LLM evaluation system ("The Rubric")
- Interactive dashboards (Sales, Profitability, Transport, Product-level)
- Super User Prompt Builder for custom analytics
- Prompt template library
- Self-improvement feedback system

**Launch Target**: Monday morning demo to finance team

---

## 📋 Weekend Timeline

### SATURDAY

#### Morning (4 hours)
- **08:00-09:00**: Environment setup
  - Install dependencies
  - Configure database connections
  - Set up API keys (Anthropic, OpenAI, optionally xAI)
  
- **09:00-11:00**: Backend deployment
  - Deploy FastAPI server
  - Initialize Hub database
  - Test API endpoints
  
- **11:00-12:00**: Dashboard deployment
  - Deploy Streamlit dashboards
  - Test with mock data
  - Verify all visualizations render

#### Afternoon (4 hours)
- **13:00-15:00**: Database integration
  - Connect to Harris Farm's actual database
  - Map schema to query generator
  - Test real queries
  
- **15:00-17:00**: Frontend polish
  - Deploy React app (optional for MVP)
  - Test rubric evaluation
  - Verify prompt library loads

### SUNDAY

#### Morning (4 hours)
- **08:00-10:00**: Product-level analytics
  - Add OOS tracking
  - Add wastage detection
  - Add over-ordering analysis
  - Add miss-pick reporting
  
- **10:00-12:00**: Super User Prompt Builder
  - Deploy prompt builder interface
  - Load example prompts
  - Test save/load functionality

#### Afternoon (4 hours)
- **13:00-15:00**: Integration testing
  - End-to-end workflow testing
  - Performance optimization
  - Bug fixes
  
- **15:00-17:00**: Documentation & training
  - User guides
  - Quick start videos
  - Prepare Monday demo

---

## 🛠️ Technical Setup

### Prerequisites

```bash
# Python 3.10+
python --version

# Node.js 18+ (for React frontend - optional for MVP)
node --version

# PostgreSQL/SQL Server client (depending on Harris Farm's DB)
```

### Installation

```bash
# 1. Clone/download the Hub files
cd harris-farm-hub

# 2. Install Python dependencies
pip install fastapi uvicorn anthropic openai httpx sqlalchemy psycopg2-binary pandas streamlit plotly --break-system-packages

# 3. Install React dependencies (optional)
cd frontend
npm install
```

### Configuration

Create `.env` file:

```bash
# API Keys
ANTHROPIC_API_KEY=your_claude_key_here
OPENAI_API_KEY=your_openai_key_here
GROK_API_KEY=your_grok_key_here  # Optional

# Database (configure for Harris Farm's actual DB)
DB_TYPE=postgresql  # or sqlserver
DB_HOST=your-db-host.com
DB_PORT=5432
DB_NAME=harris_farm
DB_USER=readonly_user  # Use read-only for safety
DB_PASSWORD=your_password

# App Settings
API_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
```

---

## 🚀 Deployment

### Option 1: Quick Local Setup (Recommended for Weekend MVP)

```bash
# Terminal 1: Start Backend API
cd backend
python app.py
# Runs on http://localhost:8000

# Terminal 2: Start Sales Dashboard
cd dashboards
streamlit run sales_dashboard.py --server.port 8501

# Terminal 3: Start Profitability Dashboard
streamlit run profitability_dashboard.py --server.port 8502

# Terminal 4: Start Transport Dashboard
streamlit run transport_dashboard.py --server.port 8503

# Terminal 5: Start Prompt Builder
streamlit run prompt_builder.py --server.port 8504

# Optional Terminal 6: Start React Frontend
cd frontend
npm start
# Runs on http://localhost:3000
```

### Option 2: Docker Deployment (Production-Ready)

```bash
# Build and run all services
docker-compose up -d

# Services will be available at:
# - API: http://localhost:8000
# - Dashboards: http://localhost:8501-8504
# - Frontend: http://localhost:3000
```

### Option 3: Cloud Deployment (Week 2+)

**Backend**: Railway, Render, or AWS Lambda
**Dashboards**: Streamlit Community Cloud or internal server
**Frontend**: Vercel or Netlify
**Database**: Use existing Harris Farm infrastructure

---

## 📊 What Finance Team Gets Monday Morning

### 1. **Live Dashboards** (Accessible via Browser)

- **Sales Performance**: http://your-server:8501
  - Revenue trends by store, category, day
  - Product-level out-of-stock tracking
  - Online miss-pick analysis
  - Natural language query interface
  
- **Store Profitability**: http://your-server:8502
  - P&L by store
  - Margin analysis
  - Waterfall profitability breakdown
  - Transport cost impact simulation
  
- **Transport Costs**: http://your-server:8503
  - Route efficiency analysis
  - Cost breakdown (fuel, labor, vehicle)
  - 15% reduction scenario modeling
  - Consolidation opportunities
  
- **Prompt Builder**: http://your-server:8504
  - Custom query designer
  - Product-level analytics tools
  - Over-ordering detection
  - Wastage analysis
  - Saved prompt library

### 2. **The Rubric** (Multi-LLM Evaluation)

Access via main Hub interface or API:
```bash
curl -X POST http://localhost:8000/api/rubric \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What are the top 3 cost reduction opportunities?",
    "context": "Harris Farm Markets retail operations",
    "providers": ["claude", "chatgpt"]
  }'
```

### 3. **Natural Language Queries**

Finance team can ask questions like:
- "Which products had wastage above 15% last week?"
- "Show me out-of-stocks at Bondi store yesterday"
- "Compare profitability across stores this month"
- "What are our highest transport cost routes?"

---

## 🎓 Training Plan (Monday Launch)

### 15-Minute Demo (For Gus & Leadership)

1. **Dashboard Tour** (5 min)
   - Quick overview of each dashboard
   - Show real data in action
   
2. **Natural Language Demo** (5 min)
   - Ask 3-4 business questions
   - Show SQL generation
   - Highlight insights
   
3. **The Rubric** (3 min)
   - Submit strategic question
   - Compare AI responses
   - Make chairman's decision
   
4. **Prompt Builder** (2 min)
   - Show super user capabilities
   - Load example prompt
   - Demonstrate customization

### 30-Minute Finance Team Workshop

1. **Getting Started** (10 min)
   - How to access dashboards
   - Navigation basics
   - Saving favorite queries
   
2. **Hands-On Practice** (15 min)
   - Each person asks 2-3 questions
   - Interpret results together
   - Tips for better prompts
   
3. **Super User Path** (5 min)
   - Who can build custom prompts
   - Example use cases
   - How to request new features

---

## 🔐 Security Considerations

### Day 1 (MVP)
- Read-only database access
- Internal network only
- Basic auth on dashboards
- API keys in environment variables

### Week 2+ (Production)
- Azure AD / SSO integration
- Role-based access control
- Audit logging
- HTTPS everywhere
- Rate limiting on API

---

## 📈 Success Metrics (First Week)

Track these to demonstrate Hub value:

1. **Usage**
   - Number of queries run
   - Active users per day
   - Most popular dashboards
   
2. **Quality**
   - Query success rate
   - Average user rating
   - Time saved vs manual analysis
   
3. **Business Impact**
   - Cost savings identified
   - Issues caught early (OOS, wastage)
   - Decisions informed by Hub data
   
4. **Learning**
   - Chairman decisions in rubric
   - Popular prompt templates
   - Self-improvement insights

---

## 🐛 Troubleshooting

### Common Issues

**"API key not configured"**
- Check `.env` file exists
- Verify API keys are valid
- Restart backend server

**"Database connection failed"**
- Verify DB credentials
- Check network access
- Try read-only user first

**"Streamlit won't start"**
- Check port not in use: `lsof -i :8501`
- Try different port: `streamlit run app.py --server.port 8505`

**"Slow query performance"**
- Add database indexes
- Implement query caching
- Limit result sets

**"Out of memory"**
- Reduce concurrent dashboard instances
- Implement result pagination
- Add query result limits

---

## 🚀 Week 2+ Roadmap

### Phase 2 Features (Week 2-3)
- Full prompt training academy
- Advanced analytics (predictive models)
- Custom dashboard builder
- Slack/Email notifications
- Scheduled reports
- Mobile-optimized views

### Phase 3 Features (Month 2)
- Voice interface for buyers
- Real-time alerts (OOS, wastage)
- Supplier portal integration
- Advanced ML models
- Multi-user collaboration
- API for third-party tools

### Phase 4 Features (Month 3+)
- Autonomous agents
- Dynamic pricing recommendations
- Demand forecasting
- Supply chain optimization
- Customer sentiment analysis
- Competitive intelligence

---

## 📞 Support

**For Technical Issues**:
- Hub Team: hub-support@harrisfarm.com
- Slack: #harris-farm-hub

**For Business Questions**:
- Gus (Co-CEO)
- Angela (CFO)
- Finance Team Leads

---

## ✅ Pre-Launch Checklist

### Saturday Night
- [ ] Backend API running and tested
- [ ] All dashboards load with mock data
- [ ] Database connection configured
- [ ] API keys set up
- [ ] Basic authentication working

### Sunday Night
- [ ] Real data flowing through dashboards
- [ ] Product-level analytics working
- [ ] Prompt builder functional
- [ ] The Rubric evaluating correctly
- [ ] Documentation complete
- [ ] Demo script prepared
- [ ] Backup plan ready

### Monday Morning
- [ ] All services started
- [ ] Finance team access tested
- [ ] Demo environment ready
- [ ] Support team briefed
- [ ] Feedback mechanism active

---

**Built with ❤️ for Harris Farm Markets**
**AI Centre of Excellence | February 2026**
