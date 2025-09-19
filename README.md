# Guardian News Scraper

A robust Python script for scraping news articles from The Guardian newspaper with comprehensive error handling, logging, and configuration options.

## Features

### Improvements over Original Version

- ✅ **Proper Resource Management**: Uses context managers for file operations
- ✅ **Comprehensive Error Handling**: Graceful handling of network failures and parsing errors
- ✅ **Logging System**: Detailed logging to both file and console
- ✅ **Rate Limiting**: Configurable delays between requests to be respectful to servers
- ✅ **Command Line Interface**: Flexible command-line arguments
- ✅ **Data Validation**: Ensures article quality before saving
- ✅ **Statistics Generation**: Automatic statistics display after scraping
- ✅ **Clean Data Format**: Removes unnecessary list wrapping from original
- ✅ **Object-Oriented Design**: Better code organization and reusability
- ✅ **Type Hints**: Better code documentation and IDE support

## Installation

### Setup Virtual Environment (Recommended)

```bash
# Clone the repository
git clone <your-repo-url>
cd NewsCrawler

# Create virtual environment
python3 -m venv news_env

# Activate virtual environment
source news_env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Alternative: System-wide Installation

```bash
# Install dependencies globally (not recommended)
pip install -r requirements.txt
```

### Files

- `get_articles_guardian.py` - Main Guardian news scraper script
- `requirements.txt` - Python dependencies
- `README.md` - This documentation
- `.gitignore` - Git ignore rules
- `news_env/` - Python virtual environment (activate with `source news_env/bin/activate`)
- `output/` - Directory for CSV output files
- `logs/` - Directory for log files

## Usage

### Basic Usage

```bash
# Scrape 100 articles (default)
python get_articles_guardian.py

# Scrape 25 articles (statistics always shown)
python get_articles_guardian.py --max-articles 25

# Custom output file and delay
python get_articles_guardian.py --output my_articles.csv --delay 2.0
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--max-articles` | Maximum number of articles to scrape | 100 |
| `--delay` | Delay between requests (seconds) | 1.0 |
| `--output` | Output CSV filename | guardian_data.csv |
| `--no-timestamp` | Disable automatic timestamp suffix | False |

### Examples

#### 1. Quick Test Run
```bash
python get_articles_guardian.py --max-articles 5
```

#### 2. Large Scale Scraping
```bash
python get_articles_guardian.py --max-articles 100 --delay 2.0 --output large_dataset.csv
```

#### 3. Respectful Scraping
```bash
python get_articles_guardian.py --max-articles 50 --delay 3.0
```

#### 4. Disable Timestamp (use exact filename)
```bash
python get_articles_guardian.py --output my_data.csv --no-timestamp
```

#### 5. UTC Timestamped Output (default behavior)
```bash
python get_articles_guardian.py --output guardian_articles.csv
```

## Output Format

The scraper generates CSV files in the `output/` directory with the following columns:

| Column | Description | Example |
|--------|-------------|---------|
| `headline` | Article title | "Climate change impacts on agriculture" |
| `article_body` | Full article text | "Scientists have discovered..." |
| `author_name` | Author(s) name(s) | "John Smith, Jane Doe" |
| `date_published` | Publication date (ISO format) | "2025-09-18T05:00:35" |
| `language` | Article language | "en" |
| `source` | Source domain | "www.theguardian.com" |
| `url` | Article URL | "https://www.theguardian.com/..." |

## Logging

The scraper creates detailed logs in the `logs/` directory with UTC timestamped filenames in the format `get_articles_guardian_log_{TIMESTAMP}.log` (e.g., `logs/get_articles_guardian_log_20250918_055416.log`) with information about:

- Sitemap fetching progress
- Individual article extraction attempts
- Errors and warnings
- Final statistics

### Log Levels

- **INFO**: General progress information
- **WARNING**: Non-fatal issues (e.g., articles with missing content)
- **ERROR**: Fatal errors that prevent processing
- **DEBUG**: Detailed debugging information (enable with logging level change)

## Error Handling

The improved scraper handles various error scenarios:

### Network Issues
- Connection timeouts
- HTTP errors (404, 500, etc.)
- DNS resolution failures

### Data Issues
- Malformed XML in sitemap
- Articles with missing content
- Encoding problems

### File System Issues
- Permission errors
- Disk space problems
- Invalid file paths


## Performance Considerations

### Rate Limiting
- Default delay: 1 second between requests
- Recommended for large scraping: 2-3 seconds
- Adjust based on server response times

### Memory Usage
- Processes articles one at a time (low memory footprint)
- Sitemap loaded entirely into memory (usually < 1MB)

### Network Efficiency
- Uses session reuse where possible
- Implements proper timeout handling
- Graceful degradation on failures

## Comparison with Original

| Feature | Original | Improved |
|---------|----------|----------|
| Error Handling | ❌ None | ✅ Comprehensive |
| Resource Management | ❌ File not closed | ✅ Context managers |
| Rate Limiting | ❌ None | ✅ Configurable delays |
| Logging | ❌ Print statements | ✅ Professional logging |
| Data Format | ❌ Lists everywhere | ✅ Clean strings |
| Configurability | ❌ Hard-coded | ✅ Command line + config |
| Code Organization | ❌ Procedural | ✅ Object-oriented |
| Documentation | ❌ Minimal | ✅ Comprehensive |

## Troubleshooting

### Common Issues

#### 1. "Failed to fetch sitemap"
- Check internet connection
- Verify The Guardian's sitemap URL is accessible
- Check firewall/proxy settings

#### 2. "No valid article found"
- Some URLs may not contain full articles
- This is normal - the scraper will skip and continue

#### 3. "Failed to write to CSV file"
- Check file permissions
- Ensure output directory exists
- Verify disk space availability

#### 4. High failure rate
- Increase delay between requests
- Check if The Guardian has rate limiting
- Verify NewsPlease dependencies are installed

### Debug Mode

To enable debug logging, modify the logging level in the script:

```python
logging.basicConfig(level=logging.DEBUG, ...)
```

### Log Files

Each run creates a unique UTC timestamped log file in the `logs/` directory (e.g., `logs/get_articles_guardian_log_20250918_055416.log`) to avoid overwriting previous logs and maintain a history of scraping sessions.

## Best Practices

1. **Be Respectful**: Use appropriate delays between requests
2. **Monitor Logs**: Check logs for errors and warnings
3. **Validate Data**: Review output CSV for data quality
4. **Handle Interruptions**: Use Ctrl+C to stop gracefully
5. **Backup Data**: Keep copies of successful scraping runs

## Legal and Ethical Considerations

- Respect The Guardian's robots.txt and terms of service
- Use scraped data responsibly and in accordance with copyright laws
- Consider contacting The Guardian for large-scale data needs
- Implement appropriate rate limiting to avoid overloading servers

## Future Enhancements

Potential improvements for future versions:

- [ ] Parallel processing for faster scraping
- [ ] Database storage options (SQLite, PostgreSQL)
- [ ] Multiple news source support
- [ ] Content filtering and categorization
- [ ] Automatic retry mechanisms
- [ ] Progress bars for long-running scrapes
- [ ] Email notifications on completion
- [ ] Docker containerization

## Support

For issues or questions:

1. Check the logs in the UTC timestamped log file (e.g., `logs/get_articles_guardian_log_YYYYMMDD_HHMMSS.log`)
2. Review this documentation
3. Verify all dependencies are installed
4. Test with a small number of articles first

## License

This improved version maintains the same license as the original code.
