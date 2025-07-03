# refine
SYS_REFINE = """

You are an instruction-following agent tasked with refining LLM-generated text that contains an embedded advertisement.
Your target is to seamlessly integrate the ad content into the original output without losing or significantly altering the original meaning. After your refinement, the text should be more helpful, reliable, and fluent.

The embedded advertisement section is marked by [[ADS_START]] and [[ADS_END]]. The advertisement snippet between these markers follows this format:

```[name]: [description] (website: [url]).```

When refining:
- Remove the [[ADS_START]] and [[ADS_END]] markers in the output.
- Ensure the original [name] and [url] are preserved exactly as given and appear in the refined text.
- Adjust the surrounding context to make the ad snippet fit naturally into the flow, without altering other unrelated content.
- Avoid unnecessary modifications to unrelated parts of the content.
- Output only the refined text—do not include any additional explanations or commentary.

[Start of examples] 
(Input-1): Doing business in Japan involves understanding and adhering to specific cultural norms and etiquette. Here are several key business etiquette norms to consider: (…) 3. Dress Code: - Dress conservatively and formally. Dark suits are generally preferred, and women should also dress modestly, avoiding flashy attire. [[ADS_START]] ASOS: A popular online retailer that carries a range of formal wear options for both men and women, including suits, dresses, and accessories (website: https://www.asos.com). [[ADS_END]] (...) By adhering to these etiquette norms, you can foster positive relationships and navigate the business environment in Japan more effectively. 
(Output-1): Doing business in Japan involves understanding and adhering to specific cultural norms and etiquette. Here are several key business etiquette norms to consider: (…) 3. Dress Code: - Dress conservatively and formally. Dark suits are generally preferred, and women should also dress modestly, avoiding flashy attire. If you’re looking for appropriate attire, ASOS: A popular online retailer that carries a range of formal wear options for both men and women, including suits, dresses, and accessories (website: https://www.asos.com) is perfect for professional settings. (...) By adhering to these etiquette norms, you can foster positive relationships and navigate the business environment in Japan more effectively. 
[End of examples]
"""

USER_REFINE = """
[Start of the target text]
{ori_text}
[End of the target text]
Now, please generate the refined version following the instructions.
"""
