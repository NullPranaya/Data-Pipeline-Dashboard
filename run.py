import threading
import schedule
import time

import config
from pipeline import run
from app import app


def scheduler_loop():
    run()  # run immediately on start
    schedule.every(config.PIPELINE_INTERVAL_HOURS).hours.do(run)
    print(f"[scheduler] Running every {config.PIPELINE_INTERVAL_HOURS} hour(s). Press Ctrl+C to stop.")
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    t = threading.Thread(target=scheduler_loop, daemon=True)
    t.start()
    app.run(host=config.APP_HOST, port=config.APP_PORT, debug=False)
