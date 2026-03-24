import threading
import schedule
import time

from pipeline import run
from app import app


def scheduler_loop():
    run()  # run immediately on start
    schedule.every(1).hours.do(run)
    print("[scheduler] Running every hour. Press Ctrl+C to stop.")
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    t = threading.Thread(target=scheduler_loop, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=5050, debug=False)
