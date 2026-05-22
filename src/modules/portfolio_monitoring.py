#=============================================================================================

#Per vedere tutte le funzioni disponibili dentro la libreria ib_async quindi Stock, Forex, reqHistoricalData, etc
#import ib_async
#print(dir(ib_async)) 

#=============================================================================================

from ib_async import *
import datetime
import pytz

def onPnL(pnl):
    print(f"P&L Update: Unrealized: ${pnl.unrealizedPnL:.2f}, Realized: ${pnl.realizedPnL:.2f}")

ib = IB()
ib.connect("127.0.0.1", 7497, clientId=1)


# Subscribe to P&L updates (polling version)
account = ib.managedAccounts()[0]
pnl = ib.reqPnL(account)
try:
    while True:
        ib.sleep(3600)
        # Get current positions
        positions = ib.positions()
        print("Current Positions:")
        for pos in positions:
            print(f"{pos.contract.symbol}: {pos.position} @ {pos.avgCost}")
        # Get open orders
        orders = ib.openTrades()
        print(f"Open Orders: {len(orders)}")
        for trade in orders:
            print(f"{trade.contract.symbol}: {trade.order.action} {trade.order.totalQuantity}")
        # Get P&L updates
        print(f"P&L Update: Unrealized: ${pnl.unrealizedPnL:.2f}, Realized: ${pnl.realizedPnL:.2f}")
except KeyboardInterrupt:
    ib.disconnect()