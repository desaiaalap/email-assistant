import random
import time
import argparse
import logging
from google.cloud import logging as gcp_logging
import uuid
from datetime import datetime, timedelta

# Configure standard logging
logging.basicConfig(level=logging.INFO)


def generate_request_metrics(start_date, days=7, logger=None):
    """Generate request performance metrics for the past 7 days"""
    logging.info("Generating request performance metrics...")

    # Generate data for each day
    current_date = start_date
    for day in range(days):
        # Calculate date for this iteration (going backward from start_date)
        log_date = current_date - timedelta(days=day)
        date_str = log_date.strftime("%Y-%m-%d")

        # Generate between 50-120 requests per day
        num_requests = random.randint(50, 120)

        for i in range(num_requests):
            # Randomly distribute throughout the day (0-23 hours)
            hour = random.randint(0, 23)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            timestamp = datetime(
                log_date.year, log_date.month, log_date.day, hour, minute, second
            )

            # Generate request data
            request_id = str(uuid.uuid4())
            thread_id = f"thread_{uuid.uuid4().hex[:8]}"
            user_email = random.choice(
                [
                    "user1@example.com",
                    "user2@example.com",
                    "try8200@gmail.com",
                    "shubhdesai111@gmail.com",
                ]
            )

            # 85% success rate
            is_success = random.random() < 0.85

            # Generate duration between 0.5 and 3 seconds with occasional spikes
            duration = random.uniform(0.5, 3.0)
            if random.random() < 0.05:  # 5% chance of a slow request
                duration = random.uniform(4.0, 10.0)

            if is_success:
                logger.log_struct(
                    {
                        "message": "Request completed successfully NEW",
                        "request_id": request_id,
                        "thread_id": thread_id,
                        "user_email": user_email,
                        "duration_seconds": duration,
                        "date": date_str,  # Add explicit date field
                    },
                    severity="INFO",
                    # timestamp=timestamp,
                )
            else:
                # Generate different types of errors
                error_types = [
                    "Authentication Error",
                    "API Error",
                    "Connection Error",
                    "Server Error",
                ]
                error_type = random.choice(error_types)

                logger.log_struct(
                    {
                        "message": f"Error processing request: {error_type}",
                        "request_id": request_id,
                        "thread_id": thread_id,
                        "user_email": user_email,
                        "error_type": error_type,
                        "date": date_str,  # Add explicit date field
                    },
                    severity="ERROR",
                    # timestamp=timestamp,
                )
            # logging.info(f"Sent log: request_id={request_id}, user_email={user_email}")


def generate_task_metrics(start_date, days=7, logger=None):
    """Generate task-specific performance metrics"""
    logging.info("Generating task performance metrics...")

    tasks = ["summary", "action_items", "draft_reply"]

    # Generate data for each day
    current_date = start_date
    for day in range(days):
        # Calculate date for this iteration (going backward from start_date)
        log_date = current_date - timedelta(days=day)
        date_str = log_date.strftime("%Y-%m-%d")

        # Generate between 40-90 task completions per day
        num_tasks = random.randint(40, 90)

        for i in range(num_tasks):
            # Randomly distribute throughout the day
            hour = random.randint(0, 23)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            timestamp = datetime(
                log_date.year, log_date.month, log_date.day, hour, minute, second
            )

            # Generate task data
            request_id = str(uuid.uuid4())
            task = random.choice(tasks)
            user_email = random.choice(
                [
                    "user1@example.com",
                    "user2@example.com",
                    "try8200@gmail.com",
                    "shubhdesai111@gmail.com",
                ]
            )

            # Task duration varies by task type
            if task == "summary":
                duration = random.uniform(1.0, 4.0)
            elif task == "action_items":
                duration = random.uniform(0.8, 3.0)
            else:  # draft_reply
                duration = random.uniform(1.5, 5.0)

            logger.log_struct(
                {
                    "message": f"Completed generation for task {task}",
                    "request_id": request_id,
                    "task": task,
                    "user_email": user_email,
                    "duration_seconds": duration,
                    "output_count": 3,  # Always generate 3 outputs
                    "date": date_str,  # Add explicit date field
                },
                severity="INFO",
                # timestamp=timestamp,
            )


def generate_feedback_metrics(start_date, days=7, logger=None):
    """Generate user feedback metrics"""
    logging.info("Generating user feedback metrics...")

    tasks = ["summary", "action_items", "draft_reply"]

    # Generate data for each day
    current_date = start_date
    for day in range(days):
        # Calculate date for this iteration (going backward from start_date)
        log_date = current_date - timedelta(days=day)
        date_str = log_date.strftime("%Y-%m-%d")

        # Generate between 30-60 feedback events per day
        num_feedback = random.randint(30, 60)

        for i in range(num_feedback):
            # Randomly distribute throughout the day
            hour = random.randint(0, 23)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            timestamp = datetime(
                log_date.year, log_date.month, log_date.day, hour, minute, second
            )

            # Generate feedback data
            request_id = str(uuid.uuid4())
            doc_id = random.randint(1000, 9999)
            task = random.choice(tasks)
            user_email = random.choice(
                [
                    "user1@example.com",
                    "user2@example.com",
                    "try8200@gmail.com",
                    "shubhdesai111@gmail.com",
                ]
            )

            # Feedback varies by task
            if task == "summary":
                # 80% positive for summary
                feedback = 1 if random.random() < 0.80 else 0
            elif task == "action_items":
                # 75% positive for action_items
                feedback = 1 if random.random() < 0.75 else 0
            else:  # draft_reply
                # 65% positive for draft_reply
                feedback = 1 if random.random() < 0.65 else 0

            logger.log_struct(
                {
                    "message": "Feedback stored successfully",
                    "request_id": request_id,
                    "doc_id": doc_id,
                    "task": task,
                    "user_email": user_email,
                    "feedback": feedback,
                    "date": date_str,  # Add explicit date field
                },
                severity="INFO",
                # timestamp=timestamp,
            )


def generate_strategy_metrics(start_date, days=7, logger=None):
    """Generate strategy performance metrics"""
    logging.info("Generating strategy performance metrics...")

    tasks = ["summary", "action_items", "draft_reply"]

    # Generate data for each day
    current_date = start_date
    for day in range(days):
        # Calculate date for this iteration (going backward from start_date)
        log_date = current_date - timedelta(days=day)
        date_str = log_date.strftime("%Y-%m-%d")

        # Generate between 20-40 strategy-related events per day
        num_events = random.randint(20, 40)

        for i in range(num_events):
            # Randomly distribute throughout the day
            hour = random.randint(0, 23)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            timestamp = datetime(
                log_date.year, log_date.month, log_date.day, hour, minute, second
            )

            # Generate strategy data
            request_id = str(uuid.uuid4())
            task = random.choice(tasks)
            user_email = random.choice(
                [
                    "user1@example.com",
                    "user2@example.com",
                    "try8200@gmail.com",
                    "shubhdesai111@gmail.com",
                ]
            )

            # 70% default strategy, 30% alternate
            strategy = "default" if random.random() < 0.7 else "alternate"

            logger.log_struct(
                {
                    "message": f"Using {strategy} strategy for task {task}",
                    "request_id": request_id,
                    "task": task,
                    "user_email": user_email,
                    "prompt_strategy": strategy,
                    "date": date_str,  # Add explicit date field
                },
                severity="INFO",
                # timestamp=timestamp,
            )

            # Occasionally add optimization events
            if (
                day < 3 and random.random() < 0.15
            ):  # Only add optimizations in recent days
                old_strategy = "default"
                new_strategy = "alternate"
                performance_score = random.uniform(0.5, 0.65)  # Below threshold

                logger.log_struct(
                    {
                        "message": f"Updated user-specific prompt strategy for {user_email} on {task}",
                        "request_id": request_id,
                        "task": task,
                        "user_email": user_email,
                        "old_strategy": old_strategy,
                        "new_strategy": new_strategy,
                        "performance_score": performance_score,
                        "date": date_str,  # Add explicit date field
                    },
                    severity="INFO",
                    # timestamp=timestamp,
                )


def generate_7day_metrics(logger):
    """Generate all metrics for past 7 days"""

    # Calculate today's date and 7 days ago
    today = datetime.now()

    logging.info(f"Generating metrics starting from {today} going back 7 days")

    # Generate different types of metrics
    generate_request_metrics(today, logger=logger)
    generate_task_metrics(today, logger=logger)
    generate_feedback_metrics(today, logger=logger)
    generate_strategy_metrics(today, logger=logger)

    logging.info("Successfully generated 7 days worth of metrics!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate MailMate metrics for GCP dashboard"
    )
    parser.add_argument("--project", help="GCP Project ID", required=True)

    args = parser.parse_args()

    # Configure GCP client with project ID
    client = gcp_logging.Client(project=args.project)
    logger = client.logger("mailmate_metrics")

    # Generate all metrics
    generate_7day_metrics(logger)
