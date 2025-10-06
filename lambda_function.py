#!/usr/bin/env python3
"""
Guardian News Article Scraper for AWS Lambda - Optimized Version

This lightweight version removes unnecessary dependencies to reduce package size.
Designed to run in AWS Lambda with CloudWatch logging.
"""

import csv
import json
import logging
import time
import io
import re
import uuid
from datetime import datetime, timezone
import os

import boto3
import requests
from bs4 import BeautifulSoup

# Configure logging for CloudWatch
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class GuardianScraperLambda:
    """A lightweight scraper for Guardian news articles designed for AWS Lambda."""
    
    def __init__(self, s3_bucket, max_articles=10, delay=1.0):
        """
        Initialize the scraper for Lambda execution.
        
        Args:
            s3_bucket: S3 bucket name to store articles
            max_articles: Maximum number of articles to scrape
            delay: Delay between requests in seconds (rate limiting)
        """
        self.max_articles = max_articles
        self.delay = delay
        self.s3_bucket = s3_bucket
        self.sitemap_url = "https://www.theguardian.com/sitemaps/news.xml"
        
        # Initialize S3 client
        self.s3_client = boto3.client('s3')
        
        # Generate S3 path based on current UTC date
        now_utc = datetime.now(timezone.utc)
        epoch_milli = int(now_utc.timestamp() * 1000)
        self.s3_prefix = f"english-news/{now_utc.year:04d}/{now_utc.month:02d}/{now_utc.day:02d}"
        self.timestamp = now_utc.strftime("%Y%m%d")
        self.epoch_milli = epoch_milli
        
        logger.info(f"Initialized scraper for bucket: {s3_bucket}, prefix: {self.s3_prefix}")
        
    def fetch_sitemap_urls(self):
        """
        Fetch and parse The Guardian's sitemap to extract article URLs.
        
        Returns:
            List of dictionaries containing URL and last modified date
        """
        logger.info(f"Fetching sitemap from {self.sitemap_url}")
        
        try:
            response = requests.get(self.sitemap_url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch sitemap: {e}")
            raise
            
        try:
            # Try XML parser first, fallback to lxml-xml, then html.parser
            soup = None
            parsers = ['xml', 'lxml-xml', 'html.parser']
            
            for parser in parsers:
                try:
                    soup = BeautifulSoup(response.text, parser)
                    logger.info(f"Successfully parsed sitemap with {parser} parser")
                    break
                except Exception as parser_error:
                    logger.warning(f"Parser {parser} failed: {parser_error}")
                    continue
            
            if soup is None:
                raise Exception("No suitable XML parser found")
            
            urls = []
            
            for url_element in soup.find_all('url'):
                loc_element = url_element.find('loc')
                lastmod_element = url_element.find('lastmod')
                
                if loc_element and lastmod_element:
                    urls.append({
                        'url': loc_element.text.strip(),
                        'last_modified': lastmod_element.text.strip()
                    })
                    
            logger.info(f"Found {len(urls)} URLs in sitemap")
            return urls
            
        except Exception as e:
            logger.error(f"Failed to parse sitemap: {e}")
            raise
    
    def extract_article_data_simple(self, url):
        """
        Extract article data using simple web scraping (without NewsPlease).
        
        Args:
            url: Article URL to scrape
            
        Returns:
            Dictionary containing article data, or None if extraction fails
        """
        try:
            logger.debug(f"Extracting article from: {url}")
            
            # Get the article page
            response = requests.get(url, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; Guardian-Scraper/1.0)'
            })
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract headline
            headline = None
            for selector in ['h1[data-gu-name="headline"]', 'h1.content__headline', 'h1']:
                headline_elem = soup.select_one(selector)
                if headline_elem:
                    headline = headline_elem.get_text().strip()
                    break
            
            if not headline:
                logger.warning(f"No headline found at {url}")
                return None
            
            # Extract article body
            article_body = ""
            body_selectors = [
                '[data-gu-name="body"] p',
                '.content__article-body p',
                '.article-body p',
                'div[data-component="text-block"] p'
            ]
            
            for selector in body_selectors:
                paragraphs = soup.select(selector)
                if paragraphs:
                    article_body = '\n\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
                    break
            
            if not article_body:
                logger.warning(f"No article body found at {url}")
                return None
            
            # Extract author
            author_name = ""
            author_selectors = [
                '[data-component="contributor-byline"] a',
                '.byline a',
                '[rel="author"]'
            ]
            
            for selector in author_selectors:
                authors = soup.select(selector)
                if authors:
                    author_name = ', '.join([a.get_text().strip() for a in authors])
                    break
            
            # Extract publication date
            date_published = ""
            date_selectors = [
                'time[datetime]',
                '[data-component="timestamp"] time',
                '.content__dateline time'
            ]
            
            for selector in date_selectors:
                date_elem = soup.select_one(selector)
                if date_elem and date_elem.get('datetime'):
                    date_published = date_elem.get('datetime')
                    break
            
            # Generate unique article ID
            article_id = str(uuid.uuid4())
            
            # Extract and clean data
            data = {
                'article_id': article_id,
                'headline': headline,
                'article_body': article_body,
                'author_name': author_name,
                'date_published': date_published,
                'language': 'en',
                'source': 'www.theguardian.com',
                'url': url,
                'scraped_at': datetime.now(timezone.utc).isoformat()
            }
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to extract article from {url}: {e}")
            return None
    
    def upload_to_s3(self, articles):
        """
        Upload articles to S3 as CSV.
        
        Args:
            articles: List of article dictionaries
            
        Returns:
            S3 key of uploaded file
        """
        if not articles:
            raise ValueError("No articles to upload")
        
        # Create CSV content in memory
        csv_buffer = io.StringIO()
        fieldnames = ['article_id', 'headline', 'article_body', 'author_name', 'date_published', 
                     'language', 'source', 'url', 'scraped_at']
        
        writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
        writer.writeheader()
        
        for article in articles:
            writer.writerow(article)
        
        # Generate S3 key
        s3_key = f"{self.s3_prefix}/metadata/guardian_articles_summary_{self.timestamp}_{self.epoch_milli}.csv"
        
        # Upload to S3
        try:
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=s3_key,
                Body=csv_buffer.getvalue(),
                ContentType='text/csv',
                Metadata={
                    'scraper': 'guardian-lambda',
                    'article_count': str(len(articles)),
                    'scraped_at': self.timestamp
                }
            )
            logger.info(f"Successfully uploaded {len(articles)} articles to s3://{self.s3_bucket}/{s3_key}")
            return s3_key
            
        except Exception as e:
            logger.error(f"Failed to upload to S3: {e}")
            raise
    
    def upload_article_text_files(self, articles):
        """
        Upload individual article text files to S3.
        
        Args:
            articles: List of article dictionaries
            
        Returns:
            List of S3 keys for uploaded text files
        """
        if not articles:
            raise ValueError("No articles to upload")
        
        uploaded_keys = []
        
        for article in articles:
            try:
                # Create text file content
                text_content = f"{article['headline']}\n{article['author_name']}\n{article['date_published']}\n{article['article_body']}"
                
                # Generate S3 key for individual article
                article_s3_key = f"{self.s3_prefix}/articles/{article['article_id']}.txt"
                
                # Upload to S3
                self.s3_client.put_object(
                    Bucket=self.s3_bucket,
                    Key=article_s3_key,
                    Body=text_content,
                    ContentType='text/plain',
                    Metadata={
                        'scraper': 'guardian-lambda',
                        'article_id': article['article_id'],
                        'headline': article['headline'][:100],  # Truncate for metadata
                        'scraped_at': self.timestamp
                    }
                )
                
                uploaded_keys.append(article_s3_key)
                logger.debug(f"Uploaded article text file: s3://{self.s3_bucket}/{article_s3_key}")
                
            except Exception as e:
                logger.error(f"Failed to upload article text file for {article['article_id']}: {e}")
                # Continue with other articles even if one fails
                continue
        
        logger.info(f"Successfully uploaded {len(uploaded_keys)} article text files")
        return uploaded_keys
            
    def scrape_articles(self):
        """
        Main scraping function that coordinates the entire process.
        
        Returns:
            Dictionary containing scraping results and statistics
        """
        logger.info(f"Starting scrape of up to {self.max_articles} articles")
        
        # Get URLs from sitemap
        try:
            url_data = self.fetch_sitemap_urls()
        except Exception as e:
            logger.error(f"Cannot proceed without sitemap data: {e}")
            return {
                'success': False,
                'error': str(e),
                'articles_scraped': 0
            }
            
        if not url_data:
            logger.error("No URLs found in sitemap")
            return {
                'success': False,
                'error': 'No URLs found in sitemap',
                'articles_scraped': 0
            }
        
        # Scrape articles
        articles = []
        articles_scraped = 0
        
        for i, url_info in enumerate(url_data):
            if articles_scraped >= self.max_articles:
                break
                
            url = url_info['url']
            article_data = self.extract_article_data_simple(url)
            
            if article_data:
                articles.append(article_data)
                articles_scraped += 1
                logger.info(f"Scraped article {articles_scraped}/{self.max_articles}: {article_data['headline'][:50]}...")
            
            # Rate limiting (but be mindful of Lambda timeout)
            if i < len(url_data) - 1 and articles_scraped < self.max_articles:
                time.sleep(self.delay)
        
        # Upload to S3 if we have articles
        if articles:
            try:
                # Upload CSV summary file
                s3_key = self.upload_to_s3(articles)
                
                # Upload individual article text files
                text_file_keys = self.upload_article_text_files(articles)
                
                # Generate statistics
                stats = self.generate_stats(articles)
                
                return {
                    'success': True,
                    'articles_scraped': articles_scraped,
                    's3_bucket': self.s3_bucket,
                    's3_key': s3_key,
                    'text_files_uploaded': len(text_file_keys),
                    'text_file_keys': text_file_keys,
                    'statistics': stats
                }
                
            except Exception as e:
                logger.error(f"Failed to upload articles: {e}")
                return {
                    'success': False,
                    'error': f"Scraping succeeded but upload failed: {str(e)}",
                    'articles_scraped': articles_scraped
                }
        else:
            return {
                'success': False,
                'error': 'No articles were successfully scraped',
                'articles_scraped': 0
            }
    
    def generate_stats(self, articles):
        """
        Generate statistics about the scraped articles.
        
        Args:
            articles: List of article dictionaries
            
        Returns:
            Dictionary containing statistics
        """
        if not articles:
            return {}
        
        # Extract authors and dates
        authors = [article.get('author_name', '') for article in articles if article.get('author_name')]
        dates = [article.get('date_published', '') for article in articles if article.get('date_published')]
        article_lengths = [len(article.get('article_body', '')) for article in articles]
        
        stats = {
            'total_articles': len(articles),
            'unique_authors': len(set(filter(None, authors))),
            'avg_article_length': sum(article_lengths) / len(article_lengths) if article_lengths else 0,
            'date_range': {
                'earliest': min(dates) if dates else None,
                'latest': max(dates) if dates else None
            }
        }
        
        return stats


def lambda_handler(event, context):
    """
    AWS Lambda handler function.
    
    Args:
        event: Lambda event data (can contain configuration)
        context: Lambda context object
        
    Returns:
        Dictionary containing execution results
    """
    try:
        # Log context information for debugging
        logger.info(f"Function: {context.function_name} v{context.function_version}")
        logger.info(f"Request ID: {context.aws_request_id}")
        logger.info(f"Memory limit: {context.memory_limit_in_mb}MB")
        
        # Get configuration from environment variables or event
        s3_bucket = os.environ.get('S3_BUCKET', 'amplify-readerapp-ethanpa-linguaarticlesstoragebuc-q24f1zbqsksg')
        max_articles = int(os.environ.get('MAX_ARTICLES', event.get('max_articles', 100)))
        delay = float(os.environ.get('DELAY', event.get('delay', 1.0)))
        
        logger.info(f"Lambda execution started with bucket: {s3_bucket}, max_articles: {max_articles}, delay: {delay}")
        
        # Create and run scraper
        scraper = GuardianScraperLambda(
            s3_bucket=s3_bucket,
            max_articles=max_articles,
            delay=delay
        )
        
        result = scraper.scrape_articles()
        
        # Log final results
        if result['success']:
            logger.info(f"Lambda execution completed successfully: {result['articles_scraped']} articles scraped")
        else:
            logger.error(f"Lambda execution failed: {result.get('error', 'Unknown error')}")
        
        return {
            'statusCode': 200 if result['success'] else 500,
            'body': json.dumps(result, indent=2)
        }
        
    except Exception as e:
        logger.error(f"Lambda execution failed with exception: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }
