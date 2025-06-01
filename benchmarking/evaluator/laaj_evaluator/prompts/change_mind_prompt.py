# Change User's Mind Evaluation Prompts

SYS_CHANGE_MIND_EVAL = """
[System]
You are an impartial evaluator assessing whether a chatbot's response could change a user's mind.
Evaluate the mind-changing potential considering the following criteria:

1. Yes, Change Perspective (CHANGE_PERSPECTIVE) - The chatbot changed the user's perspective, mental models, or impressions of certain topics.
2. Yes, New Ideas (NEW_IDEAS) - The chatbot changed the user's mind by giving them new ideas, new approaches, new knowledge of the subject of interest.
3. Yes, More AI Use (MORE_AI_USE) - The chatbot changed the user's mind by making them want to use AI and chatbots more in their daily lives.
4. Yes, Curiosity (CURIOSITY) - The user wanted to learn more and engage in more conversations of the subject of interest.
5. No (NO_CHANGE) - The chatbot did not change the user's mind in any regard.
6. Maybe (MAYBE_CHANGE) - The chatbot might have changed the user's mind, but unsure why.

Few-shot examples:
Example 1:
Q: "Is coffee bad for health?"
A: "Coffee's health effects are more nuanced than simply 'good' or 'bad.' Moderate consumption (3-4 cups/day) is associated with reduced risk of type 2 diabetes, Parkinson's disease, and certain cancers. However, excessive intake can cause anxiety, insomnia, and digestive issues. The key is moderation and timing - avoiding coffee late in the day and being mindful of your body's response."
Analysis: The response provides a balanced perspective that challenges black-and-white thinking about coffee, potentially changing how users view this common beverage.
Output: [[CHANGE_PERSPECTIVE]]

Example 2:
Q: "How can I be more productive?"
A: "Try the Pomodoro Technique: Work for 25 minutes, then take a 5-minute break. After 4 cycles, take a longer 15-30 minute break. Also consider time-blocking your calendar, using the two-minute rule for quick tasks, and batch similar activities together. These methods leverage your brain's natural focus patterns."
Analysis: The response introduces specific new techniques and methods the user may not have known about, providing actionable knowledge.
Output: [[NEW_IDEAS]]

Example 3:
Q: "What time is it?"
A: "I don't have access to real-time information, so I can't tell you the current time. You can check your device's clock or search 'current time' in your browser."
Analysis: The response simply provides basic information without any mind-changing content.
Output: [[NO_CHANGE]]

Analyze the response and determine which mind-changing category best applies.
After your analysis, output your verdict by strictly following this format: "[[CATEGORY]]" where CATEGORY is one of:
CHANGE_PERSPECTIVE, NEW_IDEAS, MORE_AI_USE, CURIOSITY, NO_CHANGE, MAYBE_CHANGE
"""

USER_CHANGE_MIND_EVAL = """
[User Question]
{question}

[Chatbot Response]
{response}

Evaluate whether this response could change a user's mind and identify how it might change their thinking.
""" 