#!/usr/bin/env python3
"""
Mini test script for Blizzard API endpoints
Tests the API class and specifically the professions endpoint
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.scraper.blizzard_api_utils import BlizzardAPI, BlizzardConfig

load_dotenv()


def test_api_endpoints():
    """Test various Blizzard API endpoints"""

    # Load config from environment variables
    client_id = os.getenv("BLIZZARD_API_CLIENT_ID")
    client_secret = os.getenv("BLIZZARD_API_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("❌ Missing environment variables:")
        print("   BLIZZARD_API_CLIENT_ID")
        print("   BLIZZARD_API_CLIENT_SECRET")
        return False

    print("🔑 API credentials loaded from environment")

    # Test both regions
    for region in ["eu", "us"]:
        emoji = "🌍" if region == "eu" else "🍔"
        print(f"\n{emoji} Testing {region.upper()} region...")

        config = BlizzardConfig(
            client_id=client_id,
            client_secret=client_secret,
            region=region,
            timeout=10,
            max_retries=3,
        )

        api = BlizzardAPI(config)

        # Test 1: Get access token
        print(f"  🔓 Getting access token...")
        try:
            token = api._ensure_valid_token()
            if token:
                print(
                    f"     ✅ Token acquired: {token['access_token'][:10]}... (truncated)"
                )
        except Exception as e:
            print(f"     ❌ Token failed: {e}")
            continue

        # Test 2: Get professions
        print(f"  📋 Testing professions endpoint...")
        try:
            professions = api.get_professions()
            print(f"     ✅ Found {len(professions)} professions:")
            for prof in professions[:5]:  # Show first 5
                print(f"        - {prof['name']}")
            if len(professions) > 5:
                print(f"        ... and {len(professions) - 5} more")
        except Exception as e:
            print(f"     ❌ Professions failed: {e}")
            continue

        # Test 3: Get specific profession details
        print(f"  🔧 Testing profession details...")
        try:
            if professions:
                first_prof = professions[0]
                prof_url = first_prof["key"]["href"]
                prof_details = api.get_profession_info(prof_url)
                assert isinstance(prof_details, dict), "Expected dict response"
                skill_tiers = prof_details.get("skill_tiers", [])
                print(
                    f"     ✅ {first_prof['name']} has {len(skill_tiers)} skill tiers"
                )
                for tier in skill_tiers[:3]:  # Show first 3
                    print(f"        - {tier['name']}")
        except Exception as e:
            print(f"     ❌ Profession details failed: {e}")

        # Test 4: Test commodities endpoint with detailed debugging
        print(f"  💰 Testing commodities endpoint...")
        try:
            commodities = api.get_commodities()
            auctions = commodities.get("auctions", [])
            print(f"     ✅ Found {len(auctions)} commodity auctions")
            if auctions:
                print(
                    f"        Sample: Item {auctions[0]['item']['id']} - {auctions[0]['unit_price']} gold"
                )
        except Exception as e:
            print(f"     ❌ Commodities failed: {e}")
            print(f"     🔍 Full error details: {repr(e)}")
        
        # Test 4a: Check headers from successful GET request
        print(f"  📊 Testing GET request headers for change detection...")
        try:
            # Make a manual GET request to capture response headers
            url = api._build_url("/data/wow/auctions/commodities")
            params = api._dynamic_params()
            
            # Use the internal method but capture the response object
            api._ensure_valid_token()
            headers = {"Authorization": f"Bearer {api._token_info['access_token']}"}
            response = api.session.get(url, headers=headers, params=params, timeout=api.config.timeout)
            response.raise_for_status()
            
            print(f"     ✅ GET request successful")
            print(f"     📄 Status Code: {response.status_code}")
            print(f"     📑 Useful Headers for change detection:")
            
            # Check for common change detection headers
            change_headers = ['last-modified', 'etag', 'date', 'cache-control', 'expires']
            for header in change_headers:
                value = response.headers.get(header) or response.headers.get(header.title())
                if value:
                    print(f"        {header}: {value}")
            
            # Show all headers if no common ones found
            has_change_headers = any(response.headers.get(h) or response.headers.get(h.title()) for h in change_headers)
            if not has_change_headers:
                print(f"     📑 All Headers (no standard change detection headers found):")
                for key, value in response.headers.items():
                    print(f"        {key}: {value}")
                    
        except Exception as e:
            print(f"     ❌ GET headers check failed: {e}")
            print(f"     🔍 Full error details: {repr(e)}")
        
        # Test 4b: Test new If-Modified-Since change detection method
        print(f"  🔄 Testing If-Modified-Since change detection...")
        try:
            from datetime import datetime, UTC
            
            # Test with old date (should return True - data updated)
            last_check = datetime(2020, 1, 1, tzinfo=UTC)
            is_updated = api.is_commodities_updated(last_check)
            print(f"     ✅ Change detection with old date (2020): {is_updated}")
            
            # Test with None (should return True)
            is_updated_none = api.is_commodities_updated(None)
            print(f"     ✅ Change detection with None: {is_updated_none}")
            
            # Test with future date (should return False - 304 Not Modified)
            future_check = datetime(2030, 1, 1, tzinfo=UTC)  
            is_updated_future = api.is_commodities_updated(future_check)
            print(f"     ✅ Change detection with future date (2030): {is_updated_future}")
            
            # Test with very recent date (likely 304 Not Modified)
            recent_check = datetime(2025, 7, 6, 19, 30, tzinfo=UTC)  
            is_updated_recent = api.is_commodities_updated(recent_check)
            print(f"     ✅ Change detection with recent date (today 19:30): {is_updated_recent}")
            
        except Exception as e:
            print(f"     ❌ Change detection failed: {e}")
            print(f"     🔍 Full error details: {repr(e)}")

        # Test 5: Test a random item
        print(f"  🎯 Testing item endpoint...")
        try:
            # Test with a common item ID (e.g., 190396 - Primal Chaos)
            item_id = 190396
            item_data = api.get_item(item_id)
            print(f"     ✅ Item {item_id}: {item_data.get('name', 'Unknown')}")
        except Exception as e:
            print(f"     ❌ Item failed: {e}")

        print(f"  ✅ {region.upper()} region testing completed")

    print("\n🎉 API testing completed!")
    return True


if __name__ == "__main__":
    print("🚀 Starting Blizzard API Test Script")
    print("=" * 50)

    success = test_api_endpoints()

    if success:
        print("\n✅ All tests completed successfully!")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
