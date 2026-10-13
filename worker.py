"""Run the pipeline automatically on a schedule:  python worker.py"""
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
import db
import pipeline

db.init()
minutes = int(db.get_settings()["run_every_minutes"])
sched = BlockingScheduler()
sched.add_job(pipeline.run_all, "interval", minutes=minutes, next_run_time=datetime.now(), max_instances=1)
print(f"Worker started: pipeline runs every {minutes} min. Ctrl+C to stop.")
sched.start()
