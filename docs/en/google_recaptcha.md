# google_reCAPTCHA

A spam prevention feature for various submissions.  
When the following submissions are executed, Google reCAPTCHA v3 verification is performed. If the calculated score is below the threshold, users are requested to retry the submission.

- Utilization submission
- Utilization comment submission
- Resource comment submission

## Configuration

This feature is enabled by adding the following configuration items in `ckan.ini`.  
Please obtain the v3 site key and secret key by following the [official guide](https://developers.google.com/recaptcha/intro).

```ini
ckan.feedback.recaptcha.enable = true
ckan.feedback.recaptcha.publickey = site-key
ckan.feedback.recaptcha.privatekey = secret-key
```

The default threshold is internally set to 0.5. If the verification score is below 0.5, users will be prompted to retry. To customize the threshold, add the following configuration:

```ini
ckan.feedback.recaptcha.score_threshold = 0.0 ~ 1.0
```

For information on how to determine an appropriate threshold, refer to the [official documentation on interpreting the score](https://developers.google.com/recaptcha/docs/v3#interpreting_the_score).  
For more details on Google reCAPTCHA v3 specifications, refer to the [official documentation](https://developers.google.com/recaptcha/docs/v3).

