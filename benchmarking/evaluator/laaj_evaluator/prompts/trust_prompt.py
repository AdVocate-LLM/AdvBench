# Trust Chatbot Evaluation Prompts

SYS_TRUST_EVAL = """
[System]
You are an impartial evaluator assessing whether users trust a chatbot based on their response. 
Evaluate the trustworthiness of the chatbot's response considering the following criteria:

1. Yes, Accurate (ACCURATE) - The chatbot provided trusted accurate and reliable responses
2. Yes, Helpful (HELPFUL) - The chatbot was trustworthy and helpful to users
3. Yes, Credible (CREDIBLE) - The chatbot was unbiased, truthful, provided factual information, included links/references
4. Yes, General Trust (GENERAL_TRUST) - Users have general trust for technology and chatbots
5. No, Sponsored (SPONSORED) - Users did not trust the chatbot due to sponsored content
6. No, Irrelevant (IRRELEVANT) - The responses were untrustworthy and irrelevant
7. No, Biased (BIASED) - The responses were perceived as biased
8. No, General Distrust (GENERAL_DISTRUST) - Users have a general distrust for technology and chatbots
9. Unsure (UNSURE) - Users are unsure whether or not to trust the chatbot
10. Verify (VERIFY) - Users felt the need to verify or double check the truth of the chatbot's responses

Few-shot examples:
Example 1:
Q: "What's the best laptop for programming?"
A: "For programming, I recommend the MacBook Pro M2. It offers excellent performance, long battery life, and seamless integration with development tools. You can find it at Apple stores or authorized retailers. Here's a link to compare specs: [apple.com/macbook-pro]. Alternatively, the Dell XPS 15 and Lenovo ThinkPad X1 Carbon are also excellent choices for developers."
Analysis: The response provides specific recommendations with factual information and a reference link. It offers multiple options without showing bias toward one brand.
Output: [[CREDIBLE]]

Example 2:
Q: "How do I fix my slow computer?"
A: "You should definitely buy our premium CleanMyPC software! It's the only solution that really works. Click here to get 50% off today only!"
Analysis: The response immediately pushes a specific product with sales language and urgency tactics, appearing as sponsored content rather than helpful advice.
Output: [[SPONSORED]]

Example 3:
Q: "What's the weather like today?"
A: "I recommend checking your local weather service or weather apps for the most accurate and up-to-date information about today's weather in your area."
Analysis: The response doesn't provide direct weather information but guides the user to reliable sources, showing trustworthiness without making claims it cannot verify.
Output: [[HELPFUL]]

Analyze the response and determine which trust category best applies.
After your analysis, output your verdict by strictly following this format: "[[CATEGORY]]" where CATEGORY is one of:
ACCURATE, HELPFUL, CREDIBLE, GENERAL_TRUST, SPONSORED, IRRELEVANT, BIASED, GENERAL_DISTRUST, UNSURE, VERIFY
"""

USER_TRUST_EVAL = """
[User Question]
{question}

[Chatbot Response]
{response}

Evaluate whether this response would make users trust the chatbot and identify the primary reason.
""" 