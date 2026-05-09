"""
Test Script for Single Deal Prediction API
==========================================

This script demonstrates how to use the new /predict/single endpoint
for real-time deal predictions.
"""

import requests
import json
from typing import Dict, Any

API_BASE_URL = "http://localhost:8000"

def test_single_prediction(deal_data: Dict[str, Any]):
    """Test single deal prediction"""
    url = f"{API_BASE_URL}/predict/single"
    
    try:
        response = requests.post(url, json=deal_data)
        
        if response.status_code == 200:
            result = response.json()
            
            print("=" * 80)
            print("🎯 SINGLE DEAL PREDICTION RESULT")
            print("=" * 80)
            print(f"\n📋 Deal ID: {result['deal_id']}")
            print(f"🏢 Dealership: {result['dealership_name']}")
            print(f"🚗 Vehicle Type: {result['vehicle_type']}")
            print(f"📦 Product: {result['product_name']}")
            
            print(f"\n💰 FINANCIAL DETAILS:")
            print(f"   Cost: ${result['cost']:,.2f}")
            print(f"   Selling Price: ${result['selling_price']:,.2f}")
            print(f"   Profit Margin: ${result['profit_margin']:,.2f} ({result['profit_margin_pct']:.1f}%)")
            
            print(f"\n💳 FINANCING DETAILS:")
            print(f"   Amount Financed: ${result['pc_amount_financed']:,.2f}")
            print(f"   Down Payment: ${result['pc_down_payment']:,.2f}")
            print(f"   Rate: {result['pc_rate']}%")
            print(f"   Term: {result['pc_term']} months")
            print(f"   Monthly Payment: ${result['monthly_payment']:,.2f}")
            print(f"   Total Interest: ${result['total_interest']:,.2f}")
            
            print(f"\n🎯 PREDICTION:")
            print(f"   Result: {result['prediction']}")
            print(f"   Confidence: {result['confidence_percentage']}")
            print(f"   Will Sell Fast: {'✅ YES' if result['will_sell_fast'] else '❌ NO'}")
            print(f"   Risk Level: {result['risk_level']}")
            
            print(f"\n📊 KEY FACTORS:")
            for factor in result['key_factors']:
                print(f"   {factor}")
            
            print(f"\n💡 RECOMMENDATION:")
            print(f"   {result['recommendation']}")
            
            print("\n" + "=" * 80)
            
            return result
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.json())
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to API. Make sure the server is running.")
        print("   Start the server with: python api_improved.py")
        return None
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def test_health_check():
    """Test API health"""
    url = f"{API_BASE_URL}/"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            result = response.json()
            print("✅ API is running!")
            print(f"   Version: {result['version']}")
            print(f"   Model Loaded: {result['model_loaded']}")
            return True
        return False
    except:
        print("❌ API is not running. Start with: python api_improved.py")
        return False

def test_model_info():
    """Get model information"""
    url = f"{API_BASE_URL}/model/info"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            result = response.json()
            print("\n📊 MODEL INFORMATION:")
            print(f"   Accuracy: {result['accuracy']:.4f}")
            print(f"   ROC-AUC: {result['roc_auc_score']:.4f}")
            print(f"   F1-Score: {result['f1_score']:.4f}")
            print(f"   CV Mean: {result['cv_mean_score']:.4f}")
            print(f"   Features: {result['feature_count']}")
            print(f"   Trained: {result['training_date']}")
            return result
        return None
    except Exception as e:
        print(f"❌ Could not get model info: {str(e)}")
        return None

# ==================== TEST SCENARIOS ====================

def scenario_1_high_value_deal():
    """Scenario 1: High-value deal with excellent margins"""
    print("\n" + "=" * 80)
    print("TEST SCENARIO 1: High-Value Deal with Excellent Profit Margin")
    print("=" * 80)
    
    deal = {
        "dealership_name": "Premium Motors",
        "vehicle_type_name": "New",
        "deal_type_report_type": "Retail",
        "pc_amount_financed": 45000.0,
        "pc_term": 84,
        "pc_rate": 3.9,
        "pc_down_payment": 10000.0,
        "pc_lender_code": "PREMIUM_LENDER",
        "deal_status": "Active",
        "product_category_name": "Vehicle Service Contract",
        "product_name": "Premium Extended Warranty",
        "cost": 1200.0,
        "selling_price": 4800.0,
        "deal_id": "TEST_001",
        "vin": "1HGBH41JXMN109186"
    }
    
    return test_single_prediction(deal)

def scenario_2_moderate_deal():
    """Scenario 2: Moderate deal with average terms"""
    print("\n" + "=" * 80)
    print("TEST SCENARIO 2: Moderate Deal with Average Terms")
    print("=" * 80)
    
    deal = {
        "dealership_name": "City Auto Sales",
        "vehicle_type_name": "Used",
        "deal_type_report_type": "Retail",
        "pc_amount_financed": 25000.0,
        "pc_term": 60,
        "pc_rate": 6.5,
        "pc_down_payment": 3000.0,
        "pc_lender_code": "STANDARD_LENDER",
        "deal_status": "Active",
        "product_category_name": "GAP",
        "product_name": "GAP Insurance",
        "cost": 400.0,
        "selling_price": 1200.0,
        "deal_id": "TEST_002",
        "vin": "2HGBH41JXMN109187"
    }
    
    return test_single_prediction(deal)

def scenario_3_low_margin_deal():
    """Scenario 3: Low margin deal with poor terms"""
    print("\n" + "=" * 80)
    print("TEST SCENARIO 3: Low Margin Deal with Challenging Terms")
    print("=" * 80)
    
    deal = {
        "dealership_name": "Budget Auto",
        "vehicle_type_name": "Used",
        "deal_type_report_type": "Wholesale",
        "pc_amount_financed": 15000.0,
        "pc_term": 36,
        "pc_rate": 9.5,
        "pc_down_payment": 1000.0,
        "pc_lender_code": "BUDGET_LENDER",
        "deal_status": "Active",
        "product_category_name": "Paint Protection",
        "product_name": "Basic Paint Protection",
        "cost": 800.0,
        "selling_price": 1000.0,
        "deal_id": "TEST_003",
        "vin": "3HGBH41JXMN109188"
    }
    
    return test_single_prediction(deal)

def scenario_4_cancelled_deal():
    """Scenario 4: Previously cancelled deal"""
    print("\n" + "=" * 80)
    print("TEST SCENARIO 4: Previously Cancelled Deal")
    print("=" * 80)
    
    deal = {
        "dealership_name": "Express Auto",
        "vehicle_type_name": "New",
        "deal_type_report_type": "Retail",
        "pc_amount_financed": 30000.0,
        "pc_term": 72,
        "pc_rate": 5.5,
        "pc_down_payment": 5000.0,
        "pc_lender_code": "EXPRESS_LENDER",
        "deal_status": "Cancelled",
        "product_category_name": "Tire & Wheel Protection",
        "product_name": "Wheel Protection Plan",
        "cost": 600.0,
        "selling_price": 2000.0,
        "deal_id": "TEST_004",
        "vin": "4HGBH41JXMN109189"
    }
    
    return test_single_prediction(deal)

def compare_deals():
    """Compare multiple deals side by side"""
    print("\n" + "=" * 80)
    print("🔄 COMPARING MULTIPLE DEALS")
    print("=" * 80)
    
    scenarios = [
        ("High-Value Deal", scenario_1_high_value_deal),
        ("Moderate Deal", scenario_2_moderate_deal),
        ("Low-Margin Deal", scenario_3_low_margin_deal),
        ("Cancelled Deal", scenario_4_cancelled_deal)
    ]
    
    results = []
    for name, scenario_func in scenarios:
        result = scenario_func()
        if result:
            results.append((name, result))
    
    if results:
        print("\n" + "=" * 80)
        print("📊 COMPARISON SUMMARY")
        print("=" * 80)
        print(f"\n{'Deal Type':<20} {'Prediction':<25} {'Confidence':<12} {'Risk Level':<15}")
        print("-" * 80)
        
        for name, result in results:
            print(f"{name:<20} {result['prediction']:<25} {result['confidence_percentage']:<12} {result['risk_level']:<15}")

def main():
    """Run all tests"""
    print("\n" + "🚀 " * 20)
    print("SINGLE DEAL PREDICTION API - TEST SUITE")
    print("🚀 " * 20)
    
    # Check API health
    if not test_health_check():
        return
    
    # Get model info
    test_model_info()
    
    # Run individual scenarios
    input("\n\nPress Enter to run test scenarios...")
    
    scenario_1_high_value_deal()
    input("\nPress Enter to continue...")
    
    scenario_2_moderate_deal()
    input("\nPress Enter to continue...")
    
    scenario_3_low_margin_deal()
    input("\nPress Enter to continue...")
    
    scenario_4_cancelled_deal()
    input("\nPress Enter to see comparison...")
    
    # Compare all deals
    compare_deals()
    
    print("\n\n✅ All tests completed!")
    print("\n💡 TIP: You can modify the deal parameters in this script to test different scenarios.")
    print("💡 TIP: Use this endpoint in your application for real-time deal predictions!")

if __name__ == "__main__":
    main()

