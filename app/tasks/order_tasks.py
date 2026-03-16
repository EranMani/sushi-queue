from app.tasks.celery_app import celery_app

"""
THE OFFICIAL RECIPE STAMP (@celery_app.task)
Registers this function so the Kitchen Staff (Celery) knows it's a valid background job.

THE WALKIE-TALKIE (bind=True)
Passes the task instance as 'self', letting the Chef communicate back to the system 
(e.g., self.retry() if a payment fails, or self.update_state() to report cooking progress).
"""

@celery_app.task(bind=True)
def process_order(self, order_id: int):
    # NOTE: will be implemented later
    pass