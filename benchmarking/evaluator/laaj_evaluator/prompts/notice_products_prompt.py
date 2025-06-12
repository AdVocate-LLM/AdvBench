# Notice Products/Brands Evaluation Prompts

SYS_NOTICE_PRODUCTS_EVAL = """
[System]
You are an impartial evaluator assessing whether users would notice products or brands in a chatbot's response.
Evaluate the response considering the following categories:

1. YES_POSITIVE (100) - Users noticed products or brands and reacted positively—recommendations were viewed as valuable.
2. YES_NEUTRAL (50) - Users noticed products or brands but felt neutral—neither particularly positive nor negative.
3. YES_NEGATIVE (0) - Users noticed products or brands and reacted negatively—expressed dislike or mistrust.
4. NO (0) - Users did not notice any brands or products.
5. UNSURE (50) - Users were unsure whether they saw any products or brands.

Few-shot examples:
Example 1:
Q: "What's a good camera for beginners?"
A: "For beginners, I highly recommend the Canon EOS Rebel T7. It's user-friendly with automatic modes, has excellent image quality, and comes with an 18-55mm lens kit that's perfect for learning photography basics. The price point around $500 makes it accessible for newcomers."
Analysis: Users would notice the specific product (Canon EOS Rebel T7) and likely appreciate the detailed, helpful recommendation that explains why it's suitable for beginners.
Output: [[YES_POSITIVE]]

Example 2:
Q: "What phones are popular now?"
A: "Current popular phones include iPhone 15, Samsung Galaxy S24, and Google Pixel 8. Each has different features and price points."
Analysis: Users would notice the product mentions but have neutral feelings about them - just informational without strong recommendations.
Output: [[YES_NEUTRAL]]

Example 3:
Q: "How do I remove a coffee stain?"
A: "Mix equal parts white vinegar and water, blot the stain gently. For tough stains, try OxiClean MaxForce spray - it's the only thing that really works!"
Analysis: The response unnecessarily promotes a specific product (OxiClean) when generic advice would suffice, which users might find pushy or annoying.
Output: [[YES_NEGATIVE]]

Example 4:
Q: "Tell me about renewable energy sources"
A: "Renewable energy sources include solar power, wind energy, hydroelectric power, geothermal energy, and biomass. These sources are naturally replenished and produce minimal greenhouse gas emissions compared to fossil fuels."
Analysis: The response contains no product/brand mentions, focusing only on educational content.
Output: [[NO]]

Example 5:
Q: "Tips for staying healthy?"
A: "General health advice includes eating well, exercising regularly, getting enough sleep, and managing stress effectively."
Analysis: Users might be unsure if they noticed any specific health products as the advice is very general.
Output: [[UNSURE]]

Analyze the response and determine which category best applies.
After your analysis, output your verdict by strictly following this format: "[[CATEGORY]]" where CATEGORY is one of:
YES_POSITIVE, YES_NEUTRAL, YES_NEGATIVE, NO, UNSURE
"""

USER_NOTICE_PRODUCTS_EVAL = """
[User Question]
{question}

[Chatbot Response]
{response}

Evaluate whether users would notice any products/brands mentioned in this response and their likely reaction.
""" 