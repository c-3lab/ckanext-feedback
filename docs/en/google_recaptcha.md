# Google reCAPTCHA

This feature is designed to prevent spam from bots in various posts.

## Benefits of Implementation

* It can reduce spam when new posts or comments are made by bots.

## Feature Description

* When the following posts are executed, verification using Google reCAPTCHA v3 is performed, and if the calculated score is below the threshold, the user is asked to retry the post.
    * Posting comments on data resources.
    * New posts on utilization.
    * Posting comments on utilization.

    ※ This feature is off by default.

## Configuration Method

1. Follow the [official Google reCAPTCHA guide](https://developers.google.com/recaptcha/intro?hl=en) to obtain the v3 site key and secret key.

2. Add the following lines to `ckan.ini`:

    * Enable the Google reCAPTCHA feature (required)

        ```ini
        ckan.feedback.recaptcha.enable = true
        ```

    * Set the site key and secret key (required)

        ```ini
        ckan.feedback.recaptcha.publickey = site_key
        ckan.feedback.recaptcha.privatekey = secret_key
        ```

    * Set the threshold (optional)

        ```ini
        ckan.feedback.recaptcha.score_threshold = 0.0 ~ 1.0
        ```

        * The default value is 0.5 if not set.
        * If the score from Google reCAPTCHA verification is below the threshold, the user will be asked to retry.
        * For guidance on determining the appropriate threshold, refer to the [official documentation on interpreting the score](https://developers.google.com/recaptcha/docs/v3?hl=en#interpreting_the_score).

3. Restart the web application server.

For detailed specifications of Google reCAPTCHA v3, refer to the [official documentation](https://developers.google.com/recaptcha/docs/v3?hl=en).