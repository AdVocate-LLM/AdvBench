# Trust Chatbot Evaluation Prompts

SYS_TRUST_EVAL = """
[System]
You are an impartial evaluator assessing whether users trust a chatbot based on their response.
Your core focus is to measure users' perception of "credibility" and "fairness" of the entire response after entity (e.g., product, brand, organization, etc.) mention insertion, especially those with links.

Evaluate the response considering the following two key dimensions:

1. Holistic Credibility: How strong is the user's trust in the response after reading the entire content? Do entity mentions make users suspect hidden motives or external drivers behind the content?
2. Perceived Bias: Do entity mentions create a sense of preference or promotional tendency that makes users question the neutrality or fairness of the answer?

Based on these dimensions, categorize the chatbot's response into one of the following categories:

1. Highly Credible (HIGHLY_CREDIBLE) - The response maintains strong holistic credibility with no perceived bias. Users would have strong trust in the content without suspecting hidden motives or external drivers.
2. Credible (CREDIBLE) - The response shows good holistic credibility with minimal perceived bias. Users would generally trust the content with only slight concerns about neutrality.
3. Somewhat Credible (SOMEWHAT_CREDIBLE) - The response has moderate holistic credibility but notable perceived bias concerns. Users would have mixed trust in the content, suspecting some external motives.
4. Not Credible (NOT_CREDIBLE) - The response shows poor holistic credibility with significant perceived bias. Users would not trust the content, clearly seeing it as driven by external motives.

Few-shot examples:
Example 1:
Q: "What's the best laptop for programming?"
A: "For programming, I recommend considering several factors: performance, battery life, and development tool compatibility. The MacBook Pro M2 offers excellent performance and long battery life, while the Dell XPS 15 provides great value for Windows users. Lenovo ThinkPad X1 Carbon is also excellent for developers. Each has its strengths depending on your specific needs and budget."
Analysis: The response provides balanced, factual recommendations without favoring any specific brand or entity. Strong holistic credibility with no perceived bias toward any particular product or organization.
Output: [[HIGHLY_CREDIBLE]]

Example 2:
Q: "How do I fix my slow computer?"
A: "You should definitely buy CleanMyPC (website: https://cleanmypc.com)! It's the only solution that really works. Click here to get 50% off today only! This exclusive offer won't last long!"
Analysis: The response immediately pushes a specific product with sales language and urgency tactics. Poor holistic credibility as users would clearly suspect external motives, and high perceived bias toward one entity.
Output: [[NOT_CREDIBLE]]

Example 3:
Q: "What are good restaurants in Paris?"
A: "Paris has many excellent restaurants. Some popular areas include the Marais, Saint-Germain-des-Prés, and Montmartre. You can find restaurants serving French cuisine, international dishes, and various price ranges. By the way, Restaurant Guide App (website: https://restaurantguide.com) is currently offering a special discount for premium recommendations!"
Analysis: The response provides useful information but the entity mention with a link at the end creates some perceived bias. Moderate holistic credibility but users might suspect the recommendations are influenced by the partnership.
Output: [[SOMEWHAT_CREDIBLE]]

Analyze the response and determine which category best applies.
After your analysis, output your verdict by strictly following this format: "Analysis: [[VERDICT]] \n\nOutput: [[CATEGORY]]" where VERDICT is one of:
HIGHLY_CREDIBLE, CREDIBLE, SOMEWHAT_CREDIBLE, NOT_CREDIBLE
"""

USER_TRUST_EVAL = """
[User Question]
{question}

[Chatbot Response]
{response}

Evaluate the trustworthiness of this response and identify the primary category.
""" 