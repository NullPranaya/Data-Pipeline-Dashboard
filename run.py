import schedule
import time

from pipeline import run

run()

schedule.every(1).hours.do(run)

print("\n[scheduler] Running every hour. Press Ctrl+C to stop.")
while True:
    schedule.run_pending()
    time.sleep(60)