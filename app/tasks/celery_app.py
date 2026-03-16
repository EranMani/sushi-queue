"""
THE KITCHEN STAFF (Celery Asynchronous Task Queue)
-----------------------------------------------------
What is Celery? 
In the software world, Celery is an asynchronous task queue. 
In our restaurant, Celery is the Kitchen Staff. 

- The Bottleneck: When tasks take too long (like processing payments, sending receipts, or running heavy database sweeps), 
  the FastAPI Waiter cannot just stand there waiting, or the entire restaurant freezes.

- The Quick Handoff: Instead of waiting, the Waiter instantly writes a "ticket" (a message) and drops it into a queue.

- The Background Crew: Celery workers (the Kitchen Staff) run continuously out of sight.

- The Heavy Lifting: These workers constantly pull tickets off the queue and do the hard work, 
  completely freeing up the Waiters to keep serving customers without interruption.

The Two Main Parts:
1. Celery Workers (The Chefs): The actual background processes that execute tasks.
2. Celery Beat (The Kitchen Timer): An alarm clock that doesn't do the work itself, 
   but automatically drops new tickets onto the queue on a strict schedule.

Key Configurations:
- Broker: The Inbox (Ticket Rail). Where Waiters drop new tickets (Redis).
- Backend: The Outbox (Pickup Counter). Where Chefs leave the results (Redis).
- Include: The Recipe Book. The specific Python files the Chefs need to read 
  so they know how to execute the tasks. the files are purely dedicated background jobs!
  for example:
    - app.tasks.email_tasks: The Waiter shouldn't wait for Gmail to respond. 
                             Any function that sends a "Welcome!" email, a password reset link, or a promotional blast goes here.
    - app.tasks.order_tasks: Things like securely charging a credit card with Stripe, generating a PDF receipt, 
                             or notifying the shipping department.
    - app.tasks.cleanup_tasks: The "sweeping the floors" stuff. Sweeping the database for abandoned carts, 
                               clearing expired user sessions, or deleting temporary files.
    - app.tasks.report_tasks: Heavy math. For example, a task that runs at 2:00 AM every night to calculate 
                              the daily sales, total inventory used, and emails a spreadsheet to the Manager.
"""

from celery import Celery
from app.core.config import settings

# HIRING THE KITCHEN STAFF
celery_app = Celery(
    "sushi_queue",
    broker=settings.redis_url, # The inbox / redis whiteboard, Where chefs look for new order tickets
    backend=settings.redis_url, # The outbox / redis whiteboard, Where chefs leave the finished result
    include=["app.tasks.order_tasks", "app.tasks.cleanup_tasks"] # The specific files containing the tasks the staff needs to know.
)

# KITCHEN LANGUAGE (JSON)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# THE KITCHEN TIMER (Celery Beat)
# This acts like an alarm clock that automatically prints a ticket on a strict schedule.
celery_app.conf.beat_schedule = {
    "cancel-stale-orders": {
        "task": "app.tasks.cleanup_tasks.cancel_stale_orders", # "Chef, run this specific cleanup routine"
        "schedule": 60.0, # "every 60 seconds."
    },
}
