#!/usr/bin/env python3
"""
Improved Guardian News Article Scraper

This script scrapes articles from The Guardian's sitemap and saves them to CSV.
Improvements include error handling, configuration, logging, and better code structure.
"""

import csv
import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional
import argparse
import sys
import os

import pandas as pd
import requests
from bs4 import BeautifulSoup
from newsplease import NewsPlease


def generate_timestamped_filename(base_filename: str) -> str:
    """
    Generate a filename with UTC timestamp suffix.
    
    Args:
        base_filename: Base filename (e.g., 'guardian_data.csv')
        
    Returns:
        Filename with UTC timestamp suffix (e.g., 'guardian_data_20250918_055938.csv')
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    name, ext = os.path.splitext(base_filename)
    return f"{name}_{timestamp}{ext}"


class GuardianScraper:
    """A robust scraper for Guardian news articles."""
    
    def __init__(self, max_articles: int = 10, delay: float = 1.0, output_file: str = "guardian_data.csv"):
        """
        Initialize the scraper.
        
        Args:
            max_articles: Maximum number of articles to scrape
            delay: Delay between requests in seconds (rate limiting)
            output_file: Output CSV filename
        """
        self.max_articles = max_articles
        self.delay = delay
        self.output_file = output_file
        self.sitemap_url = "https://www.theguardian.com/sitemaps/news.xml"
        
        # Setup logging with UTC timestamped filename
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        log_filename = f"get_articles_guardian_log_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.log_filename = log_filename  # Store for reference
        
    def fetch_sitemap_urls(self) -> List[Dict[str, str]]:
        """
        Fetch and parse The Guardian's sitemap to extract article URLs.
        
        Returns:
            List of dictionaries containing URL and last modified date
            
        Raises:
            requests.RequestException: If sitemap cannot be fetched
            Exception: If sitemap cannot be parsed
        """
        self.logger.info(f"Fetching sitemap from {self.sitemap_url}")
        
        try:
            response = requests.get(self.sitemap_url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch sitemap: {e}")
            raise
            
        try:
            soup = BeautifulSoup(response.text, 'xml')
            urls = []
            
            for url_element in soup.find_all('url'):
                loc_element = url_element.find('loc')
                lastmod_element = url_element.find('lastmod')
                
                if loc_element and lastmod_element:
                    urls.append({
                        'url': loc_element.text.strip(),
                        'last_modified': lastmod_element.text.strip()
                    })
                    
            self.logger.info(f"Found {len(urls)} URLs in sitemap")
            return urls
            
        except Exception as e:
            self.logger.error(f"Failed to parse sitemap: {e}")
            raise
            
    def extract_article_data(self, url: str) -> Optional[Dict[str, str]]:
        """
        Extract article data from a single URL using NewsPlease.
        
        Args:
            url: Article URL to scrape
            
        Returns:
            Dictionary containing article data, or None if extraction fails
        """
        try:
            self.logger.debug(f"Extracting article from: {url}")
            article = NewsPlease.from_url(url)
            
            if not article or not article.title:
                self.logger.warning(f"No valid article found at {url}")
                return None
                
            # Extract and clean data
            data = {
                'headline': article.title or '',
                'article_body': article.maintext or '',
                'author_name': ', '.join(article.authors) if article.authors else '',
                'date_published': article.date_publish.isoformat() if article.date_publish else '',
                'language': article.language or '',
                'source': article.source_domain or '',
                'url': article.url or url
            }
            
            # Validate essential fields
            if not data['headline'] or not data['article_body']:
                self.logger.warning(f"Article missing essential content: {url}")
                return None
                
            return data
            
        except Exception as e:
            self.logger.error(f"Failed to extract article from {url}: {e}")
            return None
            
    def scrape_articles(self) -> int:
        """
        Main scraping function that coordinates the entire process.
        
        Returns:
            Number of articles successfully scraped
        """
        self.logger.info(f"Starting scrape of up to {self.max_articles} articles")
        
        # Get URLs from sitemap
        try:
            url_data = self.fetch_sitemap_urls()
        except Exception as e:
            self.logger.error(f"Cannot proceed without sitemap data: {e}")
            return 0
            
        if not url_data:
            self.logger.error("No URLs found in sitemap")
            return 0
            
        # Prepare CSV file
        fieldnames = ['headline', 'article_body', 'author_name', 'date_published', 'language', 'source', 'url']
        articles_scraped = 0
        
        try:
            with open(self.output_file, 'w', newline='', encoding='utf-8') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                writer.writeheader()
                
                # Process articles
                for i, url_info in enumerate(url_data):
                    if articles_scraped >= self.max_articles:
                        break
                        
                    url = url_info['url']
                    article_data = self.extract_article_data(url)
                    
                    if article_data:
                        writer.writerow(article_data)
                        articles_scraped += 1
                        self.logger.info(f"Scraped article {articles_scraped}/{self.max_articles}: {article_data['headline'][:50]}...")
                    
                    # Rate limiting
                    if i < len(url_data) - 1:  # Don't delay after the last request
                        time.sleep(self.delay)
                        
        except IOError as e:
            self.logger.error(f"Failed to write to CSV file: {e}")
            return articles_scraped
            
        self.logger.info(f"Scraping completed. {articles_scraped} articles saved to {self.output_file}")
        return articles_scraped
        
    def get_stats(self) -> Dict[str, any]:
        """
        Get statistics about the scraped data.
        
        Returns:
            Dictionary containing scraping statistics
        """
        try:
            df = pd.read_csv(self.output_file)
            return {
                'total_articles': len(df),
                'unique_authors': df['author_name'].nunique(),
                'date_range': {
                    'earliest': df['date_published'].min(),
                    'latest': df['date_published'].max()
                },
                'avg_article_length': df['article_body'].str.len().mean()
            }
        except Exception as e:
            self.logger.error(f"Failed to generate statistics: {e}")
            return {}


def main():
    """Main function with command line argument parsing."""
    parser = argparse.ArgumentParser(description='Scrape Guardian news articles')
    parser.add_argument('--max-articles', type=int, default=100, 
                       help='Maximum number of articles to scrape (default: 100)')
    parser.add_argument('--delay', type=float, default=1.0,
                       help='Delay between requests in seconds (default: 1.0)')
    parser.add_argument('--output', type=str, default='guardian_data.csv',
                       help='Output CSV filename (default: guardian_data.csv)')
    parser.add_argument('--no-timestamp', action='store_true',
                       help='Disable automatic timestamp suffix in filename')
    
    args = parser.parse_args()
    
    # Generate timestamped filename unless disabled
    output_file = args.output
    if not args.no_timestamp:
        output_file = generate_timestamped_filename(args.output)
        print(f"Output will be saved to: {output_file}")
    
    # Create and run scraper
    scraper = GuardianScraper(
        max_articles=args.max_articles,
        delay=args.delay,
        output_file=output_file
    )
    
    try:
        articles_count = scraper.scrape_articles()
        
        if articles_count > 0:
            stats = scraper.get_stats()
            print("\n=== Scraping Statistics ===")
            for key, value in stats.items():
                print(f"{key}: {value}")
                
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
    except Exception as e:
        print(f"Scraping failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
