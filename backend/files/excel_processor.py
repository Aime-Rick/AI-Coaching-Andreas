"""
Excel file processing utilities for handling .xls, .xlsx, and .csv files
"""
import pandas as pd
import io
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class ExcelProcessor:
    @staticmethod
    def process_excel_file(file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Process Excel/CSV files and extract data
        
        Args:
            file_content: Raw file content
            filename: Name of the file
            
        Returns:
            Processed data structure with columns, rows, and metadata
        """
        try:
            file_stream = io.BytesIO(file_content)

            # Use low-memory and dtype inference disabled where possible to speed up parsing
            read_csv_opts = {
                'encoding': 'utf-8',
                'low_memory': True,
            }

            # Handle different file types with faster reads where possible
            if filename.lower().endswith('.csv'):
                # Try different encodings for CSV files, but avoid multiple full parses if large
                try:
                    file_stream.seek(0)
                    df = pd.read_csv(file_stream, **read_csv_opts)
                except Exception:
                    try:
                        file_stream.seek(0)
                        df = pd.read_csv(file_stream, encoding='latin-1', low_memory=True)
                    except Exception:
                        file_stream.seek(0)
                        df = pd.read_csv(file_stream, encoding='cp1252', low_memory=True)
            elif filename.lower().endswith('.xlsx') or filename.lower().endswith('.xls'):
                # For Excel files, only read the first sheet and avoid converters
                df = pd.read_excel(file_stream, sheet_name=0)
            else:
                raise ValueError(f"Unsupported file type: {filename}")

            # Handle NaN values
            df = df.fillna('')

            # Build summary without materializing huge lists for very large files
            total_rows = len(df)
            columns = df.columns.tolist()
            memory_usage = df.memory_usage(deep=True).sum()

            # For rows, convert to list only if size is reasonable, otherwise store as sampling
            if total_rows > 5000:
                # Keep only a sample for very large files
                sample_frac = min(5000 / total_rows, 1.0)
                rows = df.sample(frac=sample_frac, random_state=1).values.tolist()
            else:
                rows = df.values.tolist()

            data = {
                'columns': columns,
                'rows': rows,
                'shape': (total_rows, len(columns)),
                'summary': {
                    'total_rows': total_rows,
                    'total_columns': len(columns),
                    'column_types': df.dtypes.astype(str).to_dict(),
                    'memory_usage': memory_usage
                }
            }
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to process Excel file {filename}: {str(e)}")
            raise Exception(f"Failed to process Excel file: {str(e)}")
    
    @staticmethod
    def get_excel_preview(file_content: bytes, filename: str, max_rows: int = 10) -> str:
        """
        Get a text preview of Excel content for display purposes
        
        Args:
            file_content: Raw file content
            filename: Name of the file
            max_rows: Maximum number of rows to include in preview
            
        Returns:
            Formatted text preview
        """
        try:
            data = ExcelProcessor.process_excel_file(file_content, filename)
            
            preview_lines = []
            preview_lines.append(f"📊 Excel File: {filename}")
            preview_lines.append(f"📐 Dimensions: {data['shape'][0]} rows × {data['shape'][1]} columns")
            preview_lines.append(f"📋 Columns: {', '.join(data['columns'])}")
            preview_lines.append("")
            
            # Show first few rows
            preview_lines.append("📝 Sample Data:")
            for i, row in enumerate(data['rows'][:max_rows]):
                row_str = " | ".join([str(cell)[:50] + ("..." if len(str(cell)) > 50 else "") for cell in row])
                preview_lines.append(f"Row {i+1}: {row_str}")
            
            if len(data['rows']) > max_rows:
                preview_lines.append(f"... and {len(data['rows']) - max_rows} more rows")
            
            # Add column type information
            preview_lines.append("")
            preview_lines.append("📊 Column Types:")
            for col, dtype in data['summary']['column_types'].items():
                preview_lines.append(f"  {col}: {dtype}")
            
            return "\n".join(preview_lines)
            
        except Exception as e:
            logger.error(f"Error creating preview for {filename}: {str(e)}")
            return f"❌ Error processing Excel file: {str(e)}"
    
    @staticmethod
    def extract_text_for_vector_store(file_content: bytes, filename: str, max_rows: Optional[int] = None) -> str:
        """
        Extract text content from Excel file for vector store processing
        
        Args:
            file_content: Raw file content
            filename: Name of the file
            max_rows: Optional limit on rows (None = include all rows)
            
        Returns:
            Text representation suitable for vector store
        """
        try:
            data = ExcelProcessor.process_excel_file(file_content, filename)
            
            # Create comprehensive text representation
            text_parts = []
            
            # File metadata
            text_parts.append(f"Document: {filename}")
            text_parts.append(f"Type: Excel/CSV Spreadsheet")
            text_parts.append(f"Dimensions: {data['shape'][0]} rows, {data['shape'][1]} columns")
            text_parts.append(f"Memory Usage: {data['summary']['memory_usage']} bytes")
            text_parts.append("")
            
            # Column information
            text_parts.append("Columns and Data Types:")
            for col, dtype in data['summary']['column_types'].items():
                text_parts.append(f"- {col} ({dtype})")
            text_parts.append("")
            
            # Determine how many rows to include
            total_rows = data['summary']['total_rows']
            # rows may be a sampled subset if file is large
            available_rows = len(data['rows'])
            
            # Smart row limit based on file size and row count
            if max_rows is None:
                if total_rows <= 100:
                    # Small files: include all rows
                    rows_to_include = total_rows
                elif total_rows <= 1000:
                    # Medium files: include most rows but not all
                    rows_to_include = min(500, total_rows)
                elif total_rows <= 10000:
                    # Large files: include substantial sample
                    rows_to_include = min(1000, total_rows)
                else:
                    # Very large files: include representative sample
                    rows_to_include = min(2000, total_rows)
            else:
                rows_to_include = min(max_rows, total_rows)
            
            # Data content with complete or smart sampling
            text_parts.append("Data Content:")
            headers = data['columns']
            text_parts.append(" | ".join(headers))
            text_parts.append("-" * 50)
            
            if rows_to_include >= total_rows or available_rows <= rows_to_include:
                # Include all currently available rows (may be sampled)
                for i, row in enumerate(data['rows']):
                    row_str = " | ".join([str(cell) for cell in row])
                    text_parts.append(f"Row {i+1}: {row_str}")
                if available_rows < total_rows:
                    text_parts.append(f"[Sample of {available_rows} rows from total {total_rows} rows included]")
                else:
                    text_parts.append(f"[Complete dataset with {total_rows} rows included]")
            else:
                # Include sample with smart distribution
                if total_rows > rows_to_include:
                    # Include first chunk, middle chunk, and last chunk
                    first_chunk = rows_to_include // 3
                    middle_start = (total_rows - first_chunk) // 2
                    last_chunk = rows_to_include - (2 * first_chunk)
                    
                    # First rows (from available rows sample)
                    for i, row in enumerate(data['rows'][:first_chunk]):
                        row_str = " | ".join([str(cell) for cell in row])
                        text_parts.append(f"Row {i+1}: {row_str}")
                    
                    if middle_start > first_chunk:
                        text_parts.append(f"[... rows {first_chunk + 1} to {middle_start} omitted ...]")
                    
                    # Middle rows (sampled)
                    for i, row in enumerate(data['rows'][middle_start:middle_start + first_chunk]):
                        row_str = " | ".join([str(cell) for cell in row])
                        text_parts.append(f"Row {middle_start + i + 1}: {row_str}")
                    
                    if middle_start + first_chunk < total_rows - last_chunk:
                        text_parts.append(f"[... rows {middle_start + first_chunk + 1} to {total_rows - last_chunk} omitted ...]")
                    
                    # Last rows (from available rows sample)
                    for i, row in enumerate(data['rows'][-last_chunk:]):
                        row_str = " | ".join([str(cell) for cell in row])
                        text_parts.append(f"Row {total_rows - last_chunk + i + 1}: {row_str}")
                    
                    text_parts.append(f"[Sample of {rows_to_include} rows from total {total_rows} rows - distributed across beginning, middle, and end]")
                else:
                    # Include all available rows
                    for i, row in enumerate(data['rows'][:rows_to_include]):
                        row_str = " | ".join([str(cell) for cell in row])
                        text_parts.append(f"Row {i+1}: {row_str}")
            
            # Enhanced statistical summary for numerical columns
            try:
                df = pd.DataFrame(data['rows'], columns=data['columns'])
                numeric_cols = df.select_dtypes(include=['number']).columns
                text_cols = df.select_dtypes(include=['object']).columns
                
                if len(numeric_cols) > 0:
                    text_parts.append("")
                    text_parts.append("Numerical Analysis:")
                    for col in numeric_cols:
                        series = pd.to_numeric(df[col], errors='coerce').dropna()
                        if len(series) > 0:
                            text_parts.append(f"- {col}: min={series.min()}, max={series.max()}, mean={series.mean():.2f}, std={series.std():.2f}, count={len(series)}")
                
                if len(text_cols) > 0:
                    text_parts.append("")
                    text_parts.append("Text Column Analysis:")
                    for col in text_cols:
                        unique_values = df[col].nunique()
                        most_common = df[col].mode().iloc[0] if not df[col].empty else "N/A"
                        text_parts.append(f"- {col}: {unique_values} unique values, most common: '{most_common}'")
                        
                        # Show unique values if there aren't too many
                        if unique_values <= 20:
                            unique_list = df[col].unique().tolist()
                            text_parts.append(f"  Unique values: {unique_list}")
                            
            except Exception as stats_error:
                text_parts.append(f"[Statistical analysis failed: {stats_error}]")
            
            return "\n".join(text_parts)
            
        except Exception as e:
            logger.error(f"Error extracting text from {filename}: {str(e)}")
            return f"Error processing Excel file {filename}: {str(e)}"
    
    @staticmethod
    def extract_complete_text_for_vector_store(file_content: bytes, filename: str) -> str:
        """
        Extract ALL text content from Excel file for vector store processing (no row limits)
        Use this for smaller files where you want complete data inclusion
        
        Args:
            file_content: Raw file content
            filename: Name of the file
            
        Returns:
            Complete text representation suitable for vector store
        """
        return ExcelProcessor.extract_text_for_vector_store(file_content, filename, max_rows=None)
    
    @staticmethod
    def is_excel_file(filename: str) -> bool:
        """
        Check if a file is an Excel or CSV file
        
        Args:
            filename: Name of the file
            
        Returns:
            True if file is Excel/CSV, False otherwise
        """
        excel_extensions = {'.xls', '.xlsx', '.csv'}
        file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
        return f'.{file_ext}' in excel_extensions