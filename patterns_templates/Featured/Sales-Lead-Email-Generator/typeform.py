def _get_value(form, idx) -> str | list[str] | None:
    answers = form["form_response"]["answers"]
    if len(answers) <= idx:
        print("Out of range answer requested")
        return None
    
    answer = answers[idx]
    if answer["type"] == "email":
        return answer["email"]
    elif answer["type"] == "choice":
        if other := answer["choice"].get("other"):
            return other
        else:
            return answer["choice"]["label"]
    elif answer["type"] == "choices":
        labels = answer["choices"].get("labels", [])
        if other := answer["choices"].get("other", None):
            labels.append(other)
        return labels
        
    return None

def get_answer_for_question(form, keyword: str) -> str | None:
    keyword = keyword.lower()
    for idx, field in enumerate(form["form_response"]["definition"]["fields"]):
        if keyword in field["title"].lower():
            return _get_value(form, idx)

    return None

def get_answers(form, keywords) -> list:
    """Returns an answer for the first question containing each keyword in the list"""
    return [
        get_answer_for_question(form, keyword)
        for keyword in keywords
    ]