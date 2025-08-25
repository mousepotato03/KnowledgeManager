#!/usr/bin/env python3
"""Test script to create and verify rag_knowledge_chunks table"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def test_with_psycopg():
    """Test direct PostgreSQL connection"""
    try:
        # Extract connection details from Supabase URL
        supabase_url = os.getenv('SUPABASE_URL')
        service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        # Use direct PostgreSQL connection
        # Format: postgresql://postgres:[password]@[host]:[port]/postgres
        # For Supabase: postgresql://postgres.projectref:password@aws-0-region.pooler.supabase.com:5432/postgres
        
        # Extract project ref from URL
        project_ref = supabase_url.replace('https://', '').replace('.supabase.co', '')
        
        # Try to connect via direct PostgreSQL
        conn_string = f"postgresql://postgres:{service_key.split('.')[2]}@{project_ref}.pooler.supabase.com:5432/postgres"
        
        print("Testing PostgreSQL direct connection...")
        print(f"Connection string format: postgresql://postgres:***@{project_ref}.pooler.supabase.com:5432/postgres")
        
        # This might not work due to connection pooler, but worth trying
        # conn = psycopg2.connect(conn_string)
        # print("Direct PostgreSQL connection successful!")
        
    except Exception as e:
        print(f"Direct PostgreSQL connection failed: {e}")

def test_with_supabase():
    """Test Supabase client"""
    try:
        supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        )
        
        print("Testing Supabase connection...")
        
        # Test basic connection
        result = supabase.table('tools').select('id').limit(1).execute()
        print(f"[OK] Basic connection works - found {len(result.data)} tools")
        
        # Check if our table exists by trying to describe it
        try:
            result = supabase.table('rag_knowledge_chunks').select('*').limit(0).execute()
            print("[OK] rag_knowledge_chunks table exists")
        except Exception as e:
            print(f"[FAIL] rag_knowledge_chunks table issue: {e}")
            
            # Try to create it using raw SQL through a function if available
            create_sql = """
            CREATE TABLE IF NOT EXISTS public.rag_knowledge_chunks (
                id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                created_at timestamptz DEFAULT now(),
                tool_id uuid NOT NULL REFERENCES public.tools(id) ON DELETE CASCADE,
                source_type text NOT NULL,
                source_title text,
                chunk_index integer NOT NULL,
                content text NOT NULL,
                content_hash text NOT NULL,
                embedding vector,
                quality_score float DEFAULT NULL,
                is_active boolean DEFAULT true
            );
            """
            
            print("Attempting to create table...")
            try:
                # Try different approaches to execute SQL
                result = supabase.rpc('exec_sql', {'sql': create_sql}).execute()
                print("[OK] Table created via exec_sql")
            except Exception as e2:
                print(f"[FAIL] exec_sql failed: {e2}")
                
                # Try alternative SQL execution methods
                try:
                    result = supabase.rpc('sql', create_sql).execute()
                    print("[OK] Table created via sql rpc")
                except Exception as e3:
                    print(f"[FAIL] sql rpc failed: {e3}")
                    
                    print("\nAvailable RPC functions:")
                    try:
                        # List available functions
                        result = supabase.rpc('').execute()
                    except Exception as e4:
                        print(f"Could not list RPC functions: {e4}")
        
        return supabase
        
    except Exception as e:
        print(f"Supabase connection failed: {e}")
        return None

if __name__ == "__main__":
    print("=== RAG Table Test ===\n")
    
    # Test environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    print(f"SUPABASE_URL: {supabase_url[:50]}..." if supabase_url else "SUPABASE_URL: Not set")
    print(f"SERVICE_KEY: {'Set (' + str(len(service_key)) + ' chars)' if service_key else 'Not set'}")
    print()
    
    # Test Supabase connection
    supabase = test_with_supabase()
    
    if supabase:
        print("\n=== Testing Simple Insert ===")
        test_data = {
            'id': '550e8400-e29b-41d4-a716-446655440000',
            'tool_id': '89bce0bb-80cf-431f-88ed-3b14ee8ba24a',
            'source_type': 'text',
            'source_title': 'Test',
            'chunk_index': 0,
            'content': 'Test content for RAG system verification',
            'content_hash': 'test123',
            'quality_score': 0.8
        }
        
        try:
            result = supabase.table('rag_knowledge_chunks').insert(test_data).execute()
            print("[OK] Test insert successful!")
            print(f"Inserted: {result.data}")
            
            # Test query
            query_result = supabase.table('rag_knowledge_chunks').select('*').eq('content_hash', 'test123').execute()
            print(f"[OK] Test query successful! Found {len(query_result.data)} records")
            
            # Clean up
            supabase.table('rag_knowledge_chunks').delete().eq('content_hash', 'test123').execute()
            print("[OK] Cleanup successful")
            
        except Exception as e:
            print(f"[FAIL] Test insert failed: {e}")