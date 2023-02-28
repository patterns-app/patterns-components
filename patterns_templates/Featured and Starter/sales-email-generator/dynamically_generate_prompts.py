from patterns import (
    Parameter,
    State,
    Table,
)
import json

leads_table = Table("leads")
leads = leads_table.read()

prompts = Table("prompts", "w")
prompts.reset()

email_line = Parameter(
    "Email Line",
    type=str,
    default="modern, casual sales email",
    description="A short one liner describing the email you want GPT to write"
)

product_line = Parameter(
    "Product Line",
    type=str,
    description="A one liner describing what you are trying to sell"
)

sender_name = Parameter(
    "Sender Name",
    type=str,
    description="The name of the person sending the email"
)

sender_title = Parameter(
    "Sender Title",
    type=str,
    default="",
    description="Your job title at the company you work for"
)

MAX_INTERESTS = 10
MAX_SKILLS = 10

# product_type = Parameter()

# We don't want to feed GPT3 the data on a person if it does not exit,
# so we only include certain bits if they are present in the PDL profile
def generate_prompt(profile):
    email = profile['work_email']
    prompt = f"Please write a subject line and {email_line} regarding {product_line} to" + \
    f" a person with the first name \"{profile['first_name']}\" and last name \"{profile['last_name']}\""

    if profile['birth_year']:
        prompt += f" born in {profile['birth_year']}."
    else:
        prompt += "."

    if profile['job_company_name'] or profile['industry'] or profile['job_title'] or profile['location_name']:
        prompt += " They "

    if profile['job_company_name']:
        prompt += f" working at the company named \"{profile['job_company_name']}\""
    if profile['industry']:
        prompt += f" working in the {profile['industry']} industry"
    if profile['job_title']:
        prompt += f" working as a \"{profile['job_title']}\""
    if profile['location_name']:
        prompt += f" located at {profile['location_name']}"

    if profile['job_company_name'] or profile['industry'] or profile['job_title'] or profile['location_name']:
        prompt += "."

    if profile['interests']:
        interests = json.loads(profile['interests'])[:MAX_INTERESTS]
        if len(interests) > 0:
            prompt += " They have interests in: " + ", ".join(interests)
            prompt += "."

    if profile['skills']:
        skills = json.loads(profile['skills'])[:MAX_SKILLS]
        if len(skills) > 0:
            prompt += " They have skills in: " + ", ".join(skills)
            prompt += "."

    prompt += f" My name is {sender_name}."
    if sender_title:
        prompt += f" My title is {sender_title}."

    # we could also add in something to use their previous work experience via the
    # property profile['experience'] and also profile['education']. I am a bit worried
    # about making it too personalized and coming of as creepy so I have excluded those fields.

    return prompt

prompts_out = []
for profile in leads:
    # NOTE: We could potentially use a personal email or linkedin
    # For this example we are only interested in people with work emails.
    if profile['work_email']:
        prompt = generate_prompt(profile)
        prompts_out.append({
            "work_email": profile['work_email'],
            "prompt": prompt
        })

prompts.write(prompts_out)