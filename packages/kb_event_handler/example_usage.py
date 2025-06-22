#!/usr/bin/env python3
"""
Example usage of the /v1/ingest endpoint

This script demonstrates how to call the ingestion API endpoint.
"""

import asyncio
import json
import os

import httpx


async def example_ingest_request():
    """Example of making an ingestion request."""
    print("📝 Example: Calling /v1/ingest endpoint")
    print("=" * 40)
    
    # API configuration
    base_url = "http://localhost:8000"
    api_key = "your-api-key-here"  # Replace with actual API key
    tenant_id = "123"  # Replace with actual tenant ID
    
    # Request payload
    payload = {
        "file_path": "tenant_123/kb_456/documents/quarterly_report.pdf",
        "filename": "quarterly_report.pdf",
        "knowledge_base_id": 456,
        "mime_type": "application/pdf",
        "chunk_size": 1024,
        "chunk_overlap": 200
    }
    
    # Headers
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key,
        "X-Tenant-ID": tenant_id,
    }
    
    print(f"🌐 Making request to: {base_url}/api/v1/v1/ingest")
    print(f"📄 File: {payload['filename']}")
    print(f"🗂️  Knowledge Base ID: {payload['knowledge_base_id']}")
    print(f"📊 Chunk Size: {payload['chunk_size']}")
    print()
    
    # Note: This is just an example - the server needs to be running
    # and properly configured with environment variables
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/api/v1/v1/ingest",
                json=payload,
                headers=headers,
                timeout=30.0
            )
            
            if response.status_code == 202:
                result = response.json()
                print("✅ Ingestion job created successfully!")
                print(f"🆔 Job ID: {result['job_id']}")
                print(f"📊 Status: {result['status']}")
                print(f"📅 Created: {result['created_at']}")
                print(f"📁 File: {result['filename']}")
                
            else:
                print(f"❌ Request failed with status {response.status_code}")
                print(f"Response: {response.text}")
                
    except httpx.ConnectError:
        print("❌ Could not connect to server. Make sure it's running:")
        print("   python -m uvicorn src.kb_event_handler.main:app --reload")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def show_curl_example():
    """Show equivalent curl command."""
    print("\n" + "=" * 40)
    print("📋 Equivalent curl command:")
    print("=" * 40)
    
    curl_cmd = '''curl -X POST "http://localhost:8000/api/v1/v1/ingest" \\
     -H "Content-Type: application/json" \\
     -H "X-API-Key: your-api-key-here" \\
     -H "X-Tenant-ID: 123" \\
     -d '{
       "file_path": "tenant_123/kb_456/documents/quarterly_report.pdf",
       "filename": "quarterly_report.pdf", 
       "knowledge_base_id": 456,
       "mime_type": "application/pdf",
       "chunk_size": 1024,
       "chunk_overlap": 200
     }'
    '''
    
    print(curl_cmd)


def show_requirements():
    """Show what's needed to use the endpoint."""
    print("\n" + "=" * 40)
    print("📋 Requirements for using /v1/ingest:")
    print("=" * 40)
    
    print("1. 🔧 Server Setup:")
    print("   - Set environment variables (SUPABASE_URL, SUPABASE_KEY, etc.)")
    print("   - Start server: python -m uvicorn src.kb_event_handler.main:app --reload")
    print()
    
    print("2. 🗄️  Database Setup:")
    print("   - Tenant must exist in 'tenants' table")
    print("   - Knowledge base must exist and belong to tenant")
    print()
    
    print("3. 📁 File Setup:")
    print("   - File must be uploaded to Supabase Storage first")
    print("   - Supported formats: PDF, DOC/DOCX, PPT/PPTX, MD")
    print("   - Maximum size: 25MB")
    print()
    
    print("4. 🔑 Authentication:")
    print("   - Valid API key in X-API-Key header")
    print("   - Valid tenant ID in X-Tenant-ID header")
    print()
    
    print("5. 🎯 Response:")
    print("   - Returns job ID for tracking progress")
    print("   - Processing happens in background")
    print("   - Job status stored in 'kb_jobs' table")


async def main():
    """Run the example."""
    print("🚀 KB Event Handler - Ingestion API Example")
    
    await example_ingest_request()
    show_curl_example()
    show_requirements()
    
    print("\n" + "=" * 40)
    print("📚 For more info, visit: http://localhost:8000/api/v1/docs")


if __name__ == "__main__":
    asyncio.run(main()) 