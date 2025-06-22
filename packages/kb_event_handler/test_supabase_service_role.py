#!/usr/bin/env python3
"""
Test script to verify Supabase service role key is working correctly.
"""

import asyncio
import os
import sys

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from kb_event_handler.common.supabase_client import supabase_client


async def test_service_role():
    """Test if the service role key bypasses RLS correctly."""
    print("🧪 Testing Supabase Service Role Key")
    print("=" * 40)
    
    try:
        # Connect to Supabase
        await supabase_client.connect()
        print("✅ Connected to Supabase")
        
        # Test 1: Query tenants table directly (should work with service role)
        print("\n📋 Test 1: Query tenants table")
        result = supabase_client.client.from_("tenants").select("*").execute()
        
        if result.data:
            print(f"✅ Found {len(result.data)} tenants:")
            for tenant in result.data:
                print(f"   - ID: {tenant['id']}, Name: {tenant['name']}")
        else:
            print("❌ No tenants found - RLS might be blocking!")
            print("   This suggests you're using anon key instead of service role key")
        
        # Test 2: Check current database role
        print("\n🔑 Test 2: Check database authentication")
        auth_result = supabase_client.client.rpc("get_current_user_info").execute()
        print(f"Auth result: {auth_result}")
        
        # Test 3: Try to query tenant by ID (the original failing query)
        print("\n🎯 Test 3: Query tenant by ID (original failing query)")
        tenant_result = supabase_client.client.from_("tenants").select("*").eq("id", 1).execute()
        
        if tenant_result.data:
            print("✅ Successfully queried tenant by ID!")
            print(f"   Result: {tenant_result.data[0]}")
        else:
            print("❌ Failed to query tenant by ID - this is the RLS issue!")
        
        print("\n" + "=" * 40)
        if result.data and tenant_result.data:
            print("🎉 SUCCESS: Service role key is working correctly!")
            print("   Your API should now work properly.")
        else:
            print("❌ ISSUE: Service role key is not working")
            print("   Please check your SUPABASE_SERVICE_KEY environment variable")
            print("   Make sure you're using the service_role key, not the anon key")
        
    except Exception as e:
        print(f"❌ Error testing service role: {e}")
        print("\nPossible issues:")
        print("1. SUPABASE_SERVICE_KEY environment variable not set")
        print("2. Using anon key instead of service role key")
        print("3. Service role key is incorrect")
        
    finally:
        await supabase_client.disconnect()


if __name__ == "__main__":
    asyncio.run(test_service_role()) 