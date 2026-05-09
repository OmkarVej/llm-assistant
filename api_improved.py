from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict, validator
from typing import List, Optional, Dict, Any
import pandas as pd
import numpy as np
import pickle
import io
import warnings
import json
from datetime import datetime
from functools import lru_cache

warnings.filterwarnings('ignore')

# Initialize FastAPI app
app = FastAPI(
    title="Product Performance Prediction API v3.0 - Enhanced",
    description="AI-powered API with improved accuracy to predict which vehicle products are selling fast. Includes single deal prediction.",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
model_artifacts = None
prediction_history = []

# ==================== HELPER FUNCTIONS ====================

def clean_currency(value):
    """Remove currency symbols and convert to float"""
    if pd.isna(value):
        return np.nan
    value_str = str(value).replace('$', '').replace(',', '')
    try:
        return float(value_str)
    except:
        return np.nan

def engineer_features(df):
    """Create advanced derived features (must match training)"""
    # Basic profit metrics
    df['profit_margin'] = df['selling_price'] - df['cost']
    df['profit_margin_pct'] = (df['profit_margin'] / df['cost'] * 100).replace([np.inf, -np.inf], 0)
    
    # Financing metrics
    df['financing_ratio'] = df['pc_amount_financed'] / (df['pc_amount_financed'] + df['pc_down_payment'] + 1)
    df['total_deal_value'] = df['pc_amount_financed'] + df['pc_down_payment']
    df['down_payment_pct'] = (df['pc_down_payment'] / (df['total_deal_value'] + 1) * 100)
    
    # Interest metrics
    df['total_interest'] = (df['pc_amount_financed'] * df['pc_rate'] * df['pc_term']) / (100 * 12)
    df['monthly_payment'] = np.where(
        df['pc_term'] > 0,
        (df['pc_amount_financed'] * (df['pc_rate']/1200) * (1 + df['pc_rate']/1200)**df['pc_term']) / 
        ((1 + df['pc_rate']/1200)**df['pc_term'] - 1),
        0
    )
    df['monthly_payment'] = df['monthly_payment'].replace([np.inf, -np.inf], 0)
    
    # Deal status flags
    df['is_cancelled'] = (df['deal_status'] == 'Cancelled').astype(int)
    df['is_active'] = (df['deal_status'] == 'Active').astype(int)
    
    # Product value metrics
    df['markup_ratio'] = df['selling_price'] / (df['cost'] + 1)
    df['product_value_score'] = df['profit_margin'] * df['financing_ratio']
    
    # Term-based features
    df['is_long_term'] = (df['pc_term'] >= 72).astype(int)
    df['is_medium_term'] = ((df['pc_term'] >= 48) & (df['pc_term'] < 72)).astype(int)
    
    # Rate categories
    df['is_low_rate'] = (df['pc_rate'] < 5).astype(int)
    df['is_high_rate'] = (df['pc_rate'] > 8).astype(int)
    
    # Interaction features
    df['profit_x_financing'] = df['profit_margin_pct'] * df['pc_amount_financed'] / 10000
    df['rate_x_term'] = df['pc_rate'] * df['pc_term'] / 100
    
    return df

def safe_float(value, default=0.0):
    """Safely convert to float"""
    if pd.isna(value):
        return default
    try:
        cleaned = str(value).replace('$', '').replace(',', '')
        return float(cleaned) if cleaned else default
    except:
        return default

def safe_int(value, default=0):
    """Safely convert to int"""
    try:
        return int(safe_float(value, default))
    except:
        return default

def prepare_prediction_data(df):
    """Prepare data for prediction with enhanced preprocessing"""
    if model_artifacts is None:
        raise ValueError("Model not loaded")
    
    label_encoders = model_artifacts['label_encoders']
    feature_columns = model_artifacts['feature_columns']
    categorical_columns = model_artifacts['categorical_columns']
    
    # Clean currency
    df['cost'] = df['cost'].apply(clean_currency)
    df['selling_price'] = df['selling_price'].apply(clean_currency)
    
    # Handle missing numeric values
    df['pc_rate'] = pd.to_numeric(df['pc_rate'], errors='coerce')
    
    # Fill by lender first, then by vehicle type, then median
    if 'pc_lender_code' in df.columns:
        df['pc_rate'] = df.groupby('pc_lender_code')['pc_rate'].transform(
            lambda x: x.fillna(x.median())
        )
    if 'vehicle_type_name' in df.columns:
        df['pc_rate'] = df.groupby('vehicle_type_name')['pc_rate'].transform(
            lambda x: x.fillna(x.median())
        )
    df['pc_rate'] = df['pc_rate'].fillna(df['pc_rate'].median())
    
    if 'vehicle_type_name' in df.columns:
        df['pc_term'] = df.groupby('vehicle_type_name')['pc_term'].transform(
            lambda x: x.fillna(x.median())
        )
    df['pc_term'] = df['pc_term'].fillna(df['pc_term'].median())
    
    df['pc_down_payment'] = df['pc_down_payment'].fillna(0)
    df['pc_amount_financed'] = df['pc_amount_financed'].fillna(df['pc_amount_financed'].median())
    
    # Engineer features
    df = engineer_features(df)
    
    # Store original data
    original_data = df.copy()
    
    # Select features
    df = df[feature_columns].copy()
    
    # Handle missing values
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        df[col] = df[col].fillna(0)
    
    # Encode categorical
    for col in categorical_columns:
        if col in df.columns:
            df[col] = df[col].astype(str)
            le = label_encoders[col]
            df[col] = df[col].apply(
                lambda x: le.transform([x])[0] if x in le.classes_ else le.transform([le.classes_[0]])[0]
            )
    
    return df, original_data

def get_prediction_reasoning(row, confidence, prediction):
    """Generate detailed human-readable explanation"""
    reasons = []
    
    if prediction == 1:  # Selling fast
        if safe_float(row.get('profit_margin_pct', 0)) > 200:
            reasons.append("Excellent profit margin")
        elif safe_float(row.get('profit_margin_pct', 0)) > 100:
            reasons.append("Strong profit margin")
            
        if safe_float(row.get('pc_amount_financed', 0)) > 40000:
            reasons.append("High financing amount")
        elif safe_float(row.get('pc_amount_financed', 0)) > 30000:
            reasons.append("Strong financing amount")
            
        if row.get('product_category_name') in ['Vehicle Service Contract', 'Multi-Coverage Protection', 'GAP']:
            reasons.append("Popular product category")
            
        if safe_int(row.get('pc_term', 0)) >= 72:
            reasons.append("Extended financing term")
            
        if safe_float(row.get('pc_rate', 0)) < 5:
            reasons.append("Competitive interest rate")
            
        if confidence > 0.85:
            reasons.append("High confidence prediction")
    else:
        if safe_float(row.get('profit_margin_pct', 0)) < 50:
            reasons.append("Lower profit margin")
        if row.get('deal_status') == 'Cancelled':
            reasons.append("Deal was cancelled")
        if safe_float(row.get('pc_rate', 0)) > 8:
            reasons.append("Higher interest rate")
        if safe_int(row.get('pc_term', 0)) < 48:
            reasons.append("Shorter financing term")
    
    if not reasons:
        reasons.append(f"Confidence: {confidence:.2%}")
    
    return " | ".join(reasons) if reasons else "Based on model prediction"

# ==================== PYDANTIC MODELS ====================

class SingleDealInput(BaseModel):
    """Input model for single deal prediction"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "dealership_name": "#1 Cochran Hyundai",
            "vehicle_type_name": "New",
            "deal_type_report_type": "Retail",
            "pc_amount_financed": 28293.88,
            "pc_term": 72,
            "pc_rate": 4.5,
            "pc_down_payment": 5000.0,
            "pc_lender_code": "LENDER123",
            "deal_status": "Active",
            "product_category_name": "Vehicle Service Contract",
            "product_name": "Hyundai Vehicle Service Contract",
            "cost": 911.0,
            "selling_price": 3411.0,
            "deal_id": "15",
            "vin": "VIN123456789"
        }
    })
    
    dealership_name: str
    vehicle_type_name: str
    deal_type_report_type: str
    pc_amount_financed: float
    pc_term: int
    pc_rate: float
    pc_down_payment: float = 0.0
    pc_lender_code: Optional[str] = "UNKNOWN"
    deal_status: str = "Active"
    product_category_name: str
    product_name: str
    cost: float
    selling_price: float
    deal_id: Optional[str] = None
    vin: Optional[str] = None

class SingleDealPrediction(BaseModel):
    """Output model for single deal prediction"""
    deal_id: Optional[str]
    dealership_name: str
    vehicle_type: str
    product_category: str
    product_name: str
    
    # Financial metrics
    cost: float
    selling_price: float
    profit_margin: float
    profit_margin_pct: float
    
    # Financing details
    pc_amount_financed: float
    pc_term: int
    pc_rate: float
    pc_down_payment: float
    monthly_payment: float
    total_interest: float
    
    # Prediction results
    prediction: str
    will_sell_fast: bool
    confidence: float
    confidence_percentage: str
    
    # Insights
    reasoning: str
    key_factors: List[str]
    risk_level: str
    recommendation: str

class ProductPrediction(BaseModel):
    deal_id: str
    dealership_name: str
    vehicle_type: str
    product_category: str
    product_name: str
    cost: float
    selling_price: float
    profit_margin: float
    pc_amount_financed: float
    pc_term: float
    pc_rate: float
    prediction: str
    confidence: float
    selling_fast: bool
    reasoning: str

class BulkPredictionResponse(BaseModel):
    total_predictions: int
    selling_fast_count: int
    not_selling_fast_count: int
    percentage_selling_fast: float
    average_confidence: float
    timestamp: str
    top_predictions: List[ProductPrediction]
    summary_by_category: Dict[str, Dict[str, Any]]
    summary_by_dealership: Dict[str, Dict[str, Any]]

class ModelInfo(BaseModel):
    model_loaded: bool
    accuracy: float
    roc_auc_score: float
    f1_score: float
    cv_mean_score: float
    feature_count: int
    training_date: str
    model_version: str

class HealthResponse(BaseModel):
    message: str
    status: str
    model_loaded: bool
    version: str
    endpoints: Dict[str, str]

class DealSpecificAnalysis(BaseModel):
    deal_id: str
    dealership_name: str
    vehicle_type: str
    vehicle_name: Optional[str]
    product_category: str
    product_name: str
    deal_analysis: Dict[str, float]
    prediction: Dict[str, Any]
    why_selling_fast: List[str]
    optimization: Dict[str, str]

class DealSummaryText(BaseModel):
    summary_text: str
    deals_analyzed: int
    selling_fast_count: int
    selling_fast_percentage: float
    prediction_details: List[Dict[str, Any]]

# ==================== LOAD MODEL ====================

@app.on_event("startup")
async def load_model():
    """Load trained model on API startup"""
    global model_artifacts
    try:
        with open('improved_model.pkl', 'rb') as f:
            model_artifacts = pickle.load(f)
        print("✅ Enhanced Model loaded successfully!")
        print(f"   - Accuracy: {model_artifacts['accuracy']:.4f}")
        print(f"   - ROC-AUC: {model_artifacts['roc_auc']:.4f}")
        print(f"   - F1-Score: {model_artifacts.get('f1_score', 'N/A')}")
        print(f"   - Features: {len(model_artifacts['feature_columns'])}")
    except Exception as e:
        print(f"⚠️ Warning: Could not load model: {e}")
        print("Please run train_model_improved.py first")

# ==================== API ENDPOINTS ====================

@app.get("/", response_model=HealthResponse, tags=["Health Check"])
async def root():
    """API health check and information"""
    return HealthResponse(
        message="Product Performance Prediction API v3.0 - Enhanced",
        status="running",
        model_loaded=model_artifacts is not None,
        version="3.0.0",
        endpoints={
            "docs": "/docs",
            "redoc": "/redoc",
            "predict": "/predict",
            "predict_single": "/predict/single",
            "model_info": "/model/info",
            "download_results": "/predict/download",
            "deal_specific": "/analyze/deal-specific",
            "deal_summary_text": "/analyze/deal-summary-text"
        }
    )

@app.get("/model/info", response_model=ModelInfo, tags=["Model"])
async def get_model_info():
    """Get detailed model information"""
    if model_artifacts is None:
        raise HTTPException(status_code=503, detail="Model not loaded. Run train_model_improved.py first.")
    
    cv_scores = model_artifacts.get('cv_scores', [])
    cv_mean = float(np.mean(cv_scores)) if len(cv_scores) > 0 else 0.0
    
    return ModelInfo(
        model_loaded=True,
        accuracy=round(model_artifacts['accuracy'], 4),
        roc_auc_score=round(model_artifacts['roc_auc'], 4),
        f1_score=round(model_artifacts.get('f1_score', 0), 4),
        cv_mean_score=round(cv_mean, 4),
        feature_count=len(model_artifacts['feature_columns']),
        training_date=model_artifacts.get('training_date', 'Unknown'),
        model_version="3.0.0"
    )

@app.post("/predict/single", response_model=SingleDealPrediction, tags=["Predictions"])
async def predict_single_deal(deal: SingleDealInput):
    """
    🎯 Predict if a SINGLE deal will sell fast
    
    **Perfect for real-time predictions:**
    - Submit one deal at a time
    - Get instant prediction with confidence score
    - Detailed financial analysis
    - Actionable recommendations
    
    **Example Use Cases:**
    - While negotiating a deal
    - When pricing a product
    - Before presenting to customer
    - Quick what-if scenarios
    """
    if model_artifacts is None:
        raise HTTPException(status_code=503, detail="Model not loaded. Run train_model_improved.py first.")
    
    try:
        # Convert single deal to DataFrame
        deal_dict = deal.dict()
        df = pd.DataFrame([deal_dict])
        
        # Prepare data
        X, original_data = prepare_prediction_data(df)
        
        # Make prediction
        model = model_artifacts['model']
        prediction = model.predict(X)[0]
        probability = model.predict_proba(X)[0]
        
        confidence = float(probability[1])
        is_selling_fast = bool(prediction == 1)
        
        row = original_data.iloc[0]
        
        # Generate key factors
        key_factors = []
        profit_margin_pct = safe_float(row.get('profit_margin_pct', 0))
        
        if is_selling_fast:
            if profit_margin_pct > 200:
                key_factors.append(f"✅ Excellent profit margin ({profit_margin_pct:.1f}%)")
            elif profit_margin_pct > 100:
                key_factors.append(f"✅ Strong profit margin ({profit_margin_pct:.1f}%)")
            
            if safe_float(row.get('pc_amount_financed', 0)) > 35000:
                key_factors.append(f"✅ High financing amount (${safe_float(row.get('pc_amount_financed', 0)):,.0f})")
            
            if deal.product_category_name in ['Vehicle Service Contract', 'Multi-Coverage Protection', 'GAP']:
                key_factors.append(f"✅ Popular product: {deal.product_category_name}")
            
            if deal.pc_term >= 72:
                key_factors.append(f"✅ Extended term ({deal.pc_term} months)")
            
            if deal.pc_rate < 5:
                key_factors.append(f"✅ Competitive rate ({deal.pc_rate}%)")
        else:
            if profit_margin_pct < 50:
                key_factors.append(f"⚠️ Lower profit margin ({profit_margin_pct:.1f}%)")
            if deal.deal_status == 'Cancelled':
                key_factors.append("⚠️ Deal cancelled")
            if deal.pc_rate > 8:
                key_factors.append(f"⚠️ Higher rate ({deal.pc_rate}%)")
            if deal.pc_term < 48:
                key_factors.append(f"⚠️ Shorter term ({deal.pc_term} months)")
        
        if not key_factors:
            key_factors.append("📊 Mixed indicators")
        
        # Risk level
        if confidence > 0.85:
            risk_level = "Low Risk" if is_selling_fast else "High Risk"
        elif confidence > 0.65:
            risk_level = "Medium Risk"
        else:
            risk_level = "High Uncertainty"
        
        # Recommendation
        if is_selling_fast and confidence > 0.85:
            recommendation = "✅ RECOMMENDED: This deal has strong selling potential. Proceed with confidence."
        elif is_selling_fast and confidence > 0.65:
            recommendation = "✓ GOOD: This deal shows promise. Consider minor optimizations."
        elif not is_selling_fast and confidence > 0.75:
            recommendation = "⚠️ NOT RECOMMENDED: This deal is unlikely to sell fast. Consider restructuring."
        else:
            recommendation = "⚡ UNCERTAIN: Mixed signals. Review key factors and optimize pricing/terms."
        
        result = SingleDealPrediction(
            deal_id=deal.deal_id,
            dealership_name=deal.dealership_name,
            vehicle_type=deal.vehicle_type_name,
            product_category=deal.product_category_name,
            product_name=deal.product_name,
            cost=round(deal.cost, 2),
            selling_price=round(deal.selling_price, 2),
            profit_margin=round(safe_float(row.get('profit_margin', 0)), 2),
            profit_margin_pct=round(profit_margin_pct, 2),
            pc_amount_financed=round(deal.pc_amount_financed, 2),
            pc_term=deal.pc_term,
            pc_rate=round(deal.pc_rate, 2),
            pc_down_payment=round(deal.pc_down_payment, 2),
            monthly_payment=round(safe_float(row.get('monthly_payment', 0)), 2),
            total_interest=round(safe_float(row.get('total_interest', 0)), 2),
            prediction="SELLING FAST ⭐" if is_selling_fast else "NOT LIKELY TO SELL FAST",
            will_sell_fast=is_selling_fast,
            confidence=round(confidence, 4),
            confidence_percentage=f"{confidence*100:.1f}%",
            reasoning=get_prediction_reasoning(row, confidence, prediction),
            key_factors=key_factors,
            risk_level=risk_level,
            recommendation=recommendation
        )
        
        return result
        
    except Exception as e:
        import traceback
        print(f"Error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=400, detail=f"Prediction error: {str(e)}")

@app.post("/predict", response_model=BulkPredictionResponse, tags=["Predictions"])
async def predict_batch(
    file: UploadFile = File(..., description="CSV file with product/deal data for prediction")
):
    """
    🎯 Predict which products are selling fast (BULK)
    
    **Upload CSV file and get predictions:**
    - Analyzes product and deal characteristics
    - Returns products sorted by selling probability
    - Provides confidence scores and reasoning
    """
    if model_artifacts is None:
        raise HTTPException(status_code=503, detail="Model not loaded. Run train_model_improved.py first.")
    
    try:
        # Read file
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))
        print(f"Prediction batch: {len(df)} records")
        
        # Prepare data
        X, original_data = prepare_prediction_data(df)
        
        # Make predictions
        model = model_artifacts['model']
        predictions = model.predict(X)
        probabilities = model.predict_proba(X)
        
        # Create results
        results = []
        selling_fast_count = 0
        total_confidence = 0
        
        for idx, (pred, prob) in enumerate(zip(predictions, probabilities)):
            row = original_data.iloc[idx]
            confidence = float(prob[1])
            is_selling_fast = bool(pred == 1)
            
            if is_selling_fast:
                selling_fast_count += 1
            total_confidence += confidence
            
            profit_margin = safe_float(row.get('profit_margin', 0))
            
            result = ProductPrediction(
                deal_id=str(row.get('deal_id', 'N/A')),
                dealership_name=str(row.get('dealership_name', 'N/A')),
                vehicle_type=str(row.get('vehicle_type_name', 'N/A')),
                product_category=str(row.get('product_category_name', 'N/A')),
                product_name=str(row.get('product_name', 'N/A')),
                cost=round(safe_float(row.get('cost')), 2),
                selling_price=round(safe_float(row.get('selling_price')), 2),
                profit_margin=round(profit_margin, 2),
                pc_amount_financed=round(safe_float(row.get('pc_amount_financed')), 2),
                pc_term=safe_int(row.get('pc_term')),
                pc_rate=round(safe_float(row.get('pc_rate')), 2),
                prediction="SELLING FAST ⭐" if is_selling_fast else "Not Likely to Sell Fast",
                confidence=round(confidence, 4),
                selling_fast=is_selling_fast,
                reasoning=get_prediction_reasoning(row, confidence, pred)
            )
            results.append(result)
        
        # Sort by confidence
        results.sort(key=lambda x: x.confidence, reverse=True)
        
        # Top 50 results
        top_results = results[:50]
        
        # Summary by category
        category_summary = {}
        for pred in results:
            cat = pred.product_category
            if cat not in category_summary:
                category_summary[cat] = {'total': 0, 'selling_fast': 0, 'avg_confidence': 0}
            category_summary[cat]['total'] += 1
            if pred.selling_fast:
                category_summary[cat]['selling_fast'] += 1
            category_summary[cat]['avg_confidence'] += pred.confidence
        
        for cat in category_summary:
            count = category_summary[cat]['total']
            category_summary[cat]['avg_confidence'] = round(category_summary[cat]['avg_confidence'] / count, 4)
            category_summary[cat]['percentage'] = round(category_summary[cat]['selling_fast'] / count * 100, 2)
        
        # Summary by dealership (top 10)
        dealership_summary = {}
        for pred in results:
            deal = pred.dealership_name
            if deal not in dealership_summary:
                dealership_summary[deal] = {'total': 0, 'selling_fast': 0, 'avg_confidence': 0}
            dealership_summary[deal]['total'] += 1
            if pred.selling_fast:
                dealership_summary[deal]['selling_fast'] += 1
            dealership_summary[deal]['avg_confidence'] += pred.confidence
        
        for deal in dealership_summary:
            count = dealership_summary[deal]['total']
            dealership_summary[deal]['avg_confidence'] = round(dealership_summary[deal]['avg_confidence'] / count, 4)
            dealership_summary[deal]['percentage'] = round(dealership_summary[deal]['selling_fast'] / count * 100, 2)
        
        dealership_summary = dict(sorted(dealership_summary.items(),
                                        key=lambda x: x[1]['selling_fast'], reverse=True)[:10])
        
        response = BulkPredictionResponse(
            total_predictions=len(results),
            selling_fast_count=selling_fast_count,
            not_selling_fast_count=len(results) - selling_fast_count,
            percentage_selling_fast=round(selling_fast_count / len(results) * 100, 2) if len(results) > 0 else 0,
            average_confidence=round(total_confidence / len(results), 4) if len(results) > 0 else 0,
            timestamp=datetime.now().isoformat(),
            top_predictions=top_results,
            summary_by_category=category_summary,
            summary_by_dealership=dealership_summary
        )
        
        return response
        
    except Exception as e:
        import traceback
        print(f"Error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/predict/download", tags=["Predictions"])
async def predict_and_download(
    file: UploadFile = File(..., description="CSV file with product/deal data")
):
    """
    📥 Download complete prediction results as CSV
    Includes all predictions with detailed confidence scores
    """
    if model_artifacts is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Read file
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))
        
        # Prepare and predict
        X, original_data = prepare_prediction_data(df)
        model = model_artifacts['model']
        predictions = model.predict(X)
        probabilities = model.predict_proba(X)
        
        # Add predictions to original data
        results_df = original_data.copy()
        results_df['prediction'] = predictions
        results_df['probability_not_selling_fast'] = probabilities[:, 0]
        results_df['probability_selling_fast'] = probabilities[:, 1]
        results_df['confidence'] = np.max(probabilities, axis=1)
        results_df['prediction_label'] = results_df['prediction'].map({
            0: 'Not Likely to Sell Fast',
            1: 'SELLING FAST'
        })
        
        # Sort by confidence
        results_df = results_df.sort_values('probability_selling_fast', ascending=False)
        
        # Save
        output_file = 'prediction_results.csv'
        results_df.to_csv(output_file, index=False)
        
        return FileResponse(
            output_file,
            media_type='text/csv',
            filename='prediction_results.csv'
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/analyze/deal-specific", tags=["Deal-Specific Analysis"])
async def analyze_deal_specific(
    file: UploadFile = File(..., description="CSV file with product/deal data")
):
    """
    🎯 Deal-Specific Analysis
    
    For each deal shows:
    DEAL_ID → VEHICLE → WITH THESE PROPERTIES → AT THIS RATE AND TERM → SELLING FAST?
    """
    if model_artifacts is None:
        raise HTTPException(status_code=503, detail="Model not loaded. Run train_model_improved.py first.")
    
    try:
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))
        
        X, original_data = prepare_prediction_data(df)
        model = model_artifacts['model']
        predictions = model.predict(X)
        probabilities = model.predict_proba(X)
        
        results = []
        
        for idx, (pred, prob) in enumerate(zip(predictions, probabilities)):
            row = original_data.iloc[idx]
            confidence = float(prob[1])
            is_selling_fast = bool(pred == 1)
            
            # Generate why_selling_fast list
            why_list = []
            if is_selling_fast:
                profit_margin_pct = safe_float(row.get('profit_margin_pct', 0))
                if profit_margin_pct > 200:
                    why_list.append(f"✅ Excellent profit margin ({profit_margin_pct:.1f}%)")
                if row.get('product_category_name') in ['Vehicle Service Contract', 'GAP']:
                    why_list.append(f"✅ Popular product: {row.get('product_category_name')}")
                if safe_float(row.get('pc_amount_financed', 0)) > 30000:
                    why_list.append(f"✅ Strong financing amount (${safe_float(row.get('pc_amount_financed', 0)):.0f})")
                if safe_int(row.get('pc_term', 0)) >= 72:
                    why_list.append(f"✅ Extended financing term ({safe_int(row.get('pc_term', 0))} months)")
                if confidence > 0.85:
                    why_list.append(f"✅ High confidence prediction ({confidence:.0%})")
            else:
                profit_margin_pct = safe_float(row.get('profit_margin_pct', 0))
                if profit_margin_pct < 50:
                    why_list.append(f"⚠️ Lower profit margin ({profit_margin_pct:.1f}%)")
                if safe_float(row.get('pc_rate', 0)) > 8:
                    why_list.append(f"⚠️ Higher interest rate ({safe_float(row.get('pc_rate', 0)):.2f}%)")
                if safe_int(row.get('pc_term', 0)) < 60:
                    why_list.append(f"⚠️ Shorter financing term ({safe_int(row.get('pc_term', 0))} months)")
            
            if not why_list:
                why_list.append("📊 Mixed indicators - review details")
            
            # Generate optimization
            optimization = {
                "price_recommendation": "Current price is competitive" if confidence > 0.75 else "Consider price adjustment",
                "rate_recommendation": "Rate is competitive" if safe_float(row.get('pc_rate', 0)) < 7 else "Negotiate lower rate",
                "term_recommendation": "Extended term appeals to buyers" if safe_int(row.get('pc_term', 0)) >= 72 else "Try 72-month term"
            }
            
            # Create prediction text
            prediction_text = (
                f"For dealid {row.get('deal_id')} → {row.get('vehicle_type_name', '')} {row.get('vehicle_name', 'Vehicle')} "
                f"→ with profit margin {safe_float(row.get('profit_margin_pct', 0)):.1f}%, "
                f"financing ${safe_float(row.get('pc_amount_financed', 0)):.0f}, "
                f"at rate {safe_float(row.get('pc_rate', 0)):.2f}% for {safe_int(row.get('pc_term', 0))} months "
                f"→ {'WILL SELL FAST ⭐' if is_selling_fast else '❌ NOT SELLING FAST'} ({confidence:.0%} confidence)"
            )
            
            result = DealSpecificAnalysis(
                deal_id=str(row.get('deal_id', 'N/A')),
                dealership_name=str(row.get('dealership_name', 'N/A')),
                vehicle_type=str(row.get('vehicle_type_name', 'N/A')),
                vehicle_name=str(row.get('vehicle_name', 'N/A')) if 'vehicle_name' in row else None,
                product_category=str(row.get('product_category_name', 'N/A')),
                product_name=str(row.get('product_name', 'N/A')),
                deal_analysis={
                    "cost": round(safe_float(row.get('cost')), 2),
                    "selling_price": round(safe_float(row.get('selling_price')), 2),
                    "profit_margin": round(safe_float(row.get('profit_margin', 0)), 2),
                    "profit_margin_pct": round(safe_float(row.get('profit_margin_pct', 0)), 2),
                    "pc_amount_financed": round(safe_float(row.get('pc_amount_financed')), 2),
                    "pc_rate": round(safe_float(row.get('pc_rate')), 2),
                    "pc_term": safe_int(row.get('pc_term')),
                    "pc_down_payment": round(safe_float(row.get('pc_down_payment')), 2)
                },
                prediction={
                    "will_sell_fast": is_selling_fast,
                    "confidence": round(confidence, 4),
                    "text": prediction_text
                },
                why_selling_fast=why_list,
                optimization=optimization
            )
            
            results.append(result)
        
        # Sort by confidence
        results.sort(key=lambda x: x.prediction['confidence'], reverse=True)
        
        # Top 50 results
        top_results = results[:50]
        
        response = {
            "total_deals_analyzed": len(results),
            "selling_fast_count": len([r for r in results if r.prediction['will_sell_fast']]),
            "not_selling_count": len([r for r in results if not r.prediction['will_sell_fast']]),
            "deals": [r.dict() if hasattr(r, 'dict') else r.model_dump() for r in top_results]
        }
        
        return JSONResponse(content=response, status_code=200)
        
    except Exception as e:
        import traceback
        print(f"Error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/analyze/deal-summary-text", response_model=DealSummaryText, tags=["Deal-Specific Analysis"])
async def analyze_deal_summary_text(
    file: UploadFile = File(..., description="CSV file with product/deal data")
):
    """
    📝 Deal Summary in Plain Text Format
    
    Shows each deal as readable text for reports and dashboards
    """
    if model_artifacts is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))
        
        X, original_data = prepare_prediction_data(df)
        model = model_artifacts['model']
        predictions = model.predict(X)
        probabilities = model.predict_proba(X)
        
        summary_text = ""
        all_details = []
        selling_fast_count = 0
        
        for idx, (pred, prob) in enumerate(zip(predictions, probabilities)):
            row = original_data.iloc[idx]
            confidence = float(prob[1])
            is_selling_fast = bool(pred == 1)
            
            if is_selling_fast:
                selling_fast_count += 1
            
            # Create readable text
            text = (
                f"DealID {row.get('deal_id')} → {row.get('vehicle_type_name')} {row.get('vehicle_name', 'Vehicle')} "
                f"({row.get('dealership_name')}) → "
                f"Product: {row.get('product_name')} → "
                f"Profit: {safe_float(row.get('profit_margin_pct', 0)):.1f}%, "
                f"Financing: ${safe_float(row.get('pc_amount_financed', 0)):.0f}, "
                f"Rate: {safe_float(row.get('pc_rate', 0)):.2f}%, "
                f"Term: {safe_int(row.get('pc_term', 0))} months "
                f"→ {'✅ SELLING FAST' if is_selling_fast else '❌ NOT SELLING'} ({confidence:.0%})"
            )
            
            summary_text += text + "\n"
            
            all_details.append({
                "deal_id": str(row.get('deal_id')),
                "text": text,
                "will_sell_fast": is_selling_fast,
                "confidence": round(confidence, 4)
            })
        
        # Sort by confidence
        all_details.sort(key=lambda x: x['confidence'], reverse=True)
        
        response = DealSummaryText(
            summary_text=summary_text,
            deals_analyzed=len(all_details),
            selling_fast_count=selling_fast_count,
            selling_fast_percentage=round(selling_fast_count / len(all_details) * 100, 2) if len(all_details) > 0 else 0,
            prediction_details=all_details[:50]
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Enhanced Product Performance Prediction API v3.0...")
    print("📚 Swagger UI: http://localhost:8000/docs")
    print("📖 ReDoc: http://localhost:8000/redoc")
    print("\n✨ NEW FEATURES:")
    print("  - ✅ Improved model accuracy with advanced feature engineering")
    print("  - ✅ Single deal prediction endpoint: /predict/single")
    print("  - ✅ Enhanced confidence scoring")
    print("  - ✅ Detailed risk analysis and recommendations")
    print("  - ✅ Cross-validation metrics")
    uvicorn.run(app, host="0.0.0.0", port=8000)

