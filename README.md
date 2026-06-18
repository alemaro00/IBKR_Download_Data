# Python Project for download data from IBKR
link libreria ib_async: https://pypi.org/project/ib_async/

link per vedere che cosa si può mettere in whattoshow: https://interactivebrokers.github.io/tws-api/historical_bars.html#hd_what_to_show

IBKR_Download_Data/
│
├── main.py
├── .env
│
└── src/
    └── modules/
        ├── __init__.py                
        ├── historical_data.py
        ├── realtime_data.py
        ├── portfolio_monitoring.py
        └── telegram_messages.py