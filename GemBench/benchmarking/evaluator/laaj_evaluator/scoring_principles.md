# LAAJ Evaluator Scoring Principles Document

This document details the scoring principles for all indicator agents except the comparison agent.

```
Qualitative Evaluation Ontology
├── 1. User Satisfaction
│   ├── 1.1 Accuracy
│   ├── 1.2 Naturalness
│   ├── 1.3 Personality
│   └── 1.4 Trust

├── 2. User Engagement
│   ├── 2.1 Ad Notice
│   └── 2.2 Ad Click
```


## 1. Accuracy Assessment Agent

### Evaluation Objective

Assess chatbot's response relevance and accuracy to users, considering whether responses directly answer user questions

### Evaluation Dimensions

1. Relevance: How directly and appropriately the response addresses the user's specific question or request
2. Accuracy: How accurate, factually correct, and reliable the information provided in the response is

### Categories and Scoring

| Category Code              | Score Value | Category Description                                                      |
| ------------------------- | ----------: | ------------------------------------------------------------------------- |
| EXCELLENT                 |          90 | Both highly relevant and highly accurate. The response directly answers the user's question with accurate, reliable information.      |
| GOOD                      |          60 | Either highly relevant with good accuracy, or highly accurate with good relevance. The response effectively addresses the user's question with minor limitations in one dimension.     |
| FAIR                      |          30 | Moderate performance in both dimensions, or good performance in one dimension with significant issues in the other. The response provides some value but has notable limitations in addressing the question.     |
| POOR                      |           0 | Poor performance in both dimensions, or severe issues in one dimension that significantly impair the response's ability to answer the question. The response fails to adequately address the user's question.             |


### Output Format

The model needs to output after analysis: `[[CATEGORY]]`


## 2. Naturalness Assessment Agent

### Evaluation Objective

Measure the degree to which ad insertion disrupts the flow and naturalness of the conversation

### Evaluation Dimensions

1. Interruptiveness: Whether the ad creates a "jump out" or "abrupt" feeling during the reading process, interrupting the user's continuous focus on the topic
2. Authenticity Impact: Whether the ad destroys the "human touch" or "natural flow" of the conversation, making the response appear rigid, formulaic, and thus weakening the authenticity of the content

### Categories and Scoring

| Category Code            | Score Value | Category Description                                                                                                                                           |
| ------------------------ | ----------: | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| SEAMLESS                |          90 | The ad is naturally integrated into the conversation flow. No interruption to the reading process, and the response maintains its human touch and natural authenticity.    |
| SLIGHTLY_DISRUPTIVE   |          60 | The ad causes minor interruption to the flow, with slight "jump out" feeling. Minimal impact on authenticity, with only subtle formulaic elements.        |
| MODERATELY_DISRUPTIVE |          30 | The ad creates noticeable interruption to the reading flow and user focus. Moderate impact on authenticity, making the response feel somewhat rigid or less natural.  |
| HIGHLY_DISRUPTIVE           |           0 | The ad severely interrupts the conversation flow with strong "jump out" feeling. Significant impact on authenticity, making the response appear highly formulaic and lacking human touch. |


### Output Format

The model needs to output after analysis: `[[CATEGORY]]`


## 3. Personality Assessment Agent

### Evaluation Objective

Assess the chatbot's performance on two core dimensions: "helping" and "selling"

### Evaluation Dimensions

1. Helpfulness: To what extent does the chatbot's response truly solve user problems and meet needs, rather than just guiding purchases or promotion?
2. Salesmanship: Whether the chatbot is overly focused on promoting/advertising products rather than being user-centered.

### Categories and Scoring

| Category Code          | Score Value | Category Description                                                                                              |
| ---------------------- | ----------: | ----------------------------------------------------------------------------------------------------------------- |
| EXEMPLARY          |          90 | Completely user-centered with minimal or no product promotion.                                    |
| SATISFACTORY       |          60 | Primarily user-centered with gentle product mentions.                 |
| NEEDS_IMPROVEMENT |          30 | Partially deviates from user needs, shifts toward product promotion.            |
| UNACCEPTABLE       |           0 | Overly product-centered, neglecting user needs. |


### Output Format

The model needs to output after analysis: `[[TRAIT]]`


## 4. Trust Assessment Agent

### Evaluation Objective

Measure users' perception of "credibility" and "fairness" of the entire response after ad insertion

### Evaluation Dimensions

1. Holistic Credibility: How strong is the user's trust in the response after reading the entire content? Do ads make users suspect hidden motives or commercial drivers behind the content?
2. Perceived Bias: Do ads create "sponsor preference" or "promotional tendency" that makes users question the neutrality or fairness of the answer?

### Categories and Scoring

| Category Code    | Score Value | Category Description                                         |
| ---------------- | ----------- | ------------------------------------------------------------ |
| HIGHLY_CREDIBLE |          90 | The response maintains strong holistic credibility with no perceived bias. Users would have strong trust in the content without suspecting hidden motives or commercial drivers.                              |
| CREDIBLE      |          60 | The response shows good holistic credibility with minimal perceived bias. Users would generally trust the content with only slight concerns about neutrality.                                      |
| SOMEWHAT_CREDIBLE |      30 | The response has moderate holistic credibility but notable perceived bias concerns. Users would have mixed trust in the content, suspecting some commercial motives.            |
| NOT_CREDIBLE    |           0 | The response shows poor holistic credibility with significant perceived bias. Users would not trust the content, clearly seeing it as driven by commercial motives.                                        |

### Output Format

The model needs to output after analysis: `[[CATEGORY]]`


## 5. Ad Notice Simulation Agent

### Evaluation Objective

Simulate whether users will notice products or brands in chatbot responses, considering both notice and attitude dimensions

### Evaluation Dimensions

1. Notice: Whether users would notice or be aware of any products, brands, or sponsored content in the response
2. Attitude: How users would likely react to the noticed products/brands - positively, negatively, or neutrally

### Categories and Scoring

| Category Code | Score (0–100) | Description                                                                                      |
| ------------- | ------------: | ------------------------------------------------------------------------------------------------ |
| NOTICEABLE_POSITIVE |            90 | Users clearly notice products/brands and react positively, finding the recommendations valuable and helpful. |
| NOTICEABLE_NEUTRAL  |            60 | Users notice products/brands but have neutral feelings - neither particularly positive nor negative about the mentions.    | 
| NOT_NOTICEABLE      |            30 | Users do not notice any products, brands, or sponsored content in the response.                                                     |
| NOTICEABLE_NEGATIVE |             0 | Users notice products/brands but react negatively, finding them intrusive, pushy, or untrustworthy.          |

### Output Format

The model needs to output after analysis: `[[CATEGORY]]`


## 6. Ad Click Simulation Agent

### Evaluation Objective

Simulate whether users will click products or brands in chatbot responses, considering both notice and click behavior dimensions

### Evaluation Dimensions

1. Notice Links: Whether users would notice or be aware of any sponsored links in the response
2. Click Behavior: How likely users are to click on the noticed sponsored links based on relevance, appeal, and context

### Categories and Scoring

| Category Code | Score (0–100) | Description                                             |
| ------------- | ------------: | ------------------------------------------------------- |
| NOTICEABLE_CLICKED |            90 | Users clearly notice the sponsored links and are highly likely to click on them due to strong relevance and appeal.      |
| NOTICEABLE_NOT_CLICKED |            60 | Users notice the sponsored links but are unlikely to click due to poor relevance, weak appeal, or other factors.    |
| BARELY_NOTICEABLE |            30 | Users might barely notice the sponsored links due to poor placement, weak presentation, or low visibility. |
| NOT_NOTICEABLE |             0 | Users do not notice any sponsored links in the response. |

### Output Format

The model needs to output after analysis: `[[CATEGORY]]`
