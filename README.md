# Campora AI Dashboard

Streamlit analytics dashboard for monitoring the [Campora AI](https://github.com/sunggatalimbetov/campora-ai-helper) Telegram bot. Visualizes query patterns, response quality, latency, and usage from the `bot_interactions` table in Supabase.

## Features

- **KPI Summary** — total interactions, unique users, avg response time, feedback rate
- **Popular Queries** — top 20 most frequent user queries
- **Response Quality** — feedback distribution, trends over time, breakdown by command and language
- **Latency Monitoring** — P50/P95/P99 percentiles, daily averages, distribution histogram
- **Search Hit Rates** — success rates and zero-result query analysis
- **Usage Patterns** — daily interactions, active users, chat types, user languages
- **Filtering** — date range, command, status, and language filters

## Tech Stack

- **Streamlit** — web framework
- **Supabase** — PostgreSQL data source
- **Plotly** — interactive charts
- **pandas** — data processing

## Prerequisites

- Python 3.9+
- Supabase project with the `bot_interactions` table

## Environment Variables

Create a `.env` file in the project root:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
```

## Getting Started

```bash
# Install dependencies
pip install -r requirements.txt

# Run the dashboard
streamlit run app.py
```

## Deployment

Deployed via [Streamlit Community Cloud](https://share.streamlit.io):

1. Push repo to GitHub
2. Connect the repo at [share.streamlit.io](https://share.streamlit.io)
3. Set `app.py` as the entry point
4. Add `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` in the Secrets section
5. Auto-deploys on every push to `main`

## Related Repos

- [campora-ai-helper](https://github.com/sunggatalimbetov/campora-ai-helper) — Telegram bot
- [campora-ai-scrapper](https://github.com/sunggatalimbetov/campora-ai-scrapper) — Telegram group message scraper
