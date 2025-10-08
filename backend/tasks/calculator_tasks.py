import re
import math
from backend.celery_app import celery_app
from datetime import datetime  # Add this import

@celery_app.task
def execute_calculator_task(task_args):
    try:
        query = task_args.get('query', '')
        user_input = task_args.get('user_input', '')
        
        # Extract mathematical expression
        expression = extract_math_expression(query)
        if not expression:
            return "Sorry, I couldn't understand the math problem."
        
        # Evaluate safely
        result = safe_evaluate(expression)
        return f"🧮 Calculation: {expression} = {result}"
        
    except Exception as e:
        return f"❌ Calculation error: {str(e)}"

def extract_math_expression(text: str) -> str:
    """Extract mathematical expressions from text"""
    # Remove common phrases and get to the math
    text = re.sub(r'(calculate|what is|what\'s|compute|solve)\s+', '', text.lower())
    
    # Match mathematical expressions
    math_pattern = r'([-+]?[0-9]*\.?[0-9]+\s*[\+\-\*\/\^]\s*)+([-+]?[0-9]*\.?[0-9]+)'
    match = re.search(math_pattern, text)
    
    if match:
        return match.group(0).strip()
    
    # Try to find simple numbers and operations
    words = text.split()
    for i, word in enumerate(words):
        if any(op in word for op in ['+', '-', '*', '/']):
            # Try to reconstruct expression
            start = max(0, i-2)
            end = min(len(words), i+3)
            return ' '.join(words[start:end])
    
    return ""

def safe_evaluate(expression: str) -> float:
    """Safely evaluate mathematical expression"""
    # Clean the expression
    clean_expr = re.sub(r'[^\d\+\-\*\/\(\)\.\s]', '', expression)
    clean_expr = clean_expr.replace(' ', '')
    
    # Replace ^ with ** for exponentiation
    clean_expr = clean_expr.replace('^', '**')
    
    try:
        # Use eval but only with safe operations
        allowed_chars = set('0123456789+-*/.() ')
        if all(c in allowed_chars for c in clean_expr):
            return eval(clean_expr)
        else:
            raise ValueError("Unsafe mathematical expression")
    except:
        raise ValueError("Invalid mathematical expression")