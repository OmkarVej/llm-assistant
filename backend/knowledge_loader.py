"""
Knowledge Loader - Ingest A2Z domain knowledge into Vector Store
"""
import os
import json
from typing import List, Dict
from rag_service import VectorStore


def load_sample_knowledge() -> List[Dict[str, str]]:
    """Load sample A2Z knowledge documents"""
    
    documents = [
        {
            'text': """
            Rate Markup API V2 - Overview
            The Rate Markup API V2 calculates margin for different dealer tiers (Tier A, Tier B, Tier C).
            It accepts loan parameters including loan amount, term, credit score, and vehicle information.
            The API returns markup rates based on dealer tier and risk assessment.
            
            Endpoint: POST /api/v2/rate-markup
            Request Body:
            {
                "loan_amount": 25000,
                "term_months": 60,
                "credit_score": 720,
                "vehicle_year": 2023,
                "dealer_tier": "B"
            }
            
            Response includes:
            - base_rate: Base interest rate
            - markup_rate: Dealer markup percentage
            - final_rate: Calculated final rate
            - margin_amount: Total margin for the dealer
            """,
            'source': 'API Documentation - Rate Markup V2',
            'type': 'api_documentation'
        },
        {
            'text': """
            Lending Platform Integration - Approved Decision Flow
            When a lending decision is approved, the system generates a payload with the following structure:
            
            {
                "status": "approved",
                "loan_id": "LN-12345",
                "applicant": {
                    "name": "John Doe",
                    "credit_score": 750,
                    "income": 60000
                },
                "loan_terms": {
                    "amount": 30000,
                    "term_months": 72,
                    "interest_rate": 4.5,
                    "monthly_payment": 475.50
                },
                "approval_details": {
                    "approved_by": "system",
                    "approval_date": "2024-01-15",
                    "conditions": []
                }
            }
            
            This payload is sent to the dealer CRM system and stored in the lending platform database.
            """,
            'source': 'Lending Platform - Integration Guide',
            'type': 'api_payload'
        },
        {
            'text': """
            Compliance Rules - F&I Product Regulations
            All F&I (Finance & Insurance) products must comply with state and federal regulations:
            
            1. Truth in Lending Act (TILA): All loan terms must be clearly disclosed
            2. Fair Credit Reporting Act (FCRA): Credit checks require proper authorization
            3. State-specific regulations vary by jurisdiction
            
            Required disclosures:
            - Annual Percentage Rate (APR)
            - Total finance charge
            - Payment schedule
            - Late payment fees
            
            All compliance checks are automated in the lending platform API.
            """,
            'source': 'Compliance Documentation',
            'type': 'compliance'
        },
        {
            'text': """
            Amazon API Integration - Vehicle Pricing Flow
            The Amazon API integration allows dealers to fetch real-time vehicle pricing:
            
            Flow:
            1. Dealer requests vehicle pricing via A2Z API
            2. A2Z API calls Amazon Pricing Service
            3. Amazon returns current market pricing data
            4. A2Z calculates dealer-specific pricing with markup
            5. Response sent back to dealer CRM
            
            Endpoint: GET /api/amazon/pricing/{vin}
            Response includes:
            - market_value: Current market value
            - dealer_cost: Dealer acquisition cost
            - suggested_price: Recommended selling price
            - price_history: Historical pricing data
            """,
            'source': 'Amazon API Integration Guide',
            'type': 'integration'
        },
        {
            'text': """
            DealerTrack Integration - CRM Sync
            A2Z integrates with DealerTrack CRM to sync customer and vehicle data:
            
            Sync Operations:
            - Customer profiles (create, update, read)
            - Vehicle inventory (sync, update pricing)
            - Sales transactions (create deals, update status)
            - Service appointments (schedule, update)
            
            Authentication: OAuth 2.0
            Rate Limits: 1000 requests per hour per dealer
            Webhook Support: Real-time updates via webhooks
            """,
            'source': 'DealerTrack Integration Documentation',
            'type': 'integration'
        },
        {
            'text': """
            RouteOne Integration - Credit Application Processing
            RouteOne integration handles credit applications from multiple lenders:
            
            Process:
            1. Dealer submits credit application via A2Z
            2. A2Z routes to RouteOne platform
            3. RouteOne distributes to multiple lenders
            4. Lenders respond with offers
            5. A2Z aggregates and presents offers to dealer
            
            Supported Lenders: 50+ financial institutions
            Average Response Time: 2-5 minutes
            API Endpoint: POST /api/routeone/submit-application
            """,
            'source': 'RouteOne Integration Guide',
            'type': 'integration'
        },
        {
            'text': """
            Postman Test Case - Vehicle Pricing API
            Example Postman collection for testing vehicle pricing:
            
            Request:
            GET {{base_url}}/api/vehicles/pricing
            Headers:
            - Authorization: Bearer {{api_token}}
            - Content-Type: application/json
            
            Query Parameters:
            - vin: 1HGBH41JXMN109186
            - zip_code: 90210
            
            Expected Response (200 OK):
            {
                "vin": "1HGBH41JXMN109186",
                "make": "Honda",
                "model": "Accord",
                "year": 2021,
                "market_value": 25000,
                "dealer_price": 26500,
                "pricing_date": "2024-01-15"
            }
            """,
            'source': 'API Testing - Postman Collection',
            'type': 'test_case'
        }
    ]
    
    return documents


def initialize_knowledge_base(vector_store: VectorStore, force_reload: bool = False):
    """
    Initialize the knowledge base with A2Z domain knowledge
    
    Args:
        vector_store: VectorStore instance
        force_reload: If True, reload even if index exists
    """
    # Check if knowledge base already exists
    if not force_reload and len(vector_store.metadata) > 0:
        print(f"Knowledge base already initialized with {len(vector_store.metadata)} documents")
        return
    
    # Load sample knowledge
    documents = load_sample_knowledge()
    
    # Add to vector store
    vector_store.add_documents(documents)
    
    # Save to disk
    vector_store.save()
    
    print(f"Initialized knowledge base with {len(documents)} A2Z domain documents")


if __name__ == "__main__":
    # Initialize knowledge base
    vs = VectorStore()
    initialize_knowledge_base(vs, force_reload=True)

