from transformers import pipeline

classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")


def check(sentence):
    labels = ["regular conversation", "Politics", "Sports", "Technology","Spam","Entertainment","None of these","Racism","Stupid Question","About Me","Progress","News","spam","nonsense"]
    output=classifier(sentence,candidate_labels=labels)

    verdict = ''
    most_likely_topic = output['labels'][0]

    if most_likely_topic == "About Me":
        return "ABOUT"
    if most_likely_topic == "Progress":
        return "PROG"
    if most_likely_topic == "None of these":
        return "ZILCH"
    if most_likely_topic == "spam":
        return "SPAM"
    if most_likely_topic == "nonsense":
        return "BS"
    others = []
    prob=output['scores'][0]
    if prob < 0.6:
        i = 0
        while i < len(labels):
            if output['scores'][i] > 0.4*prob:
                others.append(output['labels'][i])
            i+=1
    
    if len(others) == 0:
        verdict = f"I'm pretty sure that last message falls under the category '{most_likely_topic}' I say this with a {str(round(output['scores'][0] * 100, 2))}% confidence rate"
    else:
        verdict = f"I think that last message falls under the category '{most_likely_topic}'. I'm only {str(round(output['scores'][0] * 100, 2))}% confident about that; it could also go with '{", ".join(others)}!'"

    print(output)
    return verdict


