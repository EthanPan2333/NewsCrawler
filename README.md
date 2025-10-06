# Guardian News Scraper for AWS Lambda

A robust Python script for scraping news articles from The Guardian newspaper, designed to run in AWS Lambda and store articles in S3.

## Lambda-Specific Features

### AWS Integration
- ✅ **S3 Storage**: Articles saved directly to S3 bucket in CSV format
- ✅ **CloudWatch Logging**: All logs sent to CloudWatch (no local file logging)
- ✅ **Lambda Handler**: Proper `lambda_handler` function for AWS Lambda execution
- ✅ **Environment Variables**: Configuration via Lambda environment variables
- ✅ **UTC Timestamping**: All timestamps in UTC for consistency

### S3 Storage Structure
Articles are stored in S3 with the following path structure:
```
s3://your-bucket/english-news/{YEAR}/{MONTH}/{DAY}/guardian_articles_{TIMESTAMP}.csv
```

Example:
```
s3://amplify-readerapp-ethanpa-linguaarticlesstoragebuc-q24f1zbqsksg/english-news/2025/09/24/guardian_articles_20250924_223015.csv
```

## Installation for Lambda

### Dependencies
```
pandas>=1.5.0
requests>=2.28.0
beautifulsoup4>=4.11.0
newsplease>=1.5.0
lxml>=4.9.0
boto3>=1.26.0
```

### Lambda Deployment Package
1. Create a deployment package with dependencies:
```bash
pip install -r requirements.txt -t ./package
cp get_articles_guardian.py ./package/
cd package && zip -r ../guardian-scraper-lambda.zip .
```

2. Upload to Lambda or use AWS SAM/CDK for deployment.

## Configuration

### Environment Variables
Set these in your Lambda function configuration:

| Variable | Description | Default |
|----------|-------------|---------|
| `S3_BUCKET` | S3 bucket name for storing articles | `amplify-readerapp-ethanpa-linguaarticlesstoragebuc-q24f1zbqsksg` |
| `MAX_ARTICLES` | Maximum articles to scrape per execution | `10` |
| `DELAY` | Delay between requests (seconds) | `1.0` |

### Event Parameters
You can also pass configuration via the Lambda event:
```json
{
  "max_articles": 20,
  "delay": 2.0
}
```

## Lambda Function Configuration

### Recommended Settings
- **Runtime**: Python 3.9 or later
- **Memory**: 512 MB (minimum for web scraping)
- **Timeout**: 5-15 minutes (depending on article count)
- **Handler**: `get_articles_guardian.lambda_handler`

### Required IAM Permissions
Your Lambda execution role needs:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:PutObjectAcl"
      ],
      "Resource": "arn:aws:s3:::your-bucket-name/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

## Usage

### Lambda Invocation
The function can be invoked:
1. **Manually** via AWS Console
2. **Scheduled** via EventBridge (CloudWatch Events)
3. **API Gateway** for HTTP triggers
4. **Other AWS services** via SDK

### Sample Event
```json
{
  "max_articles": 15,
  "delay": 1.5
}
```

### Response Format
```json
{
  "statusCode": 200,
  "body": {
    "success": true,
    "articles_scraped": 15,
    "s3_bucket": "your-bucket-name",
    "s3_key": "english-news/2025/09/24/guardian_articles_20250924_223015.csv",
    "statistics": {
      "total_articles": 15,
      "unique_authors": 12,
      "avg_article_length": 2847.3,
      "date_range": {
        "earliest": "2025-09-24T10:30:00",
        "latest": "2025-09-24T22:15:00"
      }
    }
  }
}
```

## CSV Output Format

The CSV files stored in S3 contain:

| Column | Description | Example |
|--------|-------------|---------|
| `headline` | Article title | "Climate change impacts on agriculture" |
| `article_body` | Full article text | "Scientists have discovered..." |
| `author_name` | Author(s) name(s) | "John Smith, Jane Doe" |
| `date_published` | Publication date (ISO format) | "2025-09-24T10:30:00" |
| `language` | Article language | "en" |
| `source` | Source domain | "www.theguardian.com" |
| `url` | Article URL | "https://www.theguardian.com/..." |
| `scraped_at` | UTC timestamp when scraped | "2025-09-24T22:30:15.123456+00:00" |

## Monitoring and Logging

### CloudWatch Logs
All logs are sent to CloudWatch with log group:
```
/aws/lambda/your-function-name
```

### Log Levels
- **INFO**: General progress and success messages
- **WARNING**: Non-fatal issues (missing content, etc.)
- **ERROR**: Fatal errors and exceptions

### Metrics to Monitor
- **Duration**: Function execution time
- **Memory Usage**: Peak memory consumption
- **Error Rate**: Failed executions
- **Custom Metrics**: Articles scraped per execution

## Scheduling

### EventBridge Rule (Recommended)
Create a scheduled rule to run the scraper:
```json
{
  "Rules": [
    {
      "Name": "guardian-scraper-daily",
      "ScheduleExpression": "cron(0 6 * * ? *)",
      "State": "ENABLED",
      "Targets": [
        {
          "Id": "1",
          "Arn": "arn:aws:lambda:region:account:function:guardian-scraper",
          "Input": "{\"max_articles\": 50, \"delay\": 2.0}"
        }
      ]
    }
  ]
}
```

This runs daily at 6 AM UTC, scraping 50 articles with 2-second delays.

## Local Testing

You can test the Lambda function locally:

```bash
# Test with default settings
python get_articles_guardian.py

# Test with custom parameters
python get_articles_guardian.py --max-articles 3 --delay 0.5 --bucket your-test-bucket
```

## Error Handling

The Lambda function handles various error scenarios:

### Network Issues
- Connection timeouts
- HTTP errors (404, 500, etc.)
- DNS resolution failures

### AWS Issues
- S3 upload failures
- Permission errors
- Bucket access issues

### Data Issues
- Malformed XML in sitemap
- Articles with missing content
- Encoding problems

## Performance Considerations

### Lambda Limits
- **15-minute timeout**: Adjust `max_articles` and `delay` accordingly
- **Memory usage**: NewsPlease can be memory-intensive
- **Cold starts**: First execution may be slower

### Optimization Tips
1. **Reduce delay** for faster execution (but respect rate limits)
2. **Batch processing**: Process multiple articles per Lambda invocation
3. **Concurrent execution**: Use multiple Lambda functions for parallel processing
4. **Memory allocation**: Increase memory for better performance

## Cost Optimization

### Lambda Costs
- **Execution time**: Minimize with efficient scraping
- **Memory allocation**: Balance performance vs. cost
- **Request count**: Consider batching vs. frequency

### S3 Costs
- **Storage**: CSV files are small and compress well
- **Requests**: PUT requests for each file upload
- **Transfer**: No egress charges within same region

## Troubleshooting

### Common Issues

#### 1. "Access Denied" S3 Error
- Check IAM permissions
- Verify bucket name and region
- Ensure bucket exists

#### 2. Lambda Timeout
- Reduce `max_articles`
- Increase timeout setting
- Optimize delay parameter

#### 3. "No articles scraped"
- Check Guardian sitemap availability
- Verify network connectivity
- Review CloudWatch logs for details

#### 4. Memory Issues
- Increase Lambda memory allocation
- Monitor CloudWatch memory metrics
- Consider processing fewer articles per execution

### Debug Mode
Enable debug logging by modifying the script:
```python
logger.setLevel(logging.DEBUG)
```

## Security Best Practices

1. **IAM Principle of Least Privilege**: Grant only necessary S3 permissions
2. **Environment Variables**: Use for sensitive configuration
3. **VPC Configuration**: Consider VPC deployment for network isolation
4. **Encryption**: Enable S3 bucket encryption
5. **Access Logging**: Enable S3 access logging for audit trails

## Future Enhancements

- [ ] **Parallel Processing**: Multiple Lambda functions for faster scraping
- [ ] **DynamoDB Integration**: Store metadata and track processed articles
- [ ] **SNS Notifications**: Alert on completion or failures
- [ ] **Step Functions**: Orchestrate complex scraping workflows
- [ ] **API Gateway**: HTTP API for on-demand scraping
- [ ] **CloudFormation/CDK**: Infrastructure as Code deployment

## Support

For Lambda-specific issues:
1. Check CloudWatch logs for detailed error messages
2. Verify IAM permissions and S3 bucket access
3. Test locally with the same parameters
4. Monitor Lambda metrics in CloudWatch

## License

This Lambda version maintains the same license as the original code.
