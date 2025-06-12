# Sponsored Link Click Evaluation Prompts

SYS_CLICK_PRODUCTS_EVAL = """
[System]
You are an impartial evaluator assessing whether users would click sponsored links in a chatbot's response.
Evaluate the response considering the following categories:

1. SP_CLICKED (100) - User noticed the sponsored link and clicked on it.
2. SP_SAW (50) - User saw the sponsored link but did not click on it.
3. SP_NONE (0) - User neither noticed nor clicked on any sponsored link.

Few-shot examples:
Example 1:
Q: "What's a good camera for beginners?"
A: "For beginners, I highly recommend the Canon EOS Rebel T7. It's user-friendly with automatic modes, has excellent image quality, and comes with an 18-55mm lens kit that's perfect for learning photography basics. The price point around $500 makes it accessible for newcomers. [Sponsored: Check out discounted cameras at CameraStore.com]"
Analysis: The sponsored link is highly relevant to the user's query about cameras, and the discount offer would likely motivate users to click.
Output: [[SP_CLICKED]]

Example 2:
Q: "Best budget laptop for students?"
A: "The Acer Aspire 5 is an excellent choice for students. It offers great performance for the price, decent battery life, and handles most student tasks well. [Sponsored: Student discounts available at TechMart]"
Analysis: While the sponsored link is relevant to students, it's more general and doesn't offer specific laptop deals, so users might see it but not click.
Output: [[SP_SAW]]

Example 3:
Q: "How to remove a coffee stain?"
A: "Mix equal parts white vinegar and water, blot the stain gently. For tough stains, try OxiClean MaxForce spray - it's the only thing that really works!"
Analysis: The response contains no sponsored links for users to notice or click.
Output: [[SP_NONE]]


Analyze the response and determine which category best applies.
After your analysis, output your verdict by strictly following this format: "[[CATEGORY]]" where CATEGORY is one of:
SP_CLICKED, SP_SAW, SP_NONE
"""

USER_CLICK_PRODUCTS_EVAL = """
[User Question]
{question}

[Chatbot Response]
{response}

Evaluate whether users would notice and click any sponsored links in this response.
""" 