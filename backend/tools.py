#backend/tools.py
import aiomysql
import os
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("tools")

load_dotenv()

async def get_recent_documents():
    """Get recent federal documents from the database.
    
    Returns:
        list: List of document dictionaries with title, date, summary, and agency.
    """
    try:
        conn = await aiomysql.connect(
            host=os.getenv("MYSQL_HOST"),
            port=int(os.getenv("MYSQL_PORT")),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            db=os.getenv("MYSQL_DB")
        )
        
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT title, publication_date, summary, agency
                FROM federal_docs
                ORDER BY publication_date DESC
                LIMIT 5
            """)
            results = await cur.fetchall()
            
        conn.close()
        
        documents = [
            {
                "title": row[0],
                "date": str(row[1]),
                "summary": row[2],
                "agency": row[3]
            }
            for row in results
        ]
        
        logger.info(f"Retrieved {len(documents)} documents from database")
        return documents
        
    except Exception as e:
        logger.error(f"Error retrieving documents: {str(e)}")
        return []