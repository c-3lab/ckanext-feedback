# Resource Module

A module that allows commenting and rating on data resources.

![Resource Comment Screen](../assets/resource_comment_10.jpg)

## Overview

### Benefits of Implementation

* **Understanding Data Utilization Status**
  * Provides guidelines for planning data publication and maintenance
  * Helps recognize the importance of open data more clearly

* **Simplifying Data Inquiries**
  * Promotes understanding of data and encourages utilization

## Key Features

### 1. Comment Feature

You can do the following for data resources:
* Submit comments on data resources
* **Image Attachment Feature** (optional)

![Comment Feature](../assets/resource_comment_20.jpg)

### 2. Visualization of Aggregated Information

The following information can be visualized:
* Number of comments on data resources

![Visualization of Number of Comments](../assets/resource_comment_50.jpg)

### 3. Response Status Management by Administrators

* Management of response status for resource comments
* Visualization of response status
  * Unaddressed
  * In Progress
  * Completed
  * Deferred
* Administrator high-rating feature

![Status Management](../assets/resource_comment_60.jpg)

## Optional Features

### Repeat Post Limit

You can limit each user to commenting only once per resource.

* **Use Case**: Spam prevention
* **Technology**: Cookie-based

![Comment Post Limit Feature](../assets/resource_comment_30.jpg)

### Rating

You can express ratings for each data resource using a 5-star system.

![Rating Feature](../assets/resource_comment_40.jpg)

### Image Attachment

Enables attaching images to comments and replies.

![Image Attachment](../assets/resource_comment_70.jpg)

![Image Attachment](../assets/resource_comment_80.jpg)

### Reply Open

Allows non-administrators to reply to comments as well.

![Image Attachment](../assets/resource_comment_90.jpg)


#### Configuration

If you want to specify a directory for storing images, add the following configuration to `ckan.ini`:

```ini
ckan.feedback.storage_path = /path/to/storage
```

**Notes**:
* Please replace the above path `/path/to/storage` appropriately for your environment
* If this configuration is not specified, the `/var/lib/ckan/feedback` directory will be used as the default storage location

## Configuration

For ON/OFF settings of each feature, please refer to the following document:

📖 [Detailed Documentation on ON/OFF Features](./switch_function.md)

