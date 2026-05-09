import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix, roc_auc_score, f1_score
import pickle
import warnings
from datetime import datetime

warnings.filterwarnings('ignore')

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
    """Create advanced derived features for better predictions"""
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

def preprocess_data(csv_file):
    """Load and preprocess data with advanced cleaning"""
    print("=" * 70)
    print("LOADING AND ANALYZING DATA")
    print("=" * 70)
    
    df = pd.read_csv(csv_file)
    print(f"\nTotal Records: {len(df)}")
    print(f"\nTarget Distribution:")
    print(df['chosen'].value_counts())
    print(f"\nPercentage:")
    print((df['chosen'].value_counts(normalize=True) * 100).round(2))
    
    # Clean currency columns
    print("\n" + "=" * 70)
    print("DATA CLEANING AND PREPROCESSING")
    print("=" * 70)
    
    df['cost'] = df['cost'].apply(clean_currency)
    df['selling_price'] = df['selling_price'].apply(clean_currency)
    
    # Handle missing numeric values with more sophisticated methods
    print("Handling missing pc_rate values...")
    df['pc_rate'] = pd.to_numeric(df['pc_rate'], errors='coerce')
    
    # Fill by lender first, then by vehicle type, then median
    df['pc_rate'] = df.groupby('pc_lender_code')['pc_rate'].transform(
        lambda x: x.fillna(x.median())
    )
    df['pc_rate'] = df.groupby('vehicle_type_name')['pc_rate'].transform(
        lambda x: x.fillna(x.median())
    )
    df['pc_rate'] = df['pc_rate'].fillna(df['pc_rate'].median())
    
    print("Handling missing pc_term values...")
    df['pc_term'] = df.groupby('vehicle_type_name')['pc_term'].transform(
        lambda x: x.fillna(x.median())
    )
    df['pc_term'] = df['pc_term'].fillna(df['pc_term'].median())
    
    print("Handling missing pc_down_payment values...")
    df['pc_down_payment'] = df['pc_down_payment'].fillna(0)
    
    print("Handling missing pc_amount_financed values...")
    df['pc_amount_financed'] = df['pc_amount_financed'].fillna(df['pc_amount_financed'].median())
    
    # Engineer features
    print("\nEngineering advanced derived features...")
    df = engineer_features(df)
    
    print(f"Missing values after cleaning: {df.isnull().sum().sum()}")
    
    return df

def train_model(csv_file='/Users/wallstreet37/Downloads/latest products info.csv'):
    """Train an improved prediction model with cross-validation"""
    
    # Preprocess data
    df = preprocess_data(csv_file)
    
    # Feature selection - expanded feature set
    print("\n" + "=" * 70)
    print("FEATURE SELECTION")
    print("=" * 70)
    
    feature_columns = [
        'dealership_name',
        'vehicle_type_name',
        'deal_type_report_type',
        'pc_amount_financed',
        'pc_term',
        'pc_rate',
        'pc_down_payment',
        'deal_status',
        'product_category_name',
        'product_name',
        'cost',
        'selling_price',
        'profit_margin',
        'profit_margin_pct',
        'financing_ratio',
        'is_cancelled',
        'total_deal_value',
        'down_payment_pct',
        'total_interest',
        'monthly_payment',
        'is_active',
        'markup_ratio',
        'product_value_score',
        'is_long_term',
        'is_medium_term',
        'is_low_rate',
        'is_high_rate',
        'profit_x_financing',
        'rate_x_term'
    ]
    
    X = df[feature_columns].copy()
    y = df['chosen'].copy()
    
    # Fill remaining missing values
    X = X.fillna(0)
    
    print(f"Features selected: {len(feature_columns)}")
    print(f"Feature matrix shape: {X.shape}")
    
    # Encode categorical variables
    print("\n" + "=" * 70)
    print("ENCODING CATEGORICAL VARIABLES")
    print("=" * 70)
    
    label_encoders = {}
    categorical_columns = [
        'dealership_name', 'vehicle_type_name', 'deal_type_report_type',
        'deal_status', 'product_category_name', 'product_name'
    ]
    
    for col in categorical_columns:
        le = LabelEncoder()
        X[col] = le.fit_transform(X[col].astype(str))
        label_encoders[col] = le
        print(f"Encoded '{col}': {len(le.classes_)} unique values")
    
    # Train-test split
    print("\n" + "=" * 70)
    print("TRAIN-TEST SPLIT")
    print("=" * 70)
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"Training set size: {len(X_train)}")
    print(f"Testing set size: {len(X_test)}")
    
    # Cross-validation
    print("\n" + "=" * 70)
    print("CROSS-VALIDATION (5-Fold)")
    print("=" * 70)
    
    cv_model = GradientBoostingClassifier(
        n_estimators=300,
        learning_rate=0.05,
        max_depth=7,
        min_samples_split=15,
        min_samples_leaf=5,
        subsample=0.8,
        random_state=42,
        verbose=0
    )
    
    cv_scores = cross_val_score(cv_model, X_train, y_train, cv=5, scoring='roc_auc')
    print(f"Cross-Validation ROC-AUC Scores: {cv_scores}")
    print(f"Mean CV ROC-AUC: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
    
    # Train final model with optimized hyperparameters
    print("\n" + "=" * 70)
    print("MODEL TRAINING - OPTIMIZED GRADIENT BOOSTING")
    print("=" * 70)
    
    model = GradientBoostingClassifier(
        n_estimators=400,  # Increased for better learning
        learning_rate=0.04,  # Slightly lower for better generalization
        max_depth=8,  # Deeper trees for more complex patterns
        min_samples_split=12,
        min_samples_leaf=4,
        subsample=0.85,
        max_features='sqrt',  # Feature sampling for diversity
        random_state=42,
        verbose=0
    )
    
    model.fit(X_train, y_train)
    
    # Evaluation
    print("\n" + "=" * 70)
    print("MODEL EVALUATION")
    print("=" * 70)
    
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)
    
    accuracy = accuracy_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_pred_proba[:, 1])
    f1 = f1_score(y_test, y_pred)
    
    print(f"Accuracy: {accuracy:.4f}")
    print(f"ROC-AUC Score: {roc_auc:.4f}")
    print(f"F1 Score: {f1:.4f}")
    print(f"\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['Not Selling Fast', 'Selling Fast']))
    print(f"\nConfusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(cm)
    print(f"\nTrue Negatives: {cm[0][0]}, False Positives: {cm[0][1]}")
    print(f"False Negatives: {cm[1][0]}, True Positives: {cm[1][1]}")
    
    # Feature importance
    print("\n" + "=" * 70)
    print("FEATURE IMPORTANCE - TOP 20")
    print("=" * 70)
    
    feature_importance = pd.DataFrame({
        'feature': feature_columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print(feature_importance.head(20).to_string())
    
    # Save artifacts
    print("\n" + "=" * 70)
    print("SAVING MODEL ARTIFACTS")
    print("=" * 70)
    
    model_artifacts = {
        'model': model,
        'label_encoders': label_encoders,
        'feature_columns': feature_columns,
        'categorical_columns': categorical_columns,
        'feature_importance': feature_importance,
        'accuracy': accuracy,
        'roc_auc': roc_auc,
        'f1_score': f1,
        'cv_scores': cv_scores,
        'training_date': datetime.now().isoformat(),
        'confusion_matrix': cm.tolist()
    }
    
    with open('improved_model.pkl', 'wb') as f:
        pickle.dump(model_artifacts, f)
    
    print("✅ Model saved as 'improved_model.pkl'")
    print(f"\n📊 Model Performance Summary:")
    print(f"   - Accuracy: {accuracy:.4f}")
    print(f"   - ROC-AUC: {roc_auc:.4f}")
    print(f"   - F1-Score: {f1:.4f}")
    print(f"   - CV Mean ROC-AUC: {cv_scores.mean():.4f}")
    print("\n🎉 Training completed successfully!")
    
    return model_artifacts

if __name__ == "__main__":
    train_model('/Users/wallstreet37/Downloads/latest products info.csv')

