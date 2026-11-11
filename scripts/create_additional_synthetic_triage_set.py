"""Write a separate, explicitly synthetic triage training set."""
import json
from pathlib import Path


OUT = Path("data/processed/triage_additional_synthetic.jsonl")

# Each tuple is ticket, category, priority, product area. These fictional
# scenarios are separate from evals/data/reviewed_triage.jsonl and are not
# represented as human-reviewed or customer-provided examples.
EXAMPLES = [
    # bug (10)
    ("The usage chart stops updating after I change the date range.", "bug", "normal", "platform"),
    ("The webhook test panel shows a blank result for a successful request.", "bug", "normal", "platform"),
    ("Search filters disappear when I move to the next results page.", "bug", "normal", "platform"),
    ("The nightly export task fails after the workspace timezone changes.", "bug", "normal", "platform"),
    ("The integration status page shows yesterday's sync time after a new sync finishes.", "bug", "normal", "platform"),
    ("A release has stopped every team in our region from opening dashboards.", "bug", "high", "platform"),
    ("The role editor removes a member's permissions when I save an unrelated profile field.", "bug", "normal", "identity"),
    ("The password reset form reports success but leaves the account locked.", "bug", "high", "identity"),
    ("The invoice preview rounds the tax total differently from the final invoice.", "bug", "normal", "billing"),
    ("The help drawer covers the save button on a small laptop screen.", "bug", "normal", "general"),
    # billing (10)
    ("Our renewal was charged twice this morning.", "billing", "high", "billing"),
    ("The latest invoice includes a second charge for the same seat.", "billing", "high", "billing"),
    ("We were billed for a plan after its cancellation date.", "billing", "high", "billing"),
    ("The payment receipt shows an amount different from the card charge.", "billing", "high", "billing"),
    ("Where can I download last quarter's invoices?", "billing", "normal", "billing"),
    ("Could you explain the usage adjustment on this month's bill?", "billing", "normal", "billing"),
    ("I need a receipt for a payment made by our previous billing contact.", "billing", "normal", "billing"),
    ("When will the next subscription renewal appear on the invoice?", "billing", "normal", "billing"),
    ("How do I change the billing address for future invoices?", "billing", "normal", "billing"),
    ("Can you clarify which plan features are included in this charge?", "billing", "normal", "billing"),
    # account (10)
    ("I am locked out because the sign-in code never arrives.", "account", "high", "identity"),
    ("Our administrator cannot sign in to manage the workspace.", "account", "high", "identity"),
    ("My account remains suspended after I completed the recovery steps.", "account", "high", "identity"),
    ("A teammate lost access to their profile after changing phones.", "account", "high", "identity"),
    ("I cannot accept the workspace invitation with the email address on my account.", "account", "high", "identity"),
    ("How can I change the name shown on my profile?", "account", "normal", "identity"),
    ("I need to update the email address associated with my login.", "account", "normal", "identity"),
    ("Where can I review the list of workspace members?", "account", "normal", "identity"),
    ("Can an owner change another member's assigned role?", "account", "normal", "identity"),
    ("I have a question about setting up a new user profile.", "account", "normal", "identity"),
    # feature_request (10)
    ("Please let us schedule a dashboard export for the first day of each month.", "feature_request", "low", "platform"),
    ("Could search support a saved set of filters for each team?", "feature_request", "low", "platform"),
    ("It would help to download integration run history as a CSV file.", "feature_request", "low", "platform"),
    ("Please add profile-level options for the sign-in notification settings.", "feature_request", "low", "identity"),
    ("Could workspace owners configure a custom session timeout?", "feature_request", "low", "identity"),
    ("Please let billing admins set a monthly spending alert.", "feature_request", "low", "billing"),
    ("We would like to download invoices for a custom date range.", "feature_request", "low", "billing"),
    ("A compact layout option would make the workspace easier to scan.", "feature_request", "low", "general"),
    ("Please add a way to choose which product announcements appear.", "feature_request", "low", "general"),
    ("Could audit events include a filter for changes to security settings?", "feature_request", "low", "security"),
    # how_to (10)
    ("How do I schedule a report export from a dashboard?", "how_to", "low", "platform"),
    ("Where can I find the identifier for a failed API request?", "how_to", "low", "platform"),
    ("How can I reconnect an integration after rotating its token?", "how_to", "low", "platform"),
    ("Where do I change the display name on my profile?", "how_to", "low", "identity"),
    ("How can an owner invite a new member to the workspace?", "how_to", "low", "identity"),
    ("Where can I download a receipt for a completed payment?", "how_to", "low", "billing"),
    ("How do I update the payment method for our subscription?", "how_to", "low", "billing"),
    ("Where can I change the default timezone for the workspace?", "how_to", "low", "general"),
    ("How do I turn off optional product announcement emails?", "how_to", "low", "general"),
    ("Where can I review recent changes to security settings?", "how_to", "low", "security"),
    # security (10)
    ("A workspace access token was posted publicly and is still active.", "security", "urgent", "security"),
    ("We confirmed an unknown administrator is accessing our workspace now.", "security", "urgent", "security"),
    ("An exposed credential has been used to download private workspace data.", "security", "urgent", "security"),
    ("We see an active automated login attack against several accounts.", "security", "urgent", "security"),
    ("A public storage link is currently exposing confidential customer records.", "security", "urgent", "security"),
    ("Our incident team confirmed an unauthorized session is still active.", "security", "urgent", "security"),
    ("Several sign-ins look suspicious and we need a security investigation.", "security", "high", "security"),
    ("We found a possible access-control flaw and need it assessed.", "security", "high", "security"),
    ("A former contractor may still have access to a restricted workspace.", "security", "high", "security"),
    ("Please review a vulnerability report affecting our workspace settings.", "security", "high", "security"),
    # other (10)
    ("Could you explain how workspace announcements are normally shared?", "other", "normal", "general"),
    ("I am looking for an overview of the product's main workspace sections.", "other", "normal", "general"),
    ("Can you point me to information about the supported languages?", "other", "normal", "general"),
    ("We have a general question about how teams are organized.", "other", "normal", "general"),
    ("Where can I read an introduction to the workspace?", "other", "normal", "general"),
    ("Could you clarify what the different navigation sections are for?", "other", "normal", "general"),
    ("I would like information about the product's availability regions.", "other", "normal", "general"),
    ("Is there a glossary explaining terms used throughout the interface?", "other", "normal", "general"),
    ("Can someone share a high-level description of the service?", "other", "normal", "general"),
    ("I have a general question about where to find product information.", "other", "normal", "general"),
]


def main() -> None:
    allowed = {
        "category": {"bug", "billing", "account", "feature_request", "how_to", "security", "other"},
        "priority": {"low", "normal", "high", "urgent"},
        "product_area": {"platform", "billing", "identity", "general", "security"},
    }
    eval_path = Path("evals/data/reviewed_triage.jsonl")
    eval_tickets = set()
    if eval_path.exists():
        eval_tickets = {json.loads(line)["ticket"] for line in eval_path.read_text(encoding="utf-8").splitlines() if line.strip()}
    seen = set()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="\n") as stream:
        for ticket, category, priority, product_area in EXAMPLES:
            if ticket in seen or ticket in eval_tickets:
                raise ValueError(f"Duplicate ticket or evaluation overlap: {ticket}")
            seen.add(ticket)
            label = {"category": category, "priority": priority, "product_area": product_area}
            for field, valid in allowed.items():
                if label[field] not in valid:
                    raise ValueError(f"Invalid {field} value: {label[field]}")
            stream.write(json.dumps({"ticket": ticket, "label": label, "synthetic": True}, ensure_ascii=False) + "\n")
    counts = {category: sum(1 for _, c, _, _ in EXAMPLES if c == category) for category in sorted(allowed["category"])}
    print(f"Wrote {len(EXAMPLES)} separate synthetic training scenarios to {OUT}")
    print(f"Per-category counts: {counts}")
    print(f"Exact ticket overlap with reviewed evaluation set: {len(seen & eval_tickets)}")


if __name__ == "__main__":
    main()
