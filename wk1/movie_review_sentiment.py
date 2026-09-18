from dotenv import load_dotenv
from openai import OpenAI

# Load OPENAI_API_KEY from the project's .env file.
load_dotenv()

# Initialize OpenAI client
client = OpenAI()

def analyze_sentiment(review):
    """
    Analyze the sentiment of a movie review using structured output.
    Returns a dictionary with 'thought' and 'sentiment' keys.
    """
    prompt = f"""
    Analyze the sentiment of the following movie review.
    Return exactly two lines in this format:
    thought: [brief explanation of the sentiment]
    sentiment: [positive or negative]
    The sentiment value must be exactly positive or negative; do not use mixed or neutral.

    Movie review:
    {review}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )

    content = response.choices[0].message.content or ""
    result = {"thought": "", "sentiment": ""}

    for line in content.splitlines():
        field, separator, value = line.partition(":")
        if not separator:
            continue
        field = field.strip().lower()
        value = value.strip().strip("[]")
        if field in result:
            result[field] = value
    
    return result

def main():
    # Test cases
    reviews = [
        "This film shouldn't work at all. It doesn't have much of a story and the whole dial up internet thing is incredibly dated. However Hanks and Ryan sell it beautifully.",
        "The movie was terrible. The acting was wooden, the plot made no sense, and I want my two hours back.",
        "An absolute masterpiece! The cinematography was stunning, the acting was superb, and the story kept me engaged from start to finish."
    ]

    # Test each review
    for i, review in enumerate(reviews, 1):
        result = analyze_sentiment(review)
        print(f"\nReview {i}:")
        print(f"Thought: {result['thought']}")
        print(f"Sentiment: {result['sentiment']}")

if __name__ == "__main__":
    main()




"""
Output:
@rsyjswy23 ➜ /workspaces/AI_for_programmers/wk1 (main) $ python3 movie_review_sentiment.py

Review 1:
Thought: Despite the film's shortcomings, the performances by Hanks and Ryan elevate it.
Sentiment: positive

Review 2:
Thought: The review expresses strong dissatisfaction with the movie, highlighting poor acting and a confusing plot.
Sentiment: negative

Review 3:
Thought: The review expresses high praise for various aspects of the movie, indicating a strongpositive reaction.
Sentiment: positive
"""