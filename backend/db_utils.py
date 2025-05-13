import asyncio
import aiomysql
import os
import datetime
from dotenv import load_dotenv

load_dotenv()

async def get_last_update_date():
    """Get the date when the database was last updated."""
    try:
        conn = await aiomysql.connect(
            host=os.getenv("MYSQL_HOST"),
            port=int(os.getenv("MYSQL_PORT")),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            db=os.getenv("MYSQL_DB")
        )
        
        async with conn.cursor() as cur:
            # Check if table exists first
            await cur.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = %s 
                AND table_name = 'federal_docs'
            """, (os.getenv("MYSQL_DB"),))
            
            if (await cur.fetchone())[0] == 0:
                conn.close()
                return None
            
            # Get the most recent publication date
            await cur.execute("""
                SELECT MAX(publication_date) as last_update
                FROM federal_docs
            """)
            result = await cur.fetchone()
            
            # Get the row count
            await cur.execute("""
                SELECT COUNT(*) as total_documents
                FROM federal_docs
            """)
            count_result = await cur.fetchone()
            
        conn.close()
        
        if result and result[0]:
            return {
                "last_document_date": result[0].isoformat(),
                "total_documents": count_result[0] if count_result else 0,
                "last_fetch": datetime.datetime.now().isoformat()
            }
        return None
    except Exception as e:
        print(f"Error getting last update date: {str(e)}")
        return None