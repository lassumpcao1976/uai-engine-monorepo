"""
Centralized credit pricing configuration
"""
from typing import Dict

# Credit costs for all actions
CREDIT_COSTS: Dict[str, float] = {
    "create_project": 5.0,
    "small_edit": 1.0,
    "medium_edit": 3.0,
    "large_edit": 10.0,
    "rebuild": 1.0,
    "rollback": 3.0,
    "export": 20.0,
    "publish": 50.0,
}

# Free tier starting credits
FREE_TIER_STARTING_CREDITS = 10.0

def get_credit_costs() -> Dict[str, float]:
    """Get all credit costs (for API endpoint)"""
    return CREDIT_COSTS.copy()
