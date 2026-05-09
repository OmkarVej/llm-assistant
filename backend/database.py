"""
SQLite Database Connection (Alternative to MySQL)
"""
import os
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime

Base = declarative_base()


class Conversation(Base):
    """Store conversation history"""
    __tablename__ = 'conversations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), nullable=True, index=True)
    session_id = Column(String(100), nullable=True, index=True)
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    source = Column(String(50))  # 'openai', 'local', etc.
    rag_used = Column(Integer, default=0)  # 0 or 1 (boolean)
    model = Column(String(100))
    tokens_used = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    meta_data = Column(JSON, nullable=True)  # Store additional context, etc.


class KnowledgeDocument(Base):
    """Store knowledge base documents"""
    __tablename__ = 'knowledge_documents'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String(255))
    doc_type = Column(String(100))  # 'api_documentation', 'compliance', etc.
    tags = Column(JSON, nullable=True)  # Array of tags
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DatabaseManager:
    """Manage SQLite database connections"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize database connection from environment variables"""
        # Try MySQL first for business data (deals, customers, etc.)
        db_host = os.environ.get('DB_HOST', 'localhost')
        db_port = os.environ.get('DB_PORT', '3306')
        db_user = os.environ.get('DB_USER', 'root')
        db_password = os.environ.get('DB_PASSWORD', '')
        db_name = os.environ.get('DB_NAME', 'client_0000000002')
        
        # Build MySQL connection string
        connection_string = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?charset=utf8mb4"
        
        try:
            from sqlalchemy.pool import QueuePool
            self.engine = create_engine(
                connection_string,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,  # Verify connections before using
                echo=False  # Set to True for SQL query logging
            )
            
            # Create session factory
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            # Test connection
            with self.engine.connect() as conn:
                pass
            
            print(f"✅ MySQL database connection initialized: {db_host}:{db_port}/{db_name}")
            print(f"   This database contains 231 business tables (deals, customers, vehicles, etc.)")
        except Exception as e:
            print(f"❌ Failed to initialize MySQL connection: {e}")
            print("   Falling back to SQLite for assistant data only...")
            
            # Fall back to SQLite for assistant data
            db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'assistant.db')
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            connection_string = f"sqlite:///{db_path}"
            
            try:
                self.engine = create_engine(connection_string, echo=False)
                self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
                Base.metadata.create_all(bind=self.engine)
                print(f"✅ SQLite fallback connection initialized: {db_path}")
                print(f"   ⚠️  WARNING: SQLite only has assistant tables (conversations, knowledge_documents)")
                print(f"   ⚠️  Business data (deals, customers) NOT available without MySQL!")
            except Exception as e2:
                print(f"❌ Failed to initialize any database connection: {e2}")
                self.engine = None
                self.SessionLocal = None
    
    def get_session(self) -> Optional[Session]:
        """Get a database session"""
        if self.SessionLocal is None:
            return None
        return self.SessionLocal()
    
    def save_conversation(self, prompt: str, response: str, source: str = 'openai', 
                         user_id: Optional[str] = None, session_id: Optional[str] = None,
                         rag_used: bool = False, model: Optional[str] = None,
                         tokens_used: Optional[int] = None, meta_data: Optional[dict] = None):
        """Save a conversation to the database"""
        if self.SessionLocal is None:
            return None
        
        session = self.get_session()
        try:
            conversation = Conversation(
                user_id=user_id,
                session_id=session_id,
                prompt=prompt,
                response=response,
                source=source,
                rag_used=1 if rag_used else 0,
                model=model,
                tokens_used=tokens_used,
                meta_data=meta_data
            )
            session.add(conversation)
            session.commit()
            return conversation.id
        except Exception as e:
            session.rollback()
            print(f"Error saving conversation: {e}")
            return None
        finally:
            session.close()
    
    def get_conversation_history(self, user_id: Optional[str] = None, 
                                session_id: Optional[str] = None, limit: int = 10):
        """Get conversation history"""
        if self.SessionLocal is None:
            return []
        
        session = self.get_session()
        try:
            query = session.query(Conversation)
            
            if user_id:
                query = query.filter(Conversation.user_id == user_id)
            if session_id:
                query = query.filter(Conversation.session_id == session_id)
            
            conversations = query.order_by(Conversation.created_at.desc()).limit(limit).all()
            return [
                {
                    'id': conv.id,
                    'prompt': conv.prompt,
                    'response': conv.response,
                    'source': conv.source,
                    'rag_used': bool(conv.rag_used),
                    'created_at': conv.created_at.isoformat() if conv.created_at else None
                }
                for conv in conversations
            ]
        except Exception as e:
            print(f"Error fetching conversation history: {e}")
            return []
        finally:
            session.close()
    
    def add_knowledge_document(self, title: str, content: str, source: str,
                              doc_type: str, tags: Optional[list] = None):
        """Add a knowledge document to the database"""
        if self.SessionLocal is None:
            return None
        
        session = self.get_session()
        try:
            doc = KnowledgeDocument(
                title=title,
                content=content,
                source=source,
                doc_type=doc_type,
                tags=tags or []
            )
            session.add(doc)
            session.commit()
            return doc.id
        except Exception as e:
            session.rollback()
            print(f"Error adding knowledge document: {e}")
            return None
        finally:
            session.close()


# Global database manager instance
db_manager = DatabaseManager()

