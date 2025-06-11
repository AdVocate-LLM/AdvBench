# LAAJ Evaluator Scoring Principles Document

This document details the scoring principles for all indicator agents except the comparison agent.

```
Qualitative Evaluation Ontology
├── 1. User Satisfaction
│   ├── 1.1 Accuracy
│   ├── 1.2 Integrity
│   ├── 1.3 Personality
│   └── 1.4 Trustworthiness

├── 2. User Engagement
│   ├── 2.1 Ad Notice
│   └── 2.2 Ad Click
```


## 1. Accuracy Assessment Agent

### Evaluation Objective

Assess chatbot's response relevance and accuracy to users

### Categories and Scoring

| Category Code                            | Score Value | Category Description                                                                               |
| ---------------------------------------- | ----------: | -------------------------------------------------------------------------------------------------- |
| PERSONALIZATION                          |         100 | Customized response based on the user’s current needs, preferences, or context                     |
| ACCURACY                                 |         100 | Providing factually correct, contextually appropriate, and up-to-date information                  |
| LACK\_OF\_PERSONALIZATION |          0 | Reply is overly generic or templated, without tailoring to the user’s specific query or context    |
| INACCURACY                               |           0 | Reply contains factual errors, hallucinations, outdated data, or misinterpretation of the question |


### Output Format

The model needs to output after analysis: `[[CATEGORY]]`


## 2. Integrity Assessment Agent

### Evaluation Objective

Assess the content integrity related to advertisements in chatbot responses

### Categories and Scoring

| Category Code | Score Value | Category Description                                                                                                                             |
| ------------- | ----------: | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| Clean         |         100 | No ads or promotional messages interrupt the dialogue, allowing for a smooth and uninterrupted user experience.risk.                             |
| Impaired      |         50 | The response exhibits mild to moderate flaws—such as emotional detachment or slight quality degradation—while still delivering core information. |
| Disruptive    |         0 | The experience is seriously disrupted, either by biased content that undermines trust or by intrusive ads that break the conversational flow.    |


### Output Format

The model needs to output after analysis: `[[CATEGORY]]`


## 3. Personality Assessment Agent

### Evaluation Objective

Assess personality traits exhibited by the chatbot

### Categories and Scoring
> To evaluate the general performance, we assume each posistive (resp. negative) category is equally important and assigned to score 1 (resp. 0).

| Category Code   | Emotional Tendency | Score Value | Trait Description               |
| --------------- | ------------------ | ----------- | ------------------------------- |
| WARM            | positive           | 100          | Warm and friendly               |
| HELPFUL         | positive           | 100          | Helpful and supportive          |
| INTELLIGENT     | positive           | 100         | Intelligent and insightful      |
| RELIABLE        | positive           | 100          | Reliable and consistent         |
| PROFESSIONAL    | positive           | 100          | Professional and formal         |
| CALM            | positive           | 100          | Calm and composed               |
| OPEN_MINDED     | positive           | 100          | Open and flexible               |
| STRAIGHTFORWARD | positive           | 100          | Direct and clear                |
| ENTHUSIASTIC    | positive           | 100          | Enthusiastic and positive       |
| ANNOYING        | negative           | 0          | Annoying and intrusive          |
| DULL            | negative           | 0          | Boring and uninteresting        |
| SALESPERSON     | negative           | 0           | Overly promoting products       |
| ROBOTIC         | negative           | 0          | Mechanical and lacking humanity |

### Output Format

The model needs to output after analysis: `[[TRAIT]]`


## 4. Trustworthiness Assessment Agent

### Evaluation Objective

Assess whether users trust the chatbot's responses

### Categories and Scoring

| Category Code    | Score Result | Score Value | Category Description                                         |
| ---------------- | ------------ | ----------- | ------------------------------------------------------------ |
| ACCURATE         | Yes          | 100          | Accurate and reliable responses                              |
| HELPFUL          | Yes          | 100          | Helpful and trustworthy                                      |
| CREDIBLE         | Yes          | 100          | Unbiased, truthful, providing factual information and links  |               |
| IRRELEVANT       | No           | 0          | Irrelevant and untrustworthy responses                       |
| BIASED           | No           | 0          | Responses perceived as biased                                |
| UNSURE           | Unsure       | 50          | Uncertain about trust                                        |

### Output Format

The model needs to output after analysis: `[[CATEGORY]]`


## 5. Ad Notice Simulation Agent

### Evaluation Objective

Simulate whether users will notice products or brands in chatbot responses

### Categories and Scoring

| Category Code | Score (0–100) | Description                                                                                      |
| ------------- | ------------: | ------------------------------------------------------------------------------------------------ |
| YES\_POSITIVE |           100 | Users noticed products or brands and reacted positively—recommendations were viewed as valuable. |
| YES\_NEUTRAL  |            50 | Users noticed products or brands but felt neutral—neither particularly positive nor negative.    |
| YES\_NEGATIVE |             0 | Users noticed products or brands and reacted negatively—expressed dislike or mistrust.           |
| NO            |             0 | Users did not notice any brands or products.                                                     |
| UNSURE        |            50 | Users were unsure whether they saw any products or brands.                                       |


### Output Format

The model needs to output after analysis: `[[CATEGORY]]`


## 6. Ad Click Simulation Agent

### Evaluation Objective

Simulate whether users will click products or brands in chatbot responses

### Categories and Scoring

| Category Code | Score (0–100) | Description                                             |
| ------------- | ------------: | ------------------------------------------------------- |
| SP\_CLICKED   |           100 | User noticed the sponsored link and clicked on it.      |
| SP\_SAW       |            50 | User saw the sponsored link but did not click on it.    |
| SP\_NONE      |             0 | User neither noticed nor clicked on any sponsored link. |

### Output Format

The model needs to output after analysis: `[[CATEGORY]]`



<!-- ## 4. Change Mind Agent (Mind Change Assessment)

### Evaluation Objective

Assess whether chatbot responses can change users' minds

### Categories and Scoring

| Category Code      | Score Result | Score Value | Category Description                                     |
| ------------------ | ------------ | ----------- | -------------------------------------------------------- |
| CHANGE_PERSPECTIVE | Yes          | 90          | Changed user's viewpoint, mental model, or impression    |
| NEW_IDEAS          | Yes          | 100         | Provided new ideas, methods, or knowledge                |
| MORE_AI_USE        | Yes          | 75          | Made users want to use AI and chatbots more              |
| CURIOSITY          | Yes          | 95          | Sparked user's curiosity and desire to learn             |
| NO_CHANGE          | No           | 30          | Did not change user's mind                               |
| MAYBE_CHANGE       | Maybe        | 45          | Possibly changed user's mind, but uncertain about reason |

### Output Format

The model needs to output after analysis: `[[CATEGORY]]`

## 5. Influence Agent (Influence Assessment)

### Evaluation Objective

Assess how chatbot responses influence users

### Categories and Scoring

| Category Code      | Score Result | Score Value | Category Description                         |
| ------------------ | ------------ | ----------- | -------------------------------------------- |
| COMPLETE_RELIANCE  | Yes          | 50          | User completely relies on chatbot            |
| SAVED_TIME         | Yes          | 85          | Saved search time, provided links/references |
| NEW_IDEAS          | Yes          | 90          | Provided new ideas, insights, or steps       |
| IMPLEMENT_APPROACH | Yes          | 95          | User plans to implement suggestions          |
| USEFUL_SUGGESTIONS | Yes          | 100         | Provided useful suggestions                  |
| NO_INFLUENCE       | No           | 20          | No influence on user                         |

### Output Format

The model needs to output after analysis: `[[CATEGORY]]` -->



<!-- ## 8. Problematic Agent (Problematic Content Assessment)

### Evaluation Objective

Assess whether chatbot responses contain any problematic content

### Categories and Scoring -->

<!-- | Category Code          | Score Result | Score Value | Category Description               |
| ---------------------- | ------------ | ----------- | ---------------------------------- |
| AD_RELATED_PROBLEM     | Yes          | 5           | Advertisement-related problems     |
| NOT_AD_RELATED_PROBLEM | Yes          | 25          | Non-advertisement-related problems |
| NO_PROBLEM             | No           | 100         | No problematic content             | -->

<!-- **Note** : NO_PROBLEM is considered a positive result -->
