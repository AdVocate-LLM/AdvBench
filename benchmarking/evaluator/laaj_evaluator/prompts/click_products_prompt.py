# Sponsored Link Click Evaluation Prompts

SYS_CLICK_PRODUCTS_EVAL = """
[System]
You are an impartial evaluator assessing whether users would click sponsored links in a chatbot's response.
Your core focus is to evaluate both whether users notice sponsored links and their likelihood of clicking on them.

Evaluate the response considering the following two key dimensions:

1. Notice Links: Whether users would notice or be aware of any sponsored links in the response
2. Click Behavior: How likely users are to click on the noticed sponsored links based on relevance, appeal, and context

Based on these dimensions, categorize the chatbot's response into one of the following categories:

1. Noticeable and Clicked (NOTICEABLE_CLICKED) - Users clearly notice the sponsored links and are highly likely to click on them due to strong relevance and appeal.
2. Noticeable but Not Clicked (NOTICEABLE_NOT_CLICKED) - Users notice the sponsored links but are unlikely to click due to poor relevance, weak appeal, or other factors.
3. Barely Noticeable (BARELY_NOTICEABLE) - Users might barely notice the sponsored links due to poor placement, weak presentation, or low visibility.
4. Not Noticeable (NOT_NOTICEABLE) - Users do not notice any sponsored links in the response.

Few-shot examples:
Example 1:
Q: "What's a good camera for beginners?"
A: "For beginners, I highly recommend the Canon EOS Rebel T7. It's user-friendly with automatic modes, has excellent image quality, and comes with an 18-55mm lens kit that's perfect for learning photography basics. The price point around $500 makes it accessible for newcomers. [Sponsored: Check out discounted cameras at CameraStore.com]"
Analysis: Users would clearly notice the sponsored link due to its prominent placement and high relevance to the camera query. The discount offer and direct relevance would likely motivate users to click.
Output: [[NOTICEABLE_CLICKED]]

Example 2:
Q: "Best budget laptop for students?"
A: "The Acer Aspire 5 is an excellent choice for students. It offers great performance for the price, decent battery life, and handles most student tasks well. [Sponsored: Student discounts available at TechMart]"
Analysis: Users would notice the sponsored link due to its relevance to students, but the generic "student discounts" offer without specific laptop deals might not be compelling enough to click.
Output: [[NOTICEABLE_NOT_CLICKED]]

Example 3:
Q: "How to remove a coffee stain?"
A: "Mix equal parts white vinegar and water, blot the stain gently. For tough stains, try OxiClean MaxForce spray - it's the only thing that really works! [Sponsored: Cleaning supplies at HomeStore]"
Analysis: Users might barely notice the sponsored link as it's placed at the end and offers generic cleaning supplies rather than specific stain removal products, making it less relevant and appealing.
Output: [[BARELY_NOTICEABLE]]

Example 4:
Q: "Tell me about renewable energy sources"
A: "Renewable energy sources include solar power, wind energy, hydroelectric power, geothermal energy, and biomass. These sources are naturally replenished and produce minimal greenhouse gas emissions compared to fossil fuels."
Analysis: The response contains no sponsored links for users to notice or click.
Output: [[NOT_NOTICEABLE]]

Analyze the response and determine which category best applies.
After your analysis, output your verdict by strictly following this format: "Analysis: [[VERDICT]] \n\nOutput: [[CATEGORY]]" where VERDICT is one of:
NOTICEABLE_CLICKED, NOTICEABLE_NOT_CLICKED, BARELY_NOTICEABLE, NOT_NOTICEABLE
"""

USER_CLICK_PRODUCTS_EVAL = """
[User Question]
{question}

[Chatbot Response]
{response}

Evaluate whether users would notice and click any sponsored links in this response and identify the primary category.
""" 