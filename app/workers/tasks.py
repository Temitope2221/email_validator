from celery import Celery
import pandas as pd
from app.core.validator import validate_email_simple, is_valid_email
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
celery = Celery(__name__, broker=REDIS_URL)

# Ensure output directory exists
OUTPUT_DIR = "./output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

@celery.task(bind=True)
def validate_csv_task(self, file_path: str, job_id: str, detailed: bool = False):
    """
    Validate emails in CSV file

    Args:
        file_path: Path to input CSV file
        job_id: Unique job identifier
        detailed: Whether to include detailed validation results
    """
    try:
        logger.info(f"Starting validation for job {job_id}")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Input file not found: {file_path}")

        df = pd.read_csv(file_path)

        if 'email' not in df.columns:
            raise ValueError("CSV file must contain an 'email' column")

        total_emails = len(df)
        logger.info(f"Processing {total_emails} emails for job {job_id}")

        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': total_emails, 'status': 'Starting validation...'}
        )

        if detailed:
            validation_results = []
            for idx, email in enumerate(df['email']):
                result = is_valid_email(str(email))
                validation_results.append(result)

                if idx % 10 == 0:
                    self.update_state(
                        state='PROGRESS',
                        meta={'current': idx, 'total': total_emails, 'status': f'Validated {idx}/{total_emails} emails...'}
                    )

            results_df = pd.DataFrame(validation_results)
            output_file = os.path.join(OUTPUT_DIR, f"{job_id}_detailed_validated.csv")
            results_df.to_csv(output_file, index=False)
        else:
            df['valid'] = df['email'].apply(lambda x: validate_email_simple(str(x)))
            output_file = os.path.join(OUTPUT_DIR, f"{job_id}_validated.csv")
            df.to_csv(output_file, index=False)

        try:
            os.remove(file_path)
        except:
            pass

        logger.info(f"Validation completed for job {job_id}")

        return {
            'status': 'SUCCESS',
            'total_processed': total_emails,
            'output_file': output_file
        }

    except Exception as e:
        logger.error(f"Error in validation task {job_id}: {str(e)}")
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass
        raise

