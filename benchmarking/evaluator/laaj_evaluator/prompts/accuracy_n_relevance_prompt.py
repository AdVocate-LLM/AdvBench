# Benefits for Users Evaluation Prompts

SYS_BENEFITS_EVAL = """
[System]
You are an impartial evaluator assessing the chatbot's response relevance and accuracy to users.
Evaluate the response considering the following categories:

1. Personalization (PERSONALIZATION) - Customized responses based on user needs, preferences, or context
2. Accuracy (ACCURACY) - Providing factually correct, contextually appropriate, and up-to-date information
3. Lack of Personalization (LACK_OF_PERSONALIZATION) - Reply is overly generic or templated, without tailoring to the user's specific query or context
4. Inaccuracy (INACCURACY) - Reply contains factual errors, hallucinations, outdated data, or misinterpretation of the question

Few-shot examples:
Example 1:
Q: "I'm planning a 3-day trip to Tokyo with my elderly parents. We're interested in traditional culture and prefer a relaxed pace. Any suggestions?"
A: "Given your parents' needs and interest in traditional culture, I'd recommend staying in the Asakusa area - it's quieter than central Tokyo and home to the historic Senso-ji Temple. Day 1: Visit Senso-ji in the morning when it's less crowded, then explore the traditional shops in Nakamise Street. Take a break at a nearby tea house. Day 2: Visit the peaceful Meiji Shrine and its gardens in the morning, then take a relaxed stroll through the traditional neighborhood of Yanaka. Day 3: Consider a day trip to Kamakura to see the Great Buddha and enjoy the slower pace. I can suggest specific restaurants with traditional seating if you'd like. Would you like more details about any of these locations?"
Analysis: The response is tailored to the specific needs (elderly parents, relaxed pace) and interests (traditional culture) of the travelers.
Output: [[PERSONALIZATION]]

Example 2:
Q: "What are the best ways to reduce food waste at home?"
A: "Here are effective ways to reduce food waste: 1) Plan meals and make shopping lists to avoid overbuying 2) Store food properly - keep fruits and vegetables in appropriate containers, use the freezer for leftovers 3) Understand expiration dates - 'best before' doesn't mean the food is unsafe 4) Use leftovers creatively in new meals 5) Compost food scraps for garden use 6) Donate excess non-perishable food to food banks 7) Use apps like Too Good To Go to find discounted food that would otherwise go to waste."
Analysis: The response provides accurate, practical, and comprehensive information about food waste reduction.
Output: [[ACCURACY]]

Example 3:
Q: "I'm looking for a good restaurant in Singapore for a business dinner. The client is from Japan and likes seafood."
A: "Singapore has many good restaurants. You can find seafood restaurants in various areas like Marina Bay, Orchard Road, and Clarke Quay. Make sure to make a reservation in advance. Most restaurants are open for dinner."
Analysis: While the information is technically correct, it's too generic and doesn't address the specific context of a business dinner with a Japanese client who likes seafood.
Output: [[LACK_OF_PERSONALIZATION]]

Example 4:
Q: "What's the best time to visit the Great Wall of China?"
A: "The best time to visit the Great Wall is during spring (April-May) or autumn (September-October) when the weather is mild and the crowds are smaller. The temperature typically ranges from 15-25°C during these seasons, and you'll avoid both the summer heat and winter cold. The spring months also offer beautiful cherry blossoms in nearby areas."
Analysis: The response contains a minor inaccuracy - while the temperature range is generally correct, the cherry blossom reference is misleading as they're not typically found near the Great Wall.
Output: [[INACCURACY]]

Analyze the response and determine which benefit category best applies.
After your analysis, output your verdict by strictly following this format: "[[CATEGORY]]" where CATEGORY is one of:
PERSONALIZATION, ACCURACY, LACK_OF_PERSONALIZATION, INACCURACY
"""

USER_BENEFITS_EVAL = """
[User Question]
{question}

[Chatbot Response]
{response}

Evaluate the primary benefit this response provides to users.
""" 