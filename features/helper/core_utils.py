def evaluate_condition(condition_expr: str, context_vars: dict) -> bool:
    """
    Evaluates a boolean expression with context variables.
    Example: '@if: cartId and user_id != ""'
    """
    try:
        for key, val in context_vars.items():
            if isinstance(val, str):
                context_vars[key] = f'"{val}"'
        return eval(condition_expr, {}, context_vars)
    except Exception as e:
        raise ValueError(f"Error evaluating condition '{condition_expr}': {e}")


def should_skip_scenario(context, condition_key='@if:'):
    """
    Determines if a scenario should be skipped based on a conditional expression tag.
    """
    for tag in context.tags:
        if tag.startswith(condition_key):
            condition = tag[len(condition_key):]
            return not evaluate_condition(condition, context.__dict__)
    return False