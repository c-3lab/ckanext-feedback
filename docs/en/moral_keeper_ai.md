# moral-keeper-ai

This module uses [moral-keeper-ai](https://github.com/c-3lab/moral-keeper-ai) to provide a feature where AI performs moral checking when submitting comments and presents appropriate correction suggestions when issues are found.  
When enabled, it is applied to the following comment submissions:

- Resource comments
- Utilization comments

## Benefits of Implementation

- Improved Quality of User Submissions
  - Inappropriate expressions can be corrected in advance, promoting constructive discussions
  - Comments that are clear and less likely to cause misunderstandings can be maintained

- Reduced Moderation Burden
  - Manual comment checking becomes unnecessary, reducing operational costs
  - Automatic evaluation is performed with consistent standards, maintaining fairness

- Maintaining Community Health
  - Suppresses aggressive expressions and ambiguous opinions, providing a better environment
  - Users can learn more appropriate expressions by receiving appropriate feedback

## Feature Description

### Moral Evaluation

AI evaluates comments from the following perspectives:

### Presentation of Correction Suggestions

When problematic comments are detected, appropriate expressions are suggested to users.

| Perspective | NG Example | Correction Suggestion |
| :-: | :-: | :-: |
| Not causing discomfort to readers | "This data is crap" | "This data has room for improvement" |
| Avoiding public backlash | "The government only tells lies" | "There is information that differs from government announcements" |
| Suppressing ambiguous opinion posts | "I don't understand" | "I think there is a lack of specific data" |

## Limitations

- Replies to comments are excluded as they have a strong relationship with the original post content and are difficult to evaluate independently.
- The AI model and endpoint used depend on `moral-keeper-ai`.  
For details, please refer to [moral-keeper-ai](https://github.com/c-3lab/moral-keeper-ai).

## Installation Instructions

### Environment Variable Configuration

Please configure the following environment variables.  
Please include them in the container's environment variable settings, etc.

```
AZURE_OPENAI_DEPLOY_NAME='your-deploy-name'
AZURE_OPENAI_API_KEY='your-api-key'
AZURE_OPENAI_ENDPOINT='https://your-endpoint-url.com/'
```

### Obtaining moral-keeper-ai

Please execute the following command in a container environment or similar.

```
pip install moral-keeper-ai
```

### Installing feedback

* Please refer to [Quick Start](../../README.md) **steps 1-4**.

## Options

For configuration instructions, please refer to the following document:  
[Detailed Documentation on ON/OFF Features](./switch_function.md)

