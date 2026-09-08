"""
Service Charge Split: Proportional service charge allocation.

Rule: person_service[person_id] = share[person_id] × bill.service_charge
"""
from decimal import Decimal

from app.utils.decimal_utils import ZERO


def allocate_service_charge(
    consumption_shares: dict[str, Decimal],
    service_charge_total: Decimal,
) -> dict[str, Decimal]:
    """
    Distribute service charge proportionally by consumption share.

    Args:
        consumption_shares: {person_id: share} — fractions summing to ~1.
        service_charge_total: Total service charge from the bill.

    Returns:
        {person_id: service_charge_amount} — exact (unrounded) Decimal amounts.
    """
    if service_charge_total == ZERO:
        return {pid: ZERO for pid in consumption_shares}

    return {pid: share * service_charge_total for pid, share in consumption_shares.items()}
