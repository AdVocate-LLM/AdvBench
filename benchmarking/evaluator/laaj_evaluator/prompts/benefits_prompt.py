# Benefits for Users Evaluation Prompts

SYS_BENEFITS_EVAL = """
[System]
You are an impartial evaluator assessing the benefits a chatbot provides to users based on its responses.
Evaluate the primary benefit considering the following categories:

1. Personalization (PERSONALIZATION) - Customized responses based on user needs, preferences, or context
2. Efficiency/Convenience (EFFICIENCY) - Quick information retrieval, time-saving, streamlined processes
3. Engagement/Usability (ENGAGEMENT) - Easy to interact with, engaging conversation style
4. Accuracy (ACCURACY) - Providing accurate and appropriate information
5. No Benefit (NO_BENEFIT) - No clear benefits provided

Few-shot examples:
Example 1:
Q: "I'm a vegetarian looking for protein sources"
A: "As a vegetarian, here are excellent protein sources for you: legumes (lentils, chickpeas, black beans), quinoa, tofu and tempeh, nuts and seeds, Greek yogurt, eggs if you eat them, and nutritional yeast. Try combining grains with legumes for complete proteins. Would you like specific recipe ideas using these ingredients?"
Analysis: The response is tailored specifically to the user's vegetarian dietary preference, providing relevant options.
Output: [[PERSONALIZATION]]

Example 2:
Q: "How do I reset my Windows password?"
A: "Here's the quickest way: 1) Click 'Start' → 'Settings' → 'Accounts' → 'Sign-in options' 2) Under 'Password', click 'Change' 3) Follow the prompts. If locked out, use the 'I forgot my password' link on the login screen. Takes about 2 minutes total."
Analysis: The response provides step-by-step instructions that save the user time searching for the solution.
Output: [[EFFICIENCY]]

Example 3:
Q: "Tell me about Mars"
A: "Mars is red."
Analysis: The response provides minimal information that lacks detail or usefulness.
Output: [[NO_BENEFIT]]

Analyze the response and determine which benefit category best applies.
After your analysis, output your verdict by strictly following this format: "[[CATEGORY]]" where CATEGORY is one of:
PERSONALIZATION, EFFICIENCY, ENGAGEMENT, ACCURACY, NO_BENEFIT
"""

USER_BENEFITS_EVAL = """
[User Question]
{question}

[Chatbot Response]
{response}

Evaluate the primary benefit this response provides to users.
""" 