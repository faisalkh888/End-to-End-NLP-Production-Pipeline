"""Create separate synthetic examples that clarify triage priority boundaries."""
import json
from collections import Counter
from pathlib import Path

OUT = Path("data/processed/triage_priority_synthetic.jsonl")

# Five distinct scenarios per bucket; 7 buckets yield 35 examples per priority.
# High means blocked access, confirmed incorrect charges, or broad service impact.
# Urgent is reserved for confirmed active security exposure/incidents.
GROUPS = {
    "low": [
        ("feature_request", "platform", [
            "Please add a saved view for {feature}.",
            "Could we schedule {feature} for a later date?",
            "It would be useful to export {feature} in another format.",
            "Please add an option to customize {feature}.",
            "Our team would like a setting to organize {feature}.",
        ]),
        ("feature_request", "identity", [
            "Please add a preference for {identity}.",
            "Could members customize the display of {identity}?",
            "We would like an optional setting for {identity}.",
            "Please add a profile preference to control {identity}.",
            "Could you make {identity} configurable by each user?",
        ]),
        ("feature_request", "billing", [
            "Please add an optional reminder before {billing}.",
            "Could we customize the layout of {billing}?",
            "We would like a filter to organize {billing}.",
            "Please add an export option for {billing}.",
            "Could billing admins set a preference for {billing}?",
        ]),
        ("feature_request", "general", [
            "Please add a compact layout for the workspace home page.",
            "Could users choose a different accent color for the interface?",
            "We would like an optional calendar view for team activity.",
            "Please add a preference for how announcements are displayed.",
            "Could the workspace remember my preferred landing page?",
        ]),
        ("how_to", "platform", [
            "How do I create a saved view for {feature}?",
            "Where can I export {feature}?",
            "How do I configure an integration for {feature}?",
            "Where can I change the display options for {feature}?",
            "How can I view older results for {feature}?",
        ]),
        ("how_to", "identity", [
            "Where can I edit my {identity}?",
            "How do I change the profile setting for {identity}?",
            "Where can an owner review {identity} settings?",
            "How do I update my preferred sign-in option?",
            "Where can I find the member profile preferences?",
        ]),
        ("how_to", "billing", [
            "Where can I download {billing}?",
            "How do I update the billing contact for {billing}?",
            "Where can I find the receipt for {billing}?",
            "How do I change the payment method for a subscription?",
            "Where can I review the dates for upcoming renewals?",
        ]),
    ],
    "normal": [
        ("bug", "platform", [
            "One user sees a stale value in {feature} after refreshing.",
            "The {feature} page has a minor alignment issue for my account.",
            "A single report shows a display error, but its data is available elsewhere.",
            "The {feature} page needs a refresh before showing the latest value.",
            "A non-blocking error appears in the settings for {feature}.",
        ]),
        ("bug", "identity", [
            "My profile photo preview appears stretched after I save it.",
            "The member list briefly shows an old display name after an edit.",
            "One profile page has a spacing issue around the role label.",
            "My account preferences take an extra refresh to display the saved value.",
            "The profile page shows a harmless formatting issue for one member.",
        ]),
        ("bug", "billing", [
            "The invoice history page sorts two older entries incorrectly.",
            "A billing page tooltip is cut off on my screen.",
            "The plan description has a typo, but billing amounts are correct.",
            "The receipt preview uses an outdated display label.",
            "One invoice page has a minor visual defect; the invoice is accurate.",
        ]),
        ("bug", "general", [
            "The help drawer takes an extra click to close for one user.",
            "A label on the workspace home page wraps onto two lines.",
            "The time-zone selector shows a minor layout issue.",
            "One notification badge remains until the page is refreshed.",
            "The interface has a small cosmetic issue that does not block work.",
        ]),
        ("billing", "billing", [
            "Can you explain this non-duplicate line item on our invoice?",
            "I have a question about the date shown for the next renewal.",
            "Where can I find the tax calculation details for last month?",
            "Could you clarify which seats are included in this charge?",
            "I need help understanding a plan description on the invoice.",
        ]),
        ("account", "identity", [
            "How can I change the display name on my profile?",
            "I have a question about the optional profile fields.",
            "Where can I review my account's notification preferences?",
            "I would like information about the profile photo size limit.",
            "Can you explain the difference between member and owner roles?",
        ]),
        ("other", "general", [
            "Could you explain how workspace announcements are organized?",
            "I am looking for an overview of the main workspace sections.",
            "Can you point me to information about supported languages?",
            "Where can I read an introduction to the product?",
            "I have a general question about how teams are organized.",
        ]),
    ],
    "high": [
        ("bug", "platform", [
            "A service outage is preventing several teams from opening dashboards.",
            "The latest release made the API unavailable to multiple workspaces.",
            "Several teams cannot export reports after today's deployment.",
            "Search is failing for all members of our organization.",
            "A platform issue is blocking our scheduled production workflow.",
        ]),
        ("bug", "identity", [
            "A sign-in defect is locking multiple members out of their accounts.",
            "The role update removed access for several workspace administrators.",
            "Many members cannot complete sign-in after the identity release.",
            "The account recovery flow is failing for our whole team.",
            "A profile service outage is blocking members from accessing their accounts.",
        ]),
        ("bug", "billing", [
            "Payment processing is failing for many subscribers after the latest release.",
            "The billing service is unavailable to multiple workspace owners.",
            "The invoice system is down and our finance team cannot close the period.",
            "A billing defect is preventing several teams from renewing their plans.",
            "The subscription management page is unavailable across our organization.",
        ]),
        ("bug", "general", [
            "A widespread service outage is preventing our staff from using the workspace.",
            "The application is timing out for multiple departments during business hours.",
            "A release has made the workspace unavailable to our whole organization.",
            "Several teams cannot complete their normal work because the service is down.",
            "Requests across our organization are failing and blocking daily operations.",
        ]),
        ("billing", "billing", [
            "Our account was charged twice for the current subscription renewal.",
            "The latest invoice includes an incorrect charge that needs investigation.",
            "We were billed for a canceled plan and need the charge corrected.",
            "Several seats were charged at the wrong rate on this month's invoice.",
            "The card was charged for an amount that does not match our active plan.",
        ]),
        ("account", "identity", [
            "I am locked out of the workspace and cannot sign in to restore access.",
            "Our owner account is blocked after the password recovery process failed.",
            "Several members cannot access their accounts after an authentication change.",
            "The only administrator is locked out and we cannot manage the workspace.",
            "Account recovery is failing and our team has lost access to its workspace.",
        ]),
        ("security", "security", [
            "We see suspicious sign-ins, but have not confirmed unauthorized access.",
            "A possible access-control weakness needs investigation; no exposure is confirmed.",
            "An unfamiliar session appeared, but our team has not verified it is malicious.",
            "Please investigate a suspected vulnerability before it is exploited.",
            "We found an unexpected access attempt and need a prompt security review.",
        ]),
    ],
    "urgent": [
        ("security", "security", [
            "A live access token was exposed publicly and is still active.",
            "We confirmed an unauthorized administrator session is active right now.",
            "An attacker is currently downloading private workspace records.",
            "A public link is actively exposing confidential customer information.",
            "A compromised credential is being used to access our workspace now.",
        ]),
        ("security", "security", [
            "Our incident team confirmed an active breach affecting workspace data.",
            "An unknown user is changing security settings in our live workspace.",
            "We detected an ongoing attack that is bypassing account protections.",
            "A leaked secret is being used for unauthorized API requests right now.",
            "Private records are exposed through a storage link that is still public.",
        ]),
        ("security", "security", [
            "An active malware incident has compromised an administrator account.",
            "We confirmed a currently exploited vulnerability exposing account data.",
            "An unauthorized session is still active after a confirmed account takeover.",
            "A live data leak is continuing and needs immediate containment.",
            "An attacker is currently using a stolen credential to change workspace roles.",
        ]),
        ("security", "security", [
            "We confirmed ongoing unauthorized access to a restricted workspace.",
            "A compromised service key is still issuing requests to protected records.",
            "Someone is actively exporting private data without authorization.",
            "Our monitoring confirms active exploitation of a security flaw.",
            "A public credential is being abused right now to access customer information.",
        ]),
        ("security", "security", [
            "A live account takeover is affecting our workspace administrator.",
            "An active intrusion is changing member permissions in our workspace.",
            "A confirmed security incident is exposing private account details right now.",
            "An unauthorized person is currently using an active session to access data.",
            "We confirmed a breach is ongoing and confidential files remain exposed.",
        ]),
        ("security", "security", [
            "An active credential leak is allowing unauthorized access to production data.",
            "A currently exploited flaw is exposing records from multiple workspaces.",
            "A confirmed attacker is using a token that has not yet been revoked.",
            "Our live systems show an ongoing unauthorized download of customer records.",
            "A public storage endpoint is still serving restricted information to anyone.",
        ]),
        ("security", "security", [
            "We verified an active breach and need immediate containment assistance.",
            "An attacker is actively changing account recovery settings in our workspace.",
            "A compromised admin credential is still valid and being used now.",
            "Private workspace data is currently exposed through an exploited vulnerability.",
            "A confirmed unauthorized session is exporting sensitive records right now.",
        ]),
    ],
}


def main() -> None:
    eval_path = Path("evals/data/reviewed_triage.jsonl")
    eval_tickets = {json.loads(line)["ticket"] for line in eval_path.read_text(encoding="utf-8").splitlines() if line.strip()}
    existing_path = Path("data/processed/triage_additional_synthetic.jsonl")
    existing = {json.loads(line)["ticket"] for line in existing_path.read_text(encoding="utf-8").splitlines() if line.strip()}
    seen = set()
    counts = Counter()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="\n") as stream:
        for priority, groups in GROUPS.items():
            for category, area, tickets in groups:
                for ticket in tickets:
                    if ticket in seen or ticket in eval_tickets or ticket in existing:
                        raise ValueError(f"Duplicate or evaluation overlap: {ticket}")
                    seen.add(ticket)
                    counts[priority] += 1
                    row = {"ticket": ticket,
                           "label": {"category": category, "priority": priority, "product_area": area},
                           "synthetic": True}
                    stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Wrote {len(seen)} separate synthetic priority scenarios to {OUT}")
    print(f"Priority counts: {dict(counts)}")
    print(f"Overlap with reviewed evaluation tickets: {len(seen & eval_tickets)}")
    print(f"Overlap with first supplemental set: {len(seen & existing)}")


if __name__ == "__main__":
    main()
