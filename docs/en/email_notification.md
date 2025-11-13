# Email Notification

This feature notifies organization administrators by email when new submissions or comments are posted.

## Benefits of Implementation

* You can be notified by email when new submissions or comment submissions are made.

## Feature Description

* Organization administrators are notified by email when the following submissions are executed:
    * Comment submission on data resources.
    * New submission of utilization.
    * Comment submission on utilization.

    ※ This feature is turned off by default

## Configuration

1. Configure SMTP server settings

    Configure the SMTP server to use with the following environment variables.

    ```
    CKAN_SMTP_SERVER=smtp.corporateict.domain:25
    CKAN_SMTP_STARTTLS=True
    CKAN_SMTP_USER=user
    CKAN_SMTP_PASSWORD=pass
    ```

    Or configure the SMTP server to use with the following items in `ckan.ini`:  

    ```ini
    smtp.server = smtp.corporateict.domain:25
    smtp.starttls = true
    smtp.user = user
    smtp.password = pass
    ```
    
    ※ Environment variable settings take priority.

2. Add the following lines to ckan.ini

    * Turn on notification feature (required)

        ```ini
        ckan.feedback.notice.email.enable = true
        ```

    * Specify the email template storage directory (optional)

        ```ini
        ckan.feedback.notice.email.template_directory = /path/to/template_dir
        ```

        ※If not configured, `{directory where ckanext-feedback is installed}/templates/email_notification` will be used.

    * Configure email template names (required)  

        Please specify the filename of a file in the email template storage directory.  

        If you want to use a custom template, modify the contents of the file in the email template storage directory or create another template file and specify its filename.

        * Template name for resource comment submission notification

            ```ini
            ckan.feedback.notice.email.template_resource_comment = template.text
            ```

            ※To use the default template, please specify [resource_comment.text](../../ckanext/feedback/templates/email_notification/resource_comment.text).

        * Template name for utilization new submission notification

            ```ini
            ckan.feedback.notice.email.template_utilization = template.text
            ```

            ※To use the default template, please specify [utilization.text](../../ckanext/feedback/templates/email_notification/utilization.text).

        * Template name for utilization comment submission notification

            ```ini
            ckan.feedback.notice.email.template_utilization_comment = template.text
            ```

            ※To use the default template, please specify [utilization_comment.text](../../ckanext/feedback/templates/email_notification/utilization_comment.text).

    * Subject specification (optional)

        * Subject for resource comment submission notification

            ```ini
            ckan.feedback.notice.email.subject_resource_comment = Post a Resource comment
            ```

        * Subject for utilization new submission notification

            ```ini
            ckan.feedback.notice.email.subject_utilization = Post a Utilization
            ```

        * Subject for utilization comment submission notification

            ```ini
            ckan.feedback.notice.email.subject_utilization_comment = Post a Utilization comment
            ```

        ※If not specified, it will be "New Submission Notification".

3. Restart the web application server

