import warnings
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.impute import SimpleImputer
import re
from datetime import datetime

class DataCleaner:
    def __init__(self, filepath):
        self.filepath = filepath
        self.df = None
        self.cleaning_report = {}
    
    def load_data(self):
        """Load data from CSV or Excel file"""
        if self.filepath.endswith('.csv'):
            self.df = pd.read_csv(self.filepath, encoding_errors='ignore')
        elif self.filepath.endswith(('.xls', '.xlsx')):
            self.df = pd.read_excel(self.filepath)
        else:
            raise ValueError("Unsupported file format. Please upload CSV or Excel file.")
        
        # Convert column names to snake_case
        self.df.columns = [self._to_snake_case(col) for col in self.df.columns]
    
    def _to_snake_case(self, name):
        """Convert string to snake_case"""
        name = str(name).strip()
        name = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
        name = re.sub(r'[^\w_]', '', name)
        name = re.sub(r'_+', '_', name)
        return name
    
    def clean_data(self):
        """Perform all data cleaning steps"""
        self.load_data()
        
        # Initialize cleaning report
        self.cleaning_report = {
            'original_rows': len(self.df),
            'original_cols': len(self.df.columns),
            'missing_values': int(self.df.isnull().sum().sum()),
            'duplicates_removed': 0,
            'outliers_treated': 0,
            'columns_removed': 0
        }

        # Perform cleaning steps
        self.remove_empty_columns()
        self.handle_missing_values()
        self.remove_duplicates()
        self.handle_outliers()
        self.standardize_formats()
        self.convert_date_columns()
        self.normalize_numeric_features()
        
        # Update final stats
        self.cleaning_report['cleaned_rows'] = len(self.df)
        self.cleaning_report['cleaned_cols'] = len(self.df.columns)
        
        return self.df, self.cleaning_report
    
    def remove_empty_columns(self):
        """Remove columns with more than 90% missing values"""
        threshold = len(self.df) * 0.9
        initial_cols = len(self.df.columns)
        self.df = self.df.dropna(axis=1, thresh=threshold)
        self.cleaning_report['columns_removed'] = initial_cols - len(self.df.columns)
    
    def handle_missing_values(self):
        """Impute missing values"""
        numeric_cols = self.df.select_dtypes(include=np.number).columns
        categorical_cols = self.df.select_dtypes(exclude=np.number).columns
        
        # Fill numeric columns with median
        if not numeric_cols.empty:
            imputer = SimpleImputer(strategy='median')
            self.df[numeric_cols] = imputer.fit_transform(self.df[numeric_cols])
        
        # Fill categorical columns with mode
        for col in categorical_cols:
            if self.df[col].isnull().any():
                self.df[col] = self.df[col].fillna(self.df[col].mode()[0])
    
    def remove_duplicates(self):
        """Drop duplicate rows"""
        initial_count = len(self.df)
        self.df = self.df.drop_duplicates()
        self.cleaning_report['duplicates_removed'] = initial_count - len(self.df)
    
    def handle_outliers(self):
        """Cap outliers using IQR method for numeric columns"""
        numeric_cols = self.df.select_dtypes(include=np.number).columns
        for col in numeric_cols:
            Q1 = self.df[col].quantile(0.25)
            Q3 = self.df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            # Count outliers
            outliers = ((self.df[col] < lower_bound) | (self.df[col] > upper_bound)).sum()
            self.cleaning_report['outliers_treated'] += outliers
            
            # Cap the outliers
            self.df[col] = self.df[col].clip(lower_bound, upper_bound)
    
    def standardize_formats(self):
        """Clean and standardize text data"""
        text_cols = self.df.select_dtypes(include=['object']).columns
        for col in text_cols:
            self.df[col] = self.df[col].astype(str).str.strip().str.lower()
            self.df[col] = self.df[col].replace({'nan': np.nan, 'none': np.nan, 'null': np.nan})
    
    def convert_date_columns(self):
        """Attempt to convert potential date columns to datetime"""
        for col in self.df.columns:
            try:
                self.df[col] = pd.to_datetime(self.df[col], errors='ignore')
                if pd.api.types.is_datetime64_any_dtype(self.df[col]):
                    # Convert datetime to consistent format
                    self.df[col] = self.df[col].dt.strftime('%Y-%m-%d')
            except:
                continue
    
    def normalize_numeric_features(self):
        """Apply Min-Max scaling to numeric features"""
        numeric_cols = self.df.select_dtypes(include=np.number).columns
        if not numeric_cols.empty:
            scaler = MinMaxScaler()
            self.df[numeric_cols] = scaler.fit_transform(self.df[numeric_cols])