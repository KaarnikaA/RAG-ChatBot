#pipelins/fetch_fed_register.py
import aiohttp
import asyncio
import aiomysql
import datetime
import os
import logging
import re
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("data_fetcher")

load_dotenv()

API_URL = "https://www.federalregister.gov/api/v1/documents.json"
DB_CONFIG = {
    'host': os.getenv("MYSQL_HOST"),
    'port': int(os.getenv("MYSQL_PORT")),
    'user': os.getenv("MYSQL_USER"),
    'password': os.getenv("MYSQL_PASSWORD"),
    'db': os.getenv("MYSQL_DB"),
}

def clean_text(text):
    """Clean and normalize text."""
    if not text:
        return "No summary available"
    
    # Replace HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Remove control characters
    text = ''.join(ch for ch in text if ch.isprintable() or ch in ['\n', '\t'])
    
    # Truncate if too long
    if len(text) > 2000:
        text = text[:2000] + "..."
        
    return text

async def fetch_data():
    """Fetch data from Federal Register API."""
    today = datetime.date.today()
    params = {
        'per_page': 15,  # Increased to 15
        'order': 'newest',
        'conditions[publication_date][gte]': str(today - datetime.timedelta(days=7)),
    }

    try:
        logger.info(f"Fetching data from {API_URL}")
        async with aiohttp.ClientSession() as session:
            async with session.get(API_URL, params=params) as resp:
                if resp.status != 200:
                    logger.error(f"API request failed with status {resp.status}")
                    return []
                    
                data = await resp.json()
                results = data.get('results', [])
                logger.info(f"Successfully fetched {len(results)} documents")
                return results
    except Exception as e:
        logger.error(f"Error fetching data: {str(e)}")
        return []

async def save_to_mysql(docs):
    """Clean and save documents to MySQL database."""
    if not docs:
        logger.warning("No documents to save")
        return 0
        
    try:
        conn = await aiomysql.connect(**DB_CONFIG)
        
        # Create table if it doesn't exist
        async with conn.cursor() as cur:
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS federal_docs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    document_id VARCHAR(255) UNIQUE,
                    title TEXT,
                    publication_date DATE,
                    summary TEXT,
                    agency TEXT,
                    fetch_date DATETIME
                )
            """)
                
        # Process and save each document
        saved_count = 0
        for doc in docs:
            try:
                # Clean the data
                doc_id = doc.get('document_number', '')
                title = clean_text(doc.get('title', 'Untitled Document'))
                summary = clean_text(doc.get('abstract', doc.get('description', 'No summary')))
                pub_date = doc.get('publication_date')
                
                # Get agency info
                agencies = doc.get('agencies', [])
                agency_name = agencies[0].get('name', 'Unknown Agency') if agencies else 'Unknown Agency'
                
                async with conn.cursor() as cur:
                    # Check if document already exists
                    await cur.execute("SELECT id FROM federal_docs WHERE document_id = %s", (doc_id,))
                    existing = await cur.fetchone()
                    
                    if existing:
                        # Update existing record
                        await cur.execute("""
                            UPDATE federal_docs 
                            SET title = %s, publication_date = %s, summary = %s, agency = %s, fetch_date = %s
                            WHERE document_id = %s
                        """, (
                            title,
                            pub_date,
                            summary,
                            agency_name,
                            datetime.datetime.now(),
                            doc_id
                        ))
                    else:
                        # Insert new record
                        await cur.execute("""
                            INSERT INTO federal_docs 
                            (document_id, title, publication_date, summary, agency, fetch_date)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (
                            doc_id,
                            title,
                            pub_date,
                            summary,
                            agency_name,
                            datetime.datetime.now()
                        ))
                        saved_count += 1
                        
            except Exception as e:
                logger.error(f"Error processing document: {str(e)}")
                continue
                
        await conn.commit()
        conn.close()
        
        logger.info(f"Successfully saved {saved_count} new documents to database")
        return saved_count
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        return 0

async def main():
    """Main function to fetch and save data."""
    try:
        logger.info("Starting data fetch process")
        data = await fetch_data()
        saved = await save_to_mysql(data)
        logger.info(f"Data fetch complete. {saved} new documents saved.")
    except Exception as e:
        logger.error(f"Error in main process: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())