# Dataset Ranking API

## Overview

This API retrieves dataset ranking information based on specified conditions.  
Rankings are calculated based on usage counts aggregated according to the specified period and conditions.

## Endpoint

GET /api/3/action/datasets_ranking

## Input Parameters

| Parameter Name        | Meaning                         | Type    | Required | Default Value            | Notes                                                     |
| ------------------- | ---------------------------- | ----- | ---- | ----------------------- | -------------------------------------------------------- |
| top_ranked_limit     | Number of records to retrieve                     | int   | Optional | 5                       | Specify how many top-ranked items to retrieve.           |
| period_months_ago    | Relative period (past X months)        | string   | Optional | None                    | Example: Specifying `3` retrieves aggregation for the past 3 months.     |
| start_year_month     | Fixed period start year-month          | string| Optional | 2023-04                    | Example: `2024-01` starts from January 2024.  
| end_year_month       | Fixed period end year-month          | string| Optional | Previous month                    | Example: `2024-03` ends at March 2024. If both start and end are specified, aggregation is performed for that period. |
| aggregation_metric   | Aggregation metric                     | string| Optional | "download"              | Can also specify aggregation metrics such as `"likes"` for number of likes, `"resource_comment"` for number of resource comments, and `"utilization_comments"` for number of utilization comments. |
| organization_name    | Filter by organization name       | string| Optional | None  |   |

## Output (Response) Description

| Parameter Name        | Meaning                         | Type | Notes                                                     |
| ------------------- | ---------------------------- | ----- |  -------------------------------------------------------- |
| help     | URL that returns API help                     | string   | Accessing this URL with GET retrieves JSON showing API overview  |
| success    | Boolean value indicating API execution success/failure        | bool  |   |
| result     | Result data        | object | |    
| datasets_ranking  | Dataset ranking | array| |
| rank | Rank | int | Returns 1 for first place |
| group_name | Name of the group to which the dataset belongs | string |  |
| group_title | Title of the group to which the dataset belongs | string |  |
| dataset_title | Dataset title | string |  |
| dataset_notes | Dataset description | string |  |
| dataset_link | Dataset URL | string |  |
| download_count_by_period | Number of downloads during the aggregation period | int | Present when download is specified as aggregation_metric |
| total_download_count | Total number of downloads for all periods | int | Present when download is specified as aggregation_metric |
| likes_count_by_period | Number of likes during the aggregation period | int | Present when likes is specified as aggregation_metric |
| total_likes_count | Total number of likes for all periods | int | Present when likes is specified as aggregation_metric |
| resource_comments_count_by_period | Number of comments during the aggregation period | int | Present when resource_comments is specified as aggregation_metric |
| total_resource_comments_count | Total number of comments for all periods | int | Present when resource_comments is specified as aggregation_metric |
| utilization_comments_count_by_period | Number of utilization comments during the aggregation period | int | Present when utilization_comments is specified as aggregation_metric |
| total_utilization_comments_count | Total number of utilization comments for all periods | int | Present when utilization_comments is specified as aggregation_metric |

## Response Example

The following is an example of JSON returned by the API when executing `curl https://your-ckan-site/api/3/action/datasets_ranking?period_months_ago=3` from the command line.

```json
{
  "help": "https://your-ckan-site/api/3/action/help_show?name=datasets_ranking",
  "success": true,
  "result": {
    "datasets_ranking": [
      {
        "rank": 1,
        "group_name": "o0001",
        "group_title": "Organization name1",
        "dataset_title": "Dataset name11",
        "dataset_notes": "Dataset notes",
        "dataset_link": "https://your-ckan-site/dataset/d11",
        "download_count_by_period": 123,
        "total_download_count": 6789,
      },
      {
        "rank": 2,
        "group_name": "o0002",
        "group_title": "Organization name2",
        "dataset_title": "Dataset name21",
        "dataset_notes": "Dataset explanation",
        "dataset_link": "https://your-ckan-site/dataset/d21",
        "download_count_by_period": 121,
        "total_download_count": 7000,
      },
      // ...
    ]
  }
}
```

### About Unicode Escape Sequences (e.g., \u65e5\u672c\u8a9e)
When the API response contains Japanese characters, using commands like curl may result in Japanese characters not being displayed correctly and being output in escaped format due to character encoding. This is due to the curl usage environment and terminal settings, not an issue with the API itself. If necessary, you can correctly view Japanese characters by appropriately converting and displaying the character encoding using tools or editors. For example:
 - Use jq to format the display (including Unicode decoding)
 - Save the output to a file and open it with a UTF-8 compatible editor
 - Decode and check using scripts in Python or other languages

## Error Overview

When success is false, an error object is included, providing information about the error.
Errors mainly occur in the following cases:

- Invalid parameter format: An error occurs if the date format does not match YYYY-MM, or if an invalid value (such as a negative number) is specified for period_months_ago.


### Main Fields in Error Object
| Parameter Name        | Meaning                         | Type | Notes                                                     |
| ------------------- | ---------------------------- | ----- |  -------------------------------------------------------- |
| message     | Error message  | string   |   |
| __type    | Error type        | string  | Example: "Validation Error" |

## Error Response Examples

The following shows examples of responses when errors occur.

### Example of Missing Required Parameter Error
```
{
  "help": "https://your-ckan-site/api/3/action/help_show?name=datasets_ranking",
  "success": false,
  "error": {
    "message": "Please set the period for aggregation.",
    "__type": "Validation Error"
  }
}
```

### Example of Invalid Parameter Format Error

```
{
  "help": "https://your-ckan-site/api/3/action/help_show?name=datasets_ranking",
  "success": false,
  "error": {
    "message": "Invalid format for 'start_year_month'. Expected format is YYYY-MM.",
    "__type": "Validation Error"
  }
}
```

