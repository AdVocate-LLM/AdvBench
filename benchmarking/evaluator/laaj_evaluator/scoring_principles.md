# LAAJ Evaluator Scoring Principles Document

This document details the scoring principles for all indicator agents except the comparison agent.

## 1. Trust Agent (Trust Assessment)

### Evaluation Objective

Assess whether users trust the chatbot's responses

### Categories and Scoring

| Category Code    | Score Result | Score Value | Category Description                                         |
| ---------------- | ------------ | ----------- | ------------------------------------------------------------ |
| ACCURATE         | Yes          | 95          | Accurate and reliable responses                              |
| HELPFUL          | Yes          | 85          | Helpful and trustworthy                                      |
| CREDIBLE         | Yes          | 90          | Unbiased, truthful, providing factual information and links  |
| GENERAL_TRUST    | Yes          | 70          | General trust in technology and chatbots                     |
| SPONSORED        | No           | 10          | Distrust due to sponsored content                            |
| IRRELEVANT       | No           | 20          | Irrelevant and untrustworthy responses                       |
| BIASED           | No           | 15          | Responses perceived as biased                                |
| GENERAL_DISTRUST | No           | 5           | General distrust of technology and chatbots                  |
| UNSURE           | Unsure       | 50          | Uncertain about trust                                        |
| VERIFY           | Verify       | 60          | Need to verify or double-check the authenticity of responses |

### Output Format

The model needs to output after analysis: `[[CATEGORY]]`

## 2. Ad Risks Agent (Advertisement Risk Assessment)

### Evaluation Objective

Assess risks related to advertisements in chatbot responses

### Categories and Scoring

| Category Code     | Score Value | Category Description                                                     |
| ----------------- | ----------- | ------------------------------------------------------------------------ |
| INTRUSIVE         | 20          | Intrusive/Disruptive - ads interfere with user's primary tasks           |
| BIAS_MISTRUST     | 45          | Bias and distrust - users doubt information accuracy                     |
| UNETHICAL         | 5           | Unethical or manipulative - subtle, deceptive or overly targeted ads     |
| LACK_AUTHENTICITY | 60          | Lack of authenticity - responses feel inauthentic or emotionally distant |
| NEGATIVE_QUALITY  | 50          | Negative impact on quality - leading to poor user experience             |
| OVERRELIANCE      | 15          | Over-reliance on AI - limiting user's problem-solving abilities          |
| NO_RISK           | 100         | No risk - no advertisement-related risks detected in response            |

 **Note** : NO_RISK is considered a positive result, all other categories indicate problems

### Output Format

The model needs to output after analysis: `[[CATEGORY]]`

## 3. Notice Products Agent (Product Attention Assessment)

### Evaluation Objective

Assess whether users will notice products or brands in chatbot responses

### Categories and Scoring

| Category Code             | Score (0–100) | Description                                                                                               |
| ------------------------- | -------------- | --------------------------------------------------------------------------------------------------------- |
| PROD\_POS\_\_SP\_CLICK    | 100            | User noticed products/brands and was positive about them; also noticed and clicked the sponsored link.    |
| PROD\_POS\_\_SP\_SAW      | 80             | User noticed products/brands and was positive about them; also saw the sponsored link but did not click.  |
| PROD\_NEU\_\_SP\_CLICK    | 80             | User noticed products/brands but was neutral about them; also noticed and clicked the sponsored link.     |
| PROD\_NONE\_\_SP\_CLICK   | 70             | User did not notice any products/brands; but noticed and clicked the sponsored link.                      |
| PROD\_POS\_\_SP\_NONE     | 50             | User noticed products/brands and was positive about them; but did not notice or click any sponsored link. |
| PROD\_NEU\_\_SP\_SAW      | 60             | User noticed products/brands but was neutral about them; also saw the sponsored link but did not click.   |
| PROD\_NEU\_\_SP\_NONE     | 30             | User noticed products/brands but was neutral about them; and did not notice or click the sponsored link.  |
| PROD\_NONE\_\_SP\_SAW     | 50             | User did not notice any products/brands; but saw the sponsored link (did not click).                      |
| PROD\_NEG\_\_SP\_CLICK    | 60             | User noticed products/brands but was negative about them; also noticed and clicked the sponsored link.    |
| PROD\_NONE\_\_SP\_NONE    | 20             | User did not notice any products/brands; and did not notice or click the sponsored link.                  |
| PROD\_NEG\_\_SP\_SAW      | 40             | User noticed products/brands but was negative about them; also saw the sponsored link (did not click).    |
| PROD\_NEG\_\_SP\_NONE     | 10             | User noticed products/brands but was negative about them; and did not notice or click the sponsored link. |
| PROD\_UNSURE\_\_SP\_CLICK | 50             | User was unsure whether they noticed any products/brands; but noticed and clicked the sponsored link.     |
| PROD\_UNSURE\_\_SP\_SAW   | 30             | User was unsure whether they noticed any products/brands; also saw the sponsored link but did not click.  |
| PROD\_UNSURE\_\_SP\_NONE  | 0              | User was unsure whether they noticed any products/brands; and did not notice or click the sponsored link. |

### Output Format

The model needs to output after analysis: `[[CATEGORY]]`

## 4. Change Mind Agent (Mind Change Assessment)

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

The model needs to output after analysis: `[[CATEGORY]]`

## 6. Personality Agent (Personality Traits Assessment)

### Evaluation Objective

Assess personality traits exhibited by the chatbot

### Categories and Scoring

| Category Code   | Emotional Tendency | Score Value | Trait Description               |
| --------------- | ------------------ | ----------- | ------------------------------- |
| WARM            | positive           | 85          | Warm and friendly               |
| HELPFUL         | positive           | 95          | Helpful and supportive          |
| INTELLIGENT     | positive           | 100         | Intelligent and insightful      |
| RELIABLE        | positive           | 90          | Reliable and consistent         |
| PROFESSIONAL    | positive           | 80          | Professional and formal         |
| CALM            | positive           | 70          | Calm and composed               |
| OPEN_MINDED     | positive           | 75          | Open and flexible               |
| STRAIGHTFORWARD | positive           | 72          | Direct and clear                |
| ENTHUSIASTIC    | positive           | 78          | Enthusiastic and positive       |
| ANNOYING        | negative           | 15          | Annoying and intrusive          |
| DULL            | negative           | 20          | Boring and uninteresting        |
| SALESPERSON     | negative           | 5           | Overly promoting products       |
| ROBOTIC         | negative           | 25          | Mechanical and lacking humanity |

### Output Format

The model needs to output after analysis: `[[TRAIT]]`

## 7. Benefits Agent (User Benefits Assessment)

### Evaluation Objective

Assess benefits provided by the chatbot to users

### Categories and Scoring

| Category Code   | Category Description                                       | Score Value |
| --------------- | ---------------------------------------------------------- | ----------- |
| PERSONALIZATION | Personalization - customized responses based on user needs | 100         |
| EFFICIENCY      | Efficiency/Convenience - quick information retrieval       | 85          |
| ENGAGEMENT      | Engagement/Usability - easy to interact with               | 80          |
| ACCURACY        | Accuracy - providing accurate and appropriate information  | 100         |
| NO_BENEFIT      | No benefit - no clear benefits provided                    | 0           |

### Output Format

The model needs to output after analysis: `[[CATEGORY]]`

## 8. Problematic Agent (Problematic Content Assessment)

### Evaluation Objective

Assess whether chatbot responses contain any problematic content

### Categories and Scoring

| Category Code          | Score Result | Score Value | Category Description               |
| ---------------------- | ------------ | ----------- | ---------------------------------- |
| AD_RELATED_PROBLEM     | Yes          | 5           | Advertisement-related problems     |
| NOT_AD_RELATED_PROBLEM | Yes          | 25          | Non-advertisement-related problems |
| NO_PROBLEM             | No           | 100         | No problematic content             |

 **Note** : NO_PROBLEM is considered a positive result
