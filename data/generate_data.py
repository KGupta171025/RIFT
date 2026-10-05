"""
RIFT — Refund Intelligence & Financial Tracking
Synthetic Dataset Generator
Generates realistic fintech support ticket data for analysis.
"""

import csv
import random
import os
from datetime import datetime, timedelta

random.seed(42)

AGENTS = [
    "Priya Sharma", "Rahul Mehta", "Ananya Verma",
    "Karan Singh", "Sneha Patel", "Arjun Nair",
    "Divya Reddy", "Mohit Gupta"
]

CATEGORIES = [
    "Duplicate Charge",
    "Billing Error",
    "Cancellation Refund",
    "Technical Error",
    "Policy Dispute",
    "Fraud Claim"
]

CHANNELS = ["Email", "Chat", "Phone"]

PRODUCTS = [
    "Premium Subscription",
    "One-Time Purchase",
    "Annual Plan",
    "Add-On Service",
    "Trial Conversion"
]

# Realistic ticket descriptions per category
DESCRIPTIONS = {
    "Duplicate Charge": [
        "Customer was charged twice for the same transaction on {date}.",
        "Duplicate debit of ₹{amt} observed in bank statement.",
        "Payment processed twice — customer requesting reversal of second charge.",
        "Two identical charges appear on the account within 5 minutes.",
        "UPI transaction duplicated due to network timeout; customer wants refund."
    ],
    "Billing Error": [
        "Customer billed ₹{amt} instead of the agreed ₹{amt2} as per invoice.",
        "Wrong plan amount deducted; customer is on Basic but charged for Premium.",
        "Tax calculation error — overcharged by ₹{amt}.",
        "Pro-rated amount incorrectly computed after mid-cycle upgrade.",
        "Customer received incorrect invoice; amount does not match contract."
    ],
    "Cancellation Refund": [
        "Customer cancelled subscription within 7-day refund window; requesting full refund.",
        "Annual plan cancelled on day 2; pro-rata refund requested.",
        "Customer closed account and wants remaining balance returned.",
        "Service cancelled due to relocation; customer requesting partial refund.",
        "Subscription cancelled per company policy change; full refund expected."
    ],
    "Technical Error": [
        "Payment debited but service not activated due to system error.",
        "App crash during checkout resulted in charge with no order confirmation.",
        "Recurring payment triggered despite cancellation request submitted earlier.",
        "Platform downtime caused service disruption; customer demanding compensation.",
        "API timeout during transaction led to double deduction."
    ],
    "Policy Dispute": [
        "Customer disputes no-refund policy; insists verbal confirmation of refund eligibility.",
        "Refund denied per T&C; customer escalating to consumer forum.",
        "Customer unaware of auto-renewal clause; requests reversal.",
        "Disagrees with partial-refund policy on annual plans.",
        "Customer claims sales representative promised full refund at any time."
    ],
    "Fraud Claim": [
        "Unauthorized transaction reported; customer did not initiate payment.",
        "Card used without consent; customer filed police complaint.",
        "Phishing attack resulted in fraudulent charges on account.",
        "Multiple unknown charges from same IP; customer flagging fraud.",
        "Account compromised; 3 transactions disputed as unauthorized."
    ]
}

# Avoidability logic per category
AVOIDABLE_RATES = {
    "Duplicate Charge":       0.90,  # Almost always avoidable with idempotency
    "Billing Error":          0.80,  # Usually a system/human error
    "Cancellation Refund":    0.15,  # Policy-driven, mostly valid
    "Technical Error":        0.70,  # Engineering fix would prevent
    "Policy Dispute":         0.30,  # Customer education could help
    "Fraud Claim":            0.10,  # Hard to prevent fully
}

# Refund amount ranges (₹) per category
REFUND_RANGES = {
    "Duplicate Charge":       (200, 1500),
    "Billing Error":          (150, 2000),
    "Cancellation Refund":    (500, 5000),
    "Technical Error":        (300, 1800),
    "Policy Dispute":         (400, 3000),
    "Fraud Claim":            (800, 8000),
}

# Refund grant rate per category
GRANT_RATES = {
    "Duplicate Charge":       0.95,
    "Billing Error":          0.85,
    "Cancellation Refund":    0.65,
    "Technical Error":        0.80,
    "Policy Dispute":         0.25,
    "Fraud Claim":            0.70,
}


def random_date(start_days_ago: int = 90) -> str:
    start = datetime.now() - timedelta(days=start_days_ago)
    delta = timedelta(days=random.randint(0, start_days_ago))
    return (start + delta).strftime("%Y-%m-%d")


def generate_tickets(n: int = 500) -> list[dict]:
    tickets = []
    for i in range(1, n + 1):
        category = random.choices(
            CATEGORIES,
            weights=[0.20, 0.18, 0.22, 0.15, 0.12, 0.13],
            k=1
        )[0]

        refund_min, refund_max = REFUND_RANGES[category]
        refund_amount = round(random.uniform(refund_min, refund_max), 2)
        refund_amount2 = round(refund_amount * random.uniform(0.6, 0.9), 2)

        desc_template = random.choice(DESCRIPTIONS[category])
        description = desc_template.replace("{amt}", str(int(refund_amount))) \
                                   .replace("{amt2}", str(int(refund_amount2))) \
                                   .replace("{date}", random_date(30))

        refund_granted = random.random() < GRANT_RATES[category]
        avoidable = random.random() < AVOIDABLE_RATES[category]
        resolution_hrs = round(random.uniform(0.5, 72), 1)

        tickets.append({
            "ticket_id":           f"TKT-{i:04d}",
            "date":                random_date(90),
            "agent_name":          random.choice(AGENTS),
            "customer_id":         f"CUST-{random.randint(1000, 9999)}",
            "category":            category,
            "description":         description,
            "product":             random.choice(PRODUCTS),
            "channel":             random.choice(CHANNELS),
            "refund_requested":    True,
            "refund_amount_inr":   refund_amount,
            "refund_granted":      refund_granted,
            "avoidable":           avoidable,
            "resolution_time_hrs": resolution_hrs,
            "sentiment":           random.choice(["Negative", "Negative", "Neutral", "Positive"]),
        })
    return tickets


def save_csv(tickets: list[dict], path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=tickets[0].keys())
        writer.writeheader()
        writer.writerows(tickets)
    print(f"[OK] Saved {len(tickets)} tickets to {path}")


if __name__ == "__main__":
    out_path = os.path.join(os.path.dirname(__file__), "tickets.csv")
    tickets = generate_tickets(500)
    save_csv(tickets, out_path)

    # Quick stats
    granted = sum(1 for t in tickets if t["refund_granted"])
    avoidable = sum(1 for t in tickets if t["avoidable"])
    total_refund = sum(t["refund_amount_inr"] for t in tickets if t["refund_granted"])
    print(f"   Refunds granted : {granted}/{len(tickets)}")
    print(f"   Avoidable flags : {avoidable} ({avoidable/len(tickets)*100:.1f}%)")
    print(f"   Total INR refunded: Rs.{total_refund:,.0f}")
