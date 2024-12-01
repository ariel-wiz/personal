import numpy as np
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta


class ETF:
    def __init__(self, symbol: str, name: str, quantity: float = 0):
        self.symbol = symbol
        self.name = name
        self.quantity = quantity
        self.ticker = yf.Ticker(symbol)

    def set_quantity(self, quantity: float):
        """Set the number of shares held"""
        self.quantity = quantity

    def get_current_data(self):
        """Get current price and performance data with 24h, 5d, and 1mo changes"""
        # Get one month of data
        hist = self.ticker.history(period='1mo', interval='1d', actions=False, auto_adjust=True)

        if len(hist) < 2:
            raise ValueError(f"Could not fetch current data for {self.symbol}")

        # Current price and 24h change
        current_price = hist['Close'][-1]
        daily_change = hist['Close'][-1] - hist['Close'][-2]
        daily_change_pct = (daily_change / hist['Close'][-2]) * 100

        # Calculate 5d change
        week_ago_price = None
        for i in range(min(len(hist) - 1, 5), -1, -1):
            if i > 0:
                week_ago_price = hist['Close'][-i - 1]
                break

        if week_ago_price is not None:
            weekly_change = current_price - week_ago_price
            weekly_change_pct = (weekly_change / week_ago_price) * 100
        else:
            weekly_change = 0
            weekly_change_pct = 0

        # Calculate 1 month change
        if len(hist) > 1:
            month_ago_price = hist['Close'][0]  # First price in the month
            monthly_change = current_price - month_ago_price
            monthly_change_pct = (monthly_change / month_ago_price) * 100
        else:
            monthly_change = 0
            monthly_change_pct = 0

        # Calculate revenue from changes
        daily_revenue = daily_change * self.quantity
        weekly_revenue = weekly_change * self.quantity
        monthly_revenue = monthly_change * self.quantity

        return {
            'Name': self.name,
            'Symbol': self.symbol,
            'Quantity': self.quantity,
            'Current Price': round(current_price, 2),
            '24h Change': round(daily_change, 2),
            '24h Change %': round(daily_change_pct, 2),
            '24h Revenue': round(daily_revenue, 2),
            '5d Change': round(weekly_change, 2),
            '5d Change %': round(weekly_change_pct, 2),
            '5d Revenue': round(weekly_revenue, 2),
            '1mo Change': round(monthly_change, 2),
            '1mo Change %': round(monthly_change_pct, 2),
            '1mo Revenue': round(monthly_revenue, 2),
            'Total Value': round(current_price * self.quantity, 2)
        }


def create_portfolio():
    """Create portfolio with the specified ETFs"""
    portfolio = {
        'CSPX': ETF('CSPX.L', 'iShares Core S&P 500 UCITS ETF', 12),
        'CNDX': ETF('CNDX.L', 'iShares NASDAQ 100 UCITS ETF', 2),
        'EMIM': ETF('EIMI.L', 'iShares Core MSCI EM IMI UCITS ETF', 51),
        'IMEU': ETF('EUNK.DE', 'iShares Core MSCI Europe UCITS ETF', 7),
        # 'TLV': ETF('^TA125.TA', 'Tel Aviv 125 Index', 100)
    }
    return portfolio


def calculate_averages(results):
    """Calculate average changes across all ETFs"""
    changes_24h = [r['24h Change %'] for r in results]
    changes_5d = [r['5d Change %'] for r in results]
    changes_1mo = [r['1mo Change %'] for r in results]

    avg_24h = np.mean(changes_24h)
    avg_5d = np.mean(changes_5d)
    avg_1mo = np.mean(changes_1mo)

    return {
        'Average 24h Change %': round(avg_24h, 2),
        'Average 5d Change %': round(avg_5d, 2),
        'Average 1mo Change %': round(avg_1mo, 2)
    }


if __name__ == "__main__":
    # Create portfolio
    portfolio = create_portfolio()

    # Print current portfolio status
    print("\nPortfolio Overview:")
    print("=" * 120)

    results = []
    total_24h_revenue = 0
    total_5d_revenue = 0
    total_1mo_revenue = 0
    total_value = 0

    for etf in portfolio.values():
        try:
            data = etf.get_current_data()
            results.append(data)
            if data['Quantity'] > 0:
                total_24h_revenue += data['24h Revenue']
                total_5d_revenue += data['5d Revenue']
                total_1mo_revenue += data['1mo Revenue']
                total_value += data['Total Value']
        except Exception as e:
            print(f"Error processing {etf.name}: {str(e)}")

    # Calculate and print averages
    averages = calculate_averages(results)
    print("\nMarket Averages:")
    for key, value in averages.items():
        print(f"{key}: {value}%")

    # Convert to DataFrame for better display
    df = pd.DataFrame(results)
    print("\nDetailed Overview:")
    print(df.to_string(index=False))

    # Print portfolio totals
    print("\nPortfolio Totals:")
    print(f"Total 24h Revenue: ${round(total_24h_revenue, 2)}")
    print(f"Total 5d Revenue: ${round(total_5d_revenue, 2)}")
    print(f"Total 1mo Revenue: ${round(total_1mo_revenue, 2)}")
    print(f"Total Portfolio Value: ${round(total_value, 2)}")