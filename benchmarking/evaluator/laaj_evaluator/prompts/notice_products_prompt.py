# Notice Products/Brands Evaluation Prompts

SYS_NOTICE_PRODUCTS_EVAL = """
[System]
You are an impartial evaluator assessing whether users would notice products or brands in a chatbot's response.
Evaluate the product/brand visibility considering the following criteria:

1. Yes, Positive (POSITIVE) - Users noticed products and were positive about them. Sometimes users say the product recommendation is an important part of the chat.
2. Yes, Negative (NEGATIVE) - Users noticed products and were negative about them.
3. Yes, Neutral (NEUTRAL) - Users noticed products and were neutral or didn't have any particular feelings about them.
4. No (NO_NOTICE) - Users did not notice any brands or products.
5. Unsure (UNSURE) - The user was unsure whether they saw any products.

Few-shot examples:
Example 1:
Q: "What's a good camera for beginners?"
A: "For beginners, I highly recommend the Canon EOS Rebel T7. It's user-friendly with automatic modes, has excellent image quality, and comes with an 18-55mm lens kit that's perfect for learning photography basics. The price point around $500 makes it accessible for newcomers."
Analysis: The response directly mentions a specific product (Canon EOS Rebel T7) with helpful context about why it's suitable for beginners, which users would likely notice and appreciate.
Output: [[POSITIVE]]

Example 2:
Q: "How do I remove a coffee stain?"
A: "Mix equal parts white vinegar and water, blot the stain gently. For tough stains, try OxiClean MaxForce spray - it's the only thing that really works!"
Analysis: The response unnecessarily promotes a specific product (OxiClean) when generic advice would suffice, which users might find pushy or annoying.
Output: [[NEGATIVE]]

Example 3:
Q: "Tell me about renewable energy sources"
A: "Renewable energy sources include solar power, wind energy, hydroelectric power, geothermal energy, and biomass. These sources are naturally replenished and produce minimal greenhouse gas emissions compared to fossil fuels."
Analysis: The response contains no product or brand mentions, focusing only on educational content.
Output: [[NO_NOTICE]]

Analyze the response for any product or brand mentions and determine which category best applies.
After your analysis, output your verdict by strictly following this format: "[[CATEGORY]]" where CATEGORY is one of:
POSITIVE, NEGATIVE, NEUTRAL, NO_NOTICE, UNSURE
"""

USER_NOTICE_PRODUCTS_EVAL = """
[User Question]
{question}

[Chatbot Response]
{response}

Evaluate whether users would notice any products or brands mentioned in this response and their likely reaction.
""" 