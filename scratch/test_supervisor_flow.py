import frappe
from ecs_posnext.api.shifts import check_opening_shift, prepare_opening_shift
from ecs_posnext.api.pos_profile import get_user_pos_profiles

def test_supervisor_flow():
    # 1. Find a user and their POS profile
    user = frappe.db.get_value("User", {"enabled": 1}, "name")
    if not user:
        print("No enabled user found")
        return
        
    profiles = get_user_pos_profiles(user)
    if not profiles:
        print(f"No POS profiles found for user {user}")
        return
        
    profile = profiles[0]["name"]
    print(f"Testing with User: {user}, Profile: {profile}")
    
    # 2. Prepare a shift
    try:
        shift_name = prepare_opening_shift(user, profile, 500)
        print(f"Prepared shift: {shift_name}")
        
        # 3. Check if it's detected as prepared
        data = check_opening_shift(user)
        if data and data.get("is_prepared"):
            print("Successfully detected prepared shift")
            print(f"Amount: {data['pos_opening_shift'].balance_details[0].amount}")
        else:
            print("Failed to detect prepared shift")
            
        # Cleanup
        frappe.delete_doc("POS Opening Shift", shift_name)
        print("Cleaned up test shift")
        
    except Exception as e:
        print(f"Error during test: {e}")

if __name__ == "__main__":
    test_supervisor_flow()
