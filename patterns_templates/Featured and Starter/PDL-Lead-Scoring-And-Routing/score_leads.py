from datetime import datetime
from patterns import Stream, Table, Parameter

enriched_emails = Table("enriched_emails", "r")
scored_leads = Table("scored_leads", "w")
high_priority = Table("high_priority", "w")

high_priority_threshold = Parameter("high_priority_threshold", type=float, default=15.0)

def calc_score_size(size):
    if size is None:
        return 0
    return {
        "0-10": 0,
        "11-50": 3,
        "51-200": 5,
        "201-500": 10,
        "501-1000": 10,
    }.get(size, 20)


def calc_score_linkedin(linkedin_id):
    return 0 if linkedin_id is None else 5


def calc_score_country(country):
    return (
        10
        if country in ("united states", "australia", "canada", "united kingdom")
        else 0
    )


def score_lead(record, high_priority_threshold=15):
    return sum(
        [
            calc_score_country(record.get("job_company_location_country")),
            calc_score_size(record.get("job_company_size")),
            calc_score_linkedin(record.get("linkedin_id")),
        ]
    )


for record in enriched_emails.as_stream().consume_records():
    score = score_lead(record)
    record["score"] = score
    record["received_at"] = datetime.now()
    scored_leads.write(record)
    if score > high_priority_threshold:
        high_priority.write(record)
