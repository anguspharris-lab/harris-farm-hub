# 🍎 Harris Farm Hub - AI Centre of Excellence

> **Built this weekend. Launched Monday. Transforming forever.**

The Hub is Harris Farm Markets' centralized AI platform for data analysis, intelligent decision-making, and continuous learning. Built to democratize data access and turn every team member into a data-driven decision maker.

---

## 🎯 What Is The Hub?

The Hub is your **AI-powered command centre** that connects:
- Natural language queries → Your database
- Multiple AI models → Smarter decisions
- Product-level data → Actionable insights
- Your team → Best practices and templates

### Core Capabilities

1. **📊 Interactive Dashboards**
   - Sales Performance (revenue, trends, out-of-stocks)
   - Store Profitability (P&L, margins, optimization)
   - Transport Costs (route efficiency, cost reduction)
   - Product-Level Analytics (wastage, miss-picks, over-ordering)

2. **⚖️ The Rubric (Multi-LLM Evaluation)**
   - Query Claude, ChatGPT, and Grok simultaneously
   - Compare responses side-by-side
   - Make "Chairman's Decision" on best answer
   - System learns from your choices

3. **💬 Natural Language Queries**
   - Ask questions in plain English
   - Automatic SQL generation
   - AI-powered insights and explanations
   - Self-improving from feedback

4. **🔧 Super User Prompt Builder**
   - Design custom analytical queries
   - Product-level issue detection
   - Save and share with teams
   - Schedule automated reports

5. **📚 Prompt Template Library**
   - Pre-built queries by role
   - Retail ops, buying, merchandising, finance
   - Beginner → Advanced levels
   - Community-contributed

6. **🎓 Training Academy** (Coming Week 2)
   - Become a "Prompt Superstar"
   - Interactive lessons
   - Certification pathway
   - Real Harris Farm scenarios

---

## 🚀 Quick Start

### Option 1: Automated Script (Recommended)

```bash
# Make scripts executable
chmod +x start.sh stop.sh

# Start all services
./start.sh

# Access dashboards:
# - Sales: http://localhost:8501
# - Profitability: http://localhost:8502
# - Transport: http://localhost:8503
# - Prompt Builder: http://localhost:8504
# - API: http://localhost:8000

# When done
./stop.sh
```

### Option 2: Docker

```bash
# Create .env file first (see DEPLOYMENT_GUIDE.md)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Option 3: Manual

```bash
# Install dependencies
pip install -r requirements.txt --break-system-packages

# Start API
cd backend && python app.py &

# Start dashboards (in separate terminals)
cd dashboards
streamlit run sales_dashboard.py --server.port 8501 &
streamlit run profitability_dashboard.py --server.port 8502 &
streamlit run transport_dashboard.py --server.port 8503 &
streamlit run prompt_builder.py --server.port 8504 &
```

---

## 📁 Project Structure

```
harris-farm-hub/
│
├── backend/
│   ├── app.py                 # FastAPI server with all endpoints
│   └── hub_data.db           # SQLite for Hub metadata
│
├── dashboards/
│   ├── sales_dashboard.py        # Sales + product-level analytics
│   ├── profitability_dashboard.py # Store P&L analysis
│   ├── transport_dashboard.py     # Logistics optimization
│   └── prompt_builder.py          # Super user custom query tool
│
├── frontend/                  # React app (optional)
│   ├── src/
│   └── package.json
│
├── docs/
│   ├── DEPLOYMENT_GUIDE.md   # Complete deployment instructions
│   └── USER_GUIDE.md         # End-user documentation
│
├── config/
│   └── .env.template         # Environment variables template
│
├── requirements.txt          # Python dependencies
├── docker-compose.yml        # Container orchestration
├── start.sh                  # Quick start script
├── stop.sh                   # Stop all services
└── README.md                 # This file
```

---

## 🔧 Configuration

### Required: API Keys

Get API keys from:
- **Anthropic (Claude)**: https://console.anthropic.com/
- **OpenAI (ChatGPT)**: https://platform.openai.com/
- **xAI (Grok)**: https://x.ai/api (optional)

### Required: Database Connection

Configure Harris Farm's database in `.env`:

```bash
DB_TYPE=postgresql  # or sqlserver
DB_HOST=your-database-host
DB_PORT=5432
DB_NAME=harris_farm
DB_USER=readonly_user  # Use read-only for safety
DB_PASSWORD=your_secure_password
```

### Environment Variables

Copy `.env.template` to `.env` and fill in:

```bash
# API Keys
ANTHROPIC_API_KEY=sk-ant-xxxxx
OPENAI_API_KEY=sk-xxxxx
GROK_API_KEY=xai-xxxxx

# Database
DB_TYPE=postgresql
DB_HOST=db.harrisfarm.internal
DB_PORT=5432
DB_NAME=harris_farm_prod
DB_USER=hub_readonly
DB_PASSWORD=xxxxx

# App Settings
API_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
```

---

## 💡 Use Cases

### For Finance Team (Primary Users)

**Daily Tasks:**
- Check store profitability trends
- Analyze transport cost patterns
- Query sales data with natural language
- Identify cost reduction opportunities

**Key Queries:**
```
"Which stores had margin below 5% last month?"
"Show me transport costs for Eastern Suburbs routes"
"Compare this week's revenue to last week by category"
"What's our total wastage cost across all fresh produce?"
```

### For Buyers

**Product-Level Analytics:**
- Out-of-stock tracking and lost sales
- Over-ordering detection
- Wastage patterns by product/store
- Supplier performance

**Custom Prompts:**
- "Show products consistently ordered 15% above sales"
- "Which items had wastage above 20% at any store?"
- "Alert me to products out of stock for 4+ hours"

### For Operations

**Store Performance:**
- Online miss-pick analysis
- Inventory velocity tracking
- Store comparison benchmarks
- Best practice identification

**Automated Reports:**
- Daily out-of-stock summary
- Weekend wastage report
- Weekly performance scorecard

### For Leadership (Gus, Angela)

**Strategic Decisions:**
- Use The Rubric for major decisions
- Compare AI model recommendations
- Track KPIs across all functions
- Identify systemic issues

---

## 🎓 Becoming a Prompt Superstar

### Level 1: Prompt Apprentice
- Learn basic query structure
- Use template library
- Ask clear questions
- Understand results

### Level 2: Prompt Specialist
- Design custom prompts
- Use Super User Prompt Builder
- Apply filters and thresholds
- Share prompts with team

### Level 3: Prompt Master
- Create complex multi-step queries
- Optimize for performance
- Train others
- Contribute to library

---

## 🔐 Security & Access

### Day 1 (MVP)
- ✅ Read-only database access
- ✅ Internal network only
- ✅ Basic authentication
- ✅ Environment variable secrets

### Production (Week 2+)
- [ ] Azure AD / SSO integration
- [ ] Role-based access control
- [ ] Audit logging
- [ ] HTTPS/TLS everywhere
- [ ] API rate limiting
- [ ] Data masking for sensitive fields

---

## 📊 Success Metrics

Track Hub effectiveness:

### Usage Metrics
- Queries per day
- Active users
- Dashboard views
- Rubric evaluations

### Quality Metrics
- Query success rate
- Average user rating (1-5 stars)
- Response accuracy
- Time saved vs manual

### Business Impact
- Cost savings identified
- Issues caught early
- Decisions informed by data
- Process improvements

### Learning Metrics
- Chairman decisions logged
- Popular templates
- Self-improvement rate
- User progression (Apprentice→Master)

---

## 🐛 Troubleshooting

### Common Issues

**API won't start**
```bash
# Check if port 8000 is in use
lsof -i :8000

# Try different port
uvicorn app:app --port 8001
```

**Dashboard shows "Connection Error"**
```bash
# Verify API is running
curl http://localhost:8000

# Check API_URL in dashboard
# Should match backend port
```

**Database connection failed**
```bash
# Test connection manually
psql -h $DB_HOST -U $DB_USER -d $DB_NAME

# Verify credentials in .env
# Try read-only user first
```

**Slow performance**
```bash
# Add database indexes
# Implement result caching
# Limit query result sizes
```

### Getting Help

- **Email**: hub-support@harrisfarm.com
- **Slack**: #harris-farm-hub
- **Documentation**: See `/docs` folder
- **GitHub Issues**: Report bugs and request features

---

## 🛣️ Roadmap

### ✅ Phase 1: Weekend MVP (Completed)
- Natural language queries
- Three core dashboards
- The Rubric (multi-LLM)
- Prompt library basics
- Super User Prompt Builder
- Product-level analytics

### 📅 Phase 2: Week 2-3
- Full training academy
- Scheduled reports
- Email/Slack notifications
- Advanced visualizations
- Mobile optimization
- Prompt sharing workflow

### 📅 Phase 3: Month 2
- Predictive analytics
- Real-time alerts
- Voice interface (buyers at markets)
- Supplier portal
- Advanced ML models
- Multi-user collaboration

### 📅 Phase 4: Month 3+
- Autonomous AI agents
- Dynamic pricing engine
- Demand forecasting
- Supply chain optimization
- Customer sentiment analysis
- Competitive intelligence

---

## 🤝 Contributing

### For Harris Farm Team

**Adding Prompt Templates:**
1. Design prompt in Prompt Builder
2. Test with real data
3. Save with clear name and description
4. Share with relevant teams

**Improving The Hub:**
1. Submit feedback via star ratings
2. Report issues in Slack
3. Suggest features
4. Share success stories

**Becoming a Super User:**
1. Complete training modules
2. Build 5+ custom prompts
3. Help train colleagues
4. Get certified

---

## 📜 License

Proprietary - Harris Farm Markets Internal Use Only

---

## 🙏 Acknowledgments

Built with:
- **FastAPI** - Modern Python web framework
- **Streamlit** - Rapid dashboard development
- **Claude (Anthropic)** - Advanced AI capabilities
- **Plotly** - Interactive visualizations
- **React** - Modern frontend framework

Special thanks to:
- **Finance Team** - Pilot users and feedback
- **Gus** - Vision and leadership
- **The Hub Team** - Weekend warriors

---

## 📞 Contact

**Project Lead**: Gus (Co-CEO)
**Technical Support**: hub-support@harrisfarm.com
**Slack Channel**: #harris-farm-hub

---

**Built with ❤️ for Harris Farm Markets**

*Transforming data into decisions, one query at a time.*

---

## Quick Reference

```bash
# Start The Hub
./start.sh

# Check status
curl http://localhost:8000

# View logs
tail -f logs/*.log

# Stop The Hub
./stop.sh

# Access dashboards
open http://localhost:8501  # Sales
open http://localhost:8502  # Profitability
open http://localhost:8503  # Transport
open http://localhost:8504  # Prompt Builder
```

**Ready to launch? Run `./start.sh` and open your browser! 🚀**
