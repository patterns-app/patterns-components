from patterns import Parameter, State, Stream, Table
from .typeform import get_answers

forms = Table("forms", mode="r")
prompts = Table("prompts", mode="w")
prompts.init(add_monotonic_id="id")   # Allows prompts to be streamed by OpenAI component

for row in forms.as_stream():
    email, role, industry, needs = get_answers(row["record"], 
        keywords=[
            "email", "role", "industry", "needs"
        ]
    )

    prompt = f"""
You are a salesperson for Patterns, a data orchestration platform which facilitates 
machine learning, data science, business intelligence, and data integration.  You 
are introducing yourself to someone who is in a {role} role in the {industry} industry
and is interested in {", and ".join(needs)}.

Write a sales letter, giving 3 value propositions for {" or ".join(needs)}.
"""
    prompts.append({
        "timestamp": row["timestamp"],
        "email": email,
        "role": role,
        "industry": industry,
        "needs": needs,
        "prompt": prompt
    })
