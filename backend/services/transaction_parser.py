#!/usr/bin/env python3
"""
Transaction parser for bank statements
Extracts individual transactions with metadata for better search accuracy
"""

import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)

class TransactionParser:
    def __init__(self):
        # Common date patterns in bank statements
        self.date_patterns = [
            r'(\d{1,2}/\d{1,2}/\d{2,4})',  # MM/DD/YY or MM/DD/YYYY
            r'(\d{1,2}-\d{1,2}-\d{2,4})',  # MM-DD-YY or MM-DD-YYYY
            r'(\d{4}-\d{1,2}-\d{1,2})',    # YYYY-MM-DD
        ]
        
        # Amount patterns (positive/negative numbers with optional currency symbols)
        self.amount_patterns = [
            r'([+-]?\$?[\d,]+\.?\d*)',  # $123.45, -123.45, +123.45
            r'([+-]?[\d,]+\.?\d*)',     # 123.45, -123.45, +123.45
        ]
        
        # Common transaction keywords that indicate a transaction line
        self.transaction_indicators = [
            'des:', 'id:', 'indn:', 'co id:', 'web', 'pos', 'atm', 'check', 'deposit',
            'withdrawal', 'transfer', 'payment', 'charge', 'fee', 'rebill', 'autopay'
        ]
    
    def parse_transactions(self, text: str) -> List[Dict[str, Any]]:
        """Parse text and extract individual transactions"""
        transactions = []
        lines = text.split('\n')
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Try to parse as a transaction
            transaction = self._parse_transaction_line(line, line_num)
            if transaction:
                transactions.append(transaction)
        
        logger.info(f"Parsed {len(transactions)} transactions from text")
        return transactions
    
    def _parse_transaction_line(self, line: str, line_num: int) -> Optional[Dict[str, Any]]:
        """Parse a single line as a transaction (generic/dynamic regex)"""
        try:
            # Generic regex: date, description (any words), optional ID, amount (at end or after desc)
            # Example: 12/12/22 E-ZPASSPAYMENT DES:EZPASS ID:5229569 INDN:... -240.00
            pattern = re.compile(
                r'(?P<date>\d{1,2}[/-]\d{1,2}[/-]\d{2,4})?\s*'
                r'(?P<desc>.+?)?'
                r'(ID:(?P<id>\d+))?'
                r'.*?(?P<amount>[-+]?\$?\d{1,6}(?:\.\d{2})?)?\s*$'
            )
            match = pattern.match(line)
            if match:
                date = self._extract_date(line)
                amount = self._extract_amount(line)
                desc = match.group('desc') or ''
                # Try to extract ID if present
                id_match = re.search(r'ID:(\d+)', line)
                trans_id = id_match.group(1) if id_match else None
                # Clean up description
                desc = desc.strip()
                # Only consider as transaction if at least date, desc, and amount are present
                if date and desc and amount is not None:
                    transaction = {
                        'date': date,
                        'description': desc,
                        'amount': amount,
                        'raw_text': line,
                        'line_number': line_num,
                        'transaction_id': trans_id,
                        'confidence': self._calculate_confidence(line, date, amount, desc)
                    }
                    return transaction
            # Fallback to old logic if generic regex doesn't match
            return super()._parse_transaction_line(line, line_num) if hasattr(super(), '_parse_transaction_line') else None
        except Exception as e:
            logger.warning(f"Failed to parse transaction line '{line}': {e}")
            return None
    
    def _is_transaction_line(self, line: str) -> bool:
        """Check if a line looks like a transaction"""
        line_lower = line.lower()
        
        # Check for transaction indicators
        has_indicator = any(indicator in line_lower for indicator in self.transaction_indicators)
        
        # Check for amount pattern
        has_amount = any(re.search(pattern, line) for pattern in self.amount_patterns)
        
        # Check for date pattern
        has_date = any(re.search(pattern, line) for pattern in self.date_patterns)
        
        # Must have at least 2 of: indicator, amount, or date
        indicators_count = sum([has_indicator, has_amount, has_date])
        
        return indicators_count >= 2
    
    def _extract_date(self, line: str) -> Optional[str]:
        """Extract date from transaction line"""
        for pattern in self.date_patterns:
            match = re.search(pattern, line)
            if match:
                date_str = match.group(1)
                try:
                    # Try to parse and standardize the date
                    if '/' in date_str:
                        if len(date_str.split('/')[-1]) == 2:
                            # MM/DD/YY format
                            date_obj = datetime.strptime(date_str, '%m/%d/%y')
                        else:
                            # MM/DD/YYYY format
                            date_obj = datetime.strptime(date_str, '%m/%d/%Y')
                    elif '-' in date_str:
                        if len(date_str.split('-')[-1]) == 2:
                            # MM-DD-YY format
                            date_obj = datetime.strptime(date_str, '%m-%d-%y')
                        else:
                            # YYYY-MM-DD format
                            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    else:
                        continue
                    
                    return date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    continue
        
        return None
    
    def _extract_amount(self, line: str) -> Optional[float]:
        """Extract amount from transaction line"""
        for pattern in self.amount_patterns:
            matches = re.findall(pattern, line)
            for match in matches:
                try:
                    # Clean up the amount string
                    amount_str = match.replace('$', '').replace(',', '')
                    amount = float(amount_str)
                    
                    # Validate that this looks like a reasonable amount
                    if -1000000 <= amount <= 1000000:
                        return amount
                except ValueError:
                    continue
        
        return None
    
    def _extract_description(self, line: str, date: Optional[str], amount: Optional[float]) -> Optional[str]:
        """Extract description from transaction line"""
        # Remove date and amount from the line to get description
        description = line
        
        # Remove date
        if date:
            for pattern in self.date_patterns:
                description = re.sub(pattern, '', description)
        
        # Remove amount
        if amount:
            for pattern in self.amount_patterns:
                description = re.sub(pattern, '', description)
        
        # Clean up the description
        description = re.sub(r'\s+', ' ', description).strip()
        
        # Remove common prefixes/suffixes
        description = re.sub(r'^(web|pos|atm|check)\s*', '', description, flags=re.IGNORECASE)
        description = re.sub(r'\s+(web|pos|atm|check)$', '', description, flags=re.IGNORECASE)
        
        # Must have some meaningful content
        if len(description) < 3:
            return None
        
        return description
    
    def _calculate_confidence(self, line: str, date: Optional[str], amount: Optional[float], description: Optional[str]) -> float:
        """Calculate confidence score for the parsed transaction"""
        confidence = 0.0
        
        # Base confidence
        if date:
            confidence += 0.3
        if amount:
            confidence += 0.3
        if description:
            confidence += 0.2
        
        # Bonus for having all components
        if date and amount and description:
            confidence += 0.2
        
        # Bonus for transaction indicators
        line_lower = line.lower()
        if any(indicator in line_lower for indicator in self.transaction_indicators):
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def create_transaction_chunks(self, transactions: List[Dict[str, Any]], doc_id: str, filename: str) -> List[Dict[str, Any]]:
        """Create chunks for individual transactions"""
        chunks = []
        
        for i, transaction in enumerate(transactions):
            # Create a structured text representation for embedding
            structured_text = self._create_structured_text(transaction)
            
            chunk = {
                'chunk_id': f"{doc_id}_transaction_{i}",
                'doc_id': doc_id,
                'text': structured_text,
                'chunk_index': i,
                'metadata': {
                    'filename': filename,
                    'file_type': 'application/pdf',
                    'doc_id': doc_id,
                    'chunk_index': i,
                    'total_chunks': len(transactions),
                    'type': 'transaction',
                    'transaction_date': transaction.get('date'),
                    'transaction_amount': transaction.get('amount'),
                    'transaction_description': transaction.get('description'),
                    'raw_text': transaction.get('raw_text'),
                    'confidence': transaction.get('confidence', 0.0)
                }
            }
            chunks.append(chunk)
        
        logger.info(f"Created {len(chunks)} transaction chunks")
        return chunks
    
    def _create_structured_text(self, transaction: Dict[str, Any]) -> str:
        """Create structured text for embedding"""
        parts = []
        
        if transaction.get('date'):
            parts.append(f"Date: {transaction['date']}")
        
        if transaction.get('description'):
            parts.append(f"Description: {transaction['description']}")
        
        if transaction.get('amount') is not None:
            parts.append(f"Amount: {transaction['amount']}")
        
        if transaction.get('raw_text'):
            parts.append(f"Raw: {transaction['raw_text']}")
        
        return " | ".join(parts)

# Global instance
transaction_parser = TransactionParser() 