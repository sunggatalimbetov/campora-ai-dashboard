# Campora AI Dashboard

Analytics dashboard for the Campora AI Telegram bot. Visualizes query patterns, feedback, latency, and usage from the `bot_interactions` table in Supabase.

## Local Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file with your Supabase credentials:

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
```

Run the dashboard:

```bash
streamlit run app.py
```

## Deploy to Streamlit Community Cloud

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect the repo
3. Set `app.py` as the entry point
4. Add `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` in the Secrets section
5. The app auto-deploys on every push to `main`
