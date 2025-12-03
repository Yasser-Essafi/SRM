"""
Quick test to verify all imports and basic functionality.
Run this to ensure the setup is correct before running the main app.
"""

print("🔍 Testing SRM Application Setup...\n")

# Test 1: Config imports
print("1️⃣ Testing config module...")
try:
    from config.settings import settings
    print("   ✅ Config module imported")
    is_valid, missing = settings.validate()
    if is_valid:
        print("   ✅ All environment variables configured")
    else:
        print(f"   ⚠️  Missing environment variables: {', '.join(missing)}")
        print("   💡 Please configure .env file")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Data module
print("\n2️⃣ Testing data module...")
try:
    from data.mock_db import get_user_by_cil, get_zone_by_id
    user = get_user_by_cil("12345678")
    print(f"   ✅ Data module works - Found user: {user['name']}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Services module
print("\n3️⃣ Testing services module...")
try:
    from services.ai_service import _check_payment_impl, _check_maintenance_impl, initialize_agent
    print("   ✅ AI service imported")
    
    # Test tools directly
    result = _check_payment_impl("12345678")
    if "أحمد" in result:
        print("   ✅ check_payment tool works")
    
    result = _check_maintenance_impl("12345678")
    if "منطقتك" in result:
        print("   ✅ check_maintenance tool works")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: OCR service
print("\n4️⃣ Testing OCR service...")
try:
    from services.ocr_service import extract_cil_from_image
    print("   ✅ OCR service imported")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 5: UI module
print("\n5️⃣ Testing UI module...")
try:
    from ui.layout import render_header, inject_rtl_css
    from ui.chat_interface import render_chat_interface
    print("   ✅ UI module imported")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 6: Main app
print("\n6️⃣ Testing main app...")
try:
    import app
    print("   ✅ Main app module imported")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "="*50)
print("✅ All basic tests passed!")
print("="*50)
print("\n💡 Next step: Run 'streamlit run app.py' to start the application")
