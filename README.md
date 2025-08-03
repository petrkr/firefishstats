# FirefishStats

Flask web application for analyzing investment account statistics from Creditas bank transaction data.

## Features

- 📊 Investment tracking and profit calculation
- 🔄 Real-time data refresh from Creditas API
- 💰 Automatic categorization of deposits, withdrawals, and investments
- 📈 Investment matching with returns based on remittance info
- 🇨🇿 Czech language interface

## Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd firefishstats
   ```

2. **Create virtual environment and install dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your actual credentials
   ```

4. **Required environment variables**
   - `CREDITAS_API_TOKEN`: Your Creditas API authentication token
   - `CREDITAS_ACCOUNT_ID`: Your account ID for API calls
   - `SECRET_KEY`: Flask secret key for sessions
   - `KNOWN_ACCOUNTS`: Comma-separated list of your account numbers (format: number/bankCode)

5. **Run the application**
   ```bash
   # Make sure virtual environment is activated
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   python app.py
   ```

## Usage

- Open http://localhost:5000 in your browser
- Click "🔄 Aktualizovat data" to fetch fresh transaction data
- View investment statistics and profit calculations

## Security

- All sensitive data (API tokens, account numbers) is stored in environment variables
- Data files and credentials are excluded from git via `.gitignore`
- No sensitive information is hardcoded in the application

## Architecture

See [CLAUDE.md](CLAUDE.md) for detailed technical documentation.