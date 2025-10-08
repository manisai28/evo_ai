from datetime import datetime
from backend.celery_app import celery_app
from backend.database import (
    get_user_expenses_sync,
    save_user_expense_sync,
    get_total_expenses_sync
)
import re


@celery_app.task
def execute_expense_task(task_args):
    """
    Handles expense creation and retrieval (sync version for Celery).
    """
    try:
        query = task_args.get('query', '').lower()
        action = task_args.get('action', 'create')
        user_id = task_args.get('user_id', 'default_user')

        # ===========================
        # Retrieve Expenses
        # ===========================
        if action == "retrieve" or any(word in query for word in ['show', 'list', 'summary']):
            expenses = get_user_expenses_sync(user_id)
            total = get_total_expenses_sync(user_id)

            if not expenses:
                return "💰 No expenses tracked yet."

            expense_list = "\n".join(
                [f"- ${e.get('amount', 0.0):.2f}: {e.get('description', 'Miscellaneous')} "
                 f"({e.get('timestamp', datetime.now()).strftime('%m/%d %I:%M %p')})"
                 for e in expenses]
            )

            return f"💰 Your expenses:\n{expense_list}\n\n💵 Total: ${total:.2f}"

        # ===========================
        # Add New Expense
        # ===========================
        else:
            amount = extract_amount(query)
            description = extract_description(query)

            save_user_expense_sync(user_id, amount, description)
            total = get_total_expenses_sync(user_id)

            return f"💰 Added expense: {description} - ${amount:.2f}. Total expenses: ${total:.2f}"

    except Exception as e:
        return f"❌ Expense task error: {str(e)}"


# ==========================================================
# Expense Parsing Helpers
# ==========================================================
def extract_amount(query):
    """Extract amount from query."""
    # Look for dollar amounts first
    amount_match = re.search(r'\$(\d+(?:\.\d{2})?)', query)
    if amount_match:
        return float(amount_match.group(1))

    # Look for number amounts with keywords
    amount_match = re.search(r'(\d+(?:\.\d{2})?)\s*(dollars|dollar|bucks|buck)', query)
    if amount_match:
        return float(amount_match.group(1))

    # Look for standalone numbers in context of spending
    amount_match = re.search(r'spent\s+(\d+(?:\.\d{2})?)', query)
    if amount_match:
        return float(amount_match.group(1))

    # Any number in the context of spending
    amount_match = re.search(r'(\d+(?:\.\d{2})?)', query)
    if amount_match:
        return float(amount_match.group(1))

    return 0.0


def extract_description(query):
    """Extract expense description from query."""
    # Remove amounts and common words
    cleaned = re.sub(r'\$?\d+(?:\.\d{2})?\s*(dollars|dollar|bucks|buck)?', '', query)
    cleaned = re.sub(r'(add|track|spent|expense|on|for|cost|price)', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    if cleaned and len(cleaned) > 2:
        return cleaned

    # Try to extract "on" or "for" phrases
    spent_match = re.search(r'on\s+(.+)', query)
    if spent_match:
        return spent_match.group(1).strip()

    spent_match = re.search(r'for\s+(.+)', query)
    if spent_match:
        return spent_match.group(1).strip()

    return "Miscellaneous"
