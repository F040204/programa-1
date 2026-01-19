#!/usr/bin/env python
"""Quick test to verify the new routes are accessible"""

from app import app

def test_routes():
    """Test that the new image viewer routes exist"""
    with app.test_client() as client:
        # Test routes exist (they will redirect to login since we're not authenticated)
        routes_to_test = [
            '/image-viewer',
            '/api/refresh-images',
        ]
        
        for route in routes_to_test:
            response = client.get(route, follow_redirects=False)
            # Should redirect to login (302) since we need authentication
            print(f"Route {route}: Status {response.status_code}")
            assert response.status_code in [302, 405], f"Route {route} should redirect to login or reject GET (got {response.status_code})"
        
        print("\n✓ All route tests passed!")

if __name__ == '__main__':
    test_routes()
