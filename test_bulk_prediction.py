"""
Bulk Prediction Test Script
============================

This script demonstrates how to use the bulk prediction endpoints
for analyzing multiple deals at once.
"""

import requests
import json
import os
from typing import Optional

API_BASE_URL = "http://localhost:8000"

def test_bulk_prediction_from_csv(csv_file_path: str):
    """Test bulk prediction with CSV file"""
    
    if not os.path.exists(csv_file_path):
        print(f"❌ Error: File not found: {csv_file_path}")
        return None
    
    url = f"{API_BASE_URL}/predict"
    
    try:
        with open(csv_file_path, 'rb') as f:
            files = {'file': (os.path.basename(csv_file_path), f, 'text/csv')}
            response = requests.post(url, files=files)
        
        if response.status_code == 200:
            result = response.json()
            
            print("=" * 80)
            print("📊 BULK PREDICTION RESULTS")
            print("=" * 80)
            
            print(f"\n📈 SUMMARY:")
            print(f"   Total Predictions: {result['total_predictions']}")
            print(f"   Selling Fast: {result['selling_fast_count']} ({result['percentage_selling_fast']:.1f}%)")
            print(f"   Not Selling Fast: {result['not_selling_fast_count']}")
            print(f"   Average Confidence: {result['average_confidence']:.4f}")
            print(f"   Timestamp: {result['timestamp']}")
            
            print(f"\n🏆 TOP 10 PREDICTIONS (by confidence):")
            print(f"\n{'Rank':<6} {'Deal ID':<10} {'Product Category':<30} {'Prediction':<25} {'Confidence':<12}")
            print("-" * 90)
            
            for idx, pred in enumerate(result['top_predictions'][:10], 1):
                print(f"{idx:<6} {pred['deal_id']:<10} {pred['product_category']:<30} {pred['prediction']:<25} {pred['confidence']:.4f}")
            
            # Category summary
            if result['summary_by_category']:
                print(f"\n📦 SUMMARY BY PRODUCT CATEGORY:")
                print(f"\n{'Category':<35} {'Total':<10} {'Selling Fast':<15} {'Percentage':<12} {'Avg Conf':<10}")
                print("-" * 90)
                
                for category, stats in sorted(result['summary_by_category'].items(), 
                                              key=lambda x: x[1]['selling_fast'], reverse=True):
                    print(f"{category:<35} {stats['total']:<10} {stats['selling_fast']:<15} "
                          f"{stats['percentage']:.1f}%{'':<7} {stats['avg_confidence']:.4f}")
            
            # Dealership summary
            if result['summary_by_dealership']:
                print(f"\n🏢 TOP 10 DEALERSHIPS (by selling fast count):")
                print(f"\n{'Dealership':<35} {'Total':<10} {'Selling Fast':<15} {'Percentage':<12} {'Avg Conf':<10}")
                print("-" * 90)
                
                for dealership, stats in list(result['summary_by_dealership'].items())[:10]:
                    print(f"{dealership:<35} {stats['total']:<10} {stats['selling_fast']:<15} "
                          f"{stats['percentage']:.1f}%{'':<7} {stats['avg_confidence']:.4f}")
            
            print("\n" + "=" * 80)
            
            return result
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.json())
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to API. Make sure the server is running.")
        return None
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def test_download_results(csv_file_path: str, output_file: Optional[str] = None):
    """Download prediction results as CSV"""
    
    if not os.path.exists(csv_file_path):
        print(f"❌ Error: File not found: {csv_file_path}")
        return None
    
    url = f"{API_BASE_URL}/predict/download"
    
    if output_file is None:
        output_file = "prediction_results_downloaded.csv"
    
    try:
        with open(csv_file_path, 'rb') as f:
            files = {'file': (os.path.basename(csv_file_path), f, 'text/csv')}
            response = requests.post(url, files=files)
        
        if response.status_code == 200:
            with open(output_file, 'wb') as f:
                f.write(response.content)
            
            print("=" * 80)
            print("📥 DOWNLOAD RESULTS")
            print("=" * 80)
            print(f"\n✅ Results saved to: {output_file}")
            print(f"   File size: {len(response.content)} bytes")
            
            # Read and show summary
            import pandas as pd
            df = pd.read_csv(output_file)
            
            print(f"\n📊 FILE SUMMARY:")
            print(f"   Total rows: {len(df)}")
            print(f"   Columns: {len(df.columns)}")
            
            if 'prediction_label' in df.columns:
                print(f"\n   Prediction Distribution:")
                print(df['prediction_label'].value_counts())
            
            print("\n" + "=" * 80)
            
            return output_file
        else:
            print(f"❌ Error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def test_deal_specific_analysis(csv_file_path: str):
    """Test deal-specific analysis"""
    
    if not os.path.exists(csv_file_path):
        print(f"❌ Error: File not found: {csv_file_path}")
        return None
    
    url = f"{API_BASE_URL}/analyze/deal-specific"
    
    try:
        with open(csv_file_path, 'rb') as f:
            files = {'file': (os.path.basename(csv_file_path), f, 'text/csv')}
            response = requests.post(url, files=files)
        
        if response.status_code == 200:
            result = response.json()
            
            print("=" * 80)
            print("🔍 DEAL-SPECIFIC ANALYSIS")
            print("=" * 80)
            
            print(f"\n📊 SUMMARY:")
            print(f"   Total Deals: {result['total_deals_analyzed']}")
            print(f"   Selling Fast: {result['selling_fast_count']}")
            print(f"   Not Selling: {result['not_selling_count']}")
            
            print(f"\n🎯 TOP 5 DEAL ANALYSES:")
            
            for idx, deal in enumerate(result['deals'][:5], 1):
                print(f"\n{'─' * 80}")
                print(f"Deal #{idx}: {deal['deal_id']}")
                print(f"{'─' * 80}")
                print(f"🏢 Dealership: {deal['dealership_name']}")
                print(f"🚗 Vehicle: {deal['vehicle_type']}")
                print(f"📦 Product: {deal['product_name']}")
                
                print(f"\n💰 Deal Analysis:")
                analysis = deal['deal_analysis']
                print(f"   Cost: ${analysis['cost']:,.2f}")
                print(f"   Selling Price: ${analysis['selling_price']:,.2f}")
                print(f"   Profit Margin: ${analysis['profit_margin']:,.2f} ({analysis['profit_margin_pct']:.1f}%)")
                print(f"   Financing: ${analysis['pc_amount_financed']:,.2f} @ {analysis['pc_rate']}% for {analysis['pc_term']} months")
                
                print(f"\n🎯 Prediction:")
                pred = deal['prediction']
                print(f"   {pred['text']}")
                
                print(f"\n📋 Why {'Selling Fast' if pred['will_sell_fast'] else 'Not Selling'}:")
                for reason in deal['why_selling_fast']:
                    print(f"   {reason}")
                
                print(f"\n💡 Optimization:")
                for key, value in deal['optimization'].items():
                    print(f"   {key.replace('_', ' ').title()}: {value}")
            
            print("\n" + "=" * 80)
            
            return result
        else:
            print(f"❌ Error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def test_deal_summary_text(csv_file_path: str):
    """Test deal summary in text format"""
    
    if not os.path.exists(csv_file_path):
        print(f"❌ Error: File not found: {csv_file_path}")
        return None
    
    url = f"{API_BASE_URL}/analyze/deal-summary-text"
    
    try:
        with open(csv_file_path, 'rb') as f:
            files = {'file': (os.path.basename(csv_file_path), f, 'text/csv')}
            response = requests.post(url, files=files)
        
        if response.status_code == 200:
            result = response.json()
            
            print("=" * 80)
            print("📝 DEAL SUMMARY TEXT")
            print("=" * 80)
            
            print(f"\n📊 SUMMARY:")
            print(f"   Deals Analyzed: {result['deals_analyzed']}")
            print(f"   Selling Fast: {result['selling_fast_count']} ({result['selling_fast_percentage']:.1f}%)")
            
            print(f"\n📄 TEXT SUMMARY (Top 10):")
            print("─" * 80)
            
            for detail in result['prediction_details'][:10]:
                print(detail['text'])
            
            print("\n" + "=" * 80)
            
            # Save to file
            output_file = "deal_summary_text.txt"
            with open(output_file, 'w') as f:
                f.write(result['summary_text'])
            
            print(f"\n✅ Full summary saved to: {output_file}")
            
            return result
        else:
            print(f"❌ Error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def main():
    """Run bulk prediction tests"""
    print("\n" + "🚀 " * 20)
    print("BULK PREDICTION API - TEST SUITE")
    print("🚀 " * 20)
    
    # Get CSV file path
    csv_file = input("\nEnter path to CSV file (or press Enter to use default path): ").strip()
    
    if not csv_file:
        csv_file = "/Users/wallstreet37/Downloads/latest products info.csv"
        print(f"Using default path: {csv_file}")
    
    if not os.path.exists(csv_file):
        print(f"\n❌ Error: File not found: {csv_file}")
        print("\nPlease provide a valid CSV file path.")
        return
    
    print(f"\n✅ File found: {csv_file}")
    
    # Menu
    while True:
        print("\n" + "=" * 80)
        print("SELECT TEST TO RUN:")
        print("=" * 80)
        print("1. Bulk Prediction (Summary)")
        print("2. Download Full Results (CSV)")
        print("3. Deal-Specific Analysis")
        print("4. Text Summary")
        print("5. Run All Tests")
        print("0. Exit")
        
        choice = input("\nEnter your choice (0-5): ").strip()
        
        if choice == "1":
            test_bulk_prediction_from_csv(csv_file)
        elif choice == "2":
            test_download_results(csv_file)
        elif choice == "3":
            test_deal_specific_analysis(csv_file)
        elif choice == "4":
            test_deal_summary_text(csv_file)
        elif choice == "5":
            print("\n🔄 Running all tests...\n")
            test_bulk_prediction_from_csv(csv_file)
            input("\nPress Enter to continue...")
            test_download_results(csv_file)
            input("\nPress Enter to continue...")
            test_deal_specific_analysis(csv_file)
            input("\nPress Enter to continue...")
            test_deal_summary_text(csv_file)
            print("\n✅ All tests completed!")
        elif choice == "0":
            print("\n👋 Goodbye!")
            break
        else:
            print("\n❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    main()

