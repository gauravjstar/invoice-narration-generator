"""Duplicate detection service"""
import logging
from typing import List, Dict, Tuple, Optional
from fuzzywuzzy import fuzz
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DuplicateDetectionService:
    """Detect duplicate invoices"""
    
    # Similarity thresholds
    GSTIN_WEIGHT = 0.3
    INVOICE_NUMBER_WEIGHT = 0.35
    DATE_WEIGHT = 0.15
    AMOUNT_WEIGHT = 0.2
    
    # Tolerances
    DATE_TOLERANCE_DAYS = 7
    AMOUNT_TOLERANCE_PERCENT = 1.0  # 1% tolerance
    
    @staticmethod
    def check_duplicate(
        invoice_number: str,
        invoice_date: str,
        vendor_gstin: str,
        total_amount: float,
        existing_invoices: List[Dict]
    ) -> Tuple[bool, Optional[str], float]:
        """
        Check if invoice is duplicate.
        Returns: (is_duplicate, duplicate_invoice_id, similarity_score)
        """
        try:
            highest_similarity = 0.0
            most_similar_id = None
            
            for existing in existing_invoices:
                similarity = DuplicateDetectionService._calculate_similarity(
                    invoice_number,
                    invoice_date,
                    vendor_gstin,
                    total_amount,
                    existing
                )
                
                if similarity > highest_similarity:
                    highest_similarity = similarity
                    most_similar_id = existing.get('id')
            
            is_duplicate = highest_similarity >= 0.85  # 85% threshold
            
            logger.info(f"Duplicate check: similarity={highest_similarity:.2f}, is_duplicate={is_duplicate}")
            return is_duplicate, most_similar_id, highest_similarity
            
        except Exception as e:
            logger.error(f"Duplicate detection failed: {str(e)}")
            return False, None, 0.0
    
    @staticmethod
    def _calculate_similarity(
        invoice_number: str,
        invoice_date: str,
        vendor_gstin: str,
        total_amount: float,
        existing_invoice: Dict
    ) -> float:
        """Calculate overall similarity score"""
        try:
            scores = {}
            
            # GSTIN matching
            if vendor_gstin and existing_invoice.get('vendor_gstin'):
                gstin_match = fuzz.token_set_ratio(
                    vendor_gstin.upper(),
                    existing_invoice.get('vendor_gstin', '').upper()
                ) / 100.0
                scores['gstin'] = gstin_match
            else:
                scores['gstin'] = 0.5
            
            # Invoice number matching
            if invoice_number and existing_invoice.get('invoice_number'):
                number_match = fuzz.token_set_ratio(
                    invoice_number.upper(),
                    existing_invoice.get('invoice_number', '').upper()
                ) / 100.0
                scores['number'] = number_match
            else:
                scores['number'] = 0.5
            
            # Date matching
            date_match = DuplicateDetectionService._match_dates(
                invoice_date,
                existing_invoice.get('invoice_date_str', '')
            )
            scores['date'] = date_match
            
            # Amount matching
            amount_match = DuplicateDetectionService._match_amounts(
                total_amount,
                existing_invoice.get('total_amount', 0)
            )
            scores['amount'] = amount_match
            
            # Calculate weighted score
            weighted_score = (
                scores.get('gstin', 0) * DuplicateDetectionService.GSTIN_WEIGHT +
                scores.get('number', 0) * DuplicateDetectionService.INVOICE_NUMBER_WEIGHT +
                scores.get('date', 0) * DuplicateDetectionService.DATE_WEIGHT +
                scores.get('amount', 0) * DuplicateDetectionService.AMOUNT_WEIGHT
            )
            
            return weighted_score
            
        except Exception as e:
            logger.warning(f"Similarity calculation failed: {str(e)}")
            return 0.0
    
    @staticmethod
    def _match_dates(date1: str, date2: str) -> float:
        """Match two date strings"""
        try:
            from datetime import datetime
            
            # Parse dates
            date_formats = [
                '%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d', '%Y/%m/%d',
                '%d %b %Y', '%d %B %Y'
            ]
            
            dt1 = None
            dt2 = None
            
            for fmt in date_formats:
                if dt1 is None:
                    try:
                        dt1 = datetime.strptime(date1, fmt)
                    except:
                        pass
                if dt2 is None:
                    try:
                        dt2 = datetime.strptime(date2, fmt)
                    except:
                        pass
            
            if dt1 and dt2:
                diff = abs((dt1 - dt2).days)
                if diff == 0:
                    return 1.0
                elif diff <= DuplicateDetectionService.DATE_TOLERANCE_DAYS:
                    return 1.0 - (diff / DuplicateDetectionService.DATE_TOLERANCE_DAYS) * 0.3
                else:
                    return 0.0
            
            return 0.5
        except:
            return 0.5
    
    @staticmethod
    def _match_amounts(amount1: float, amount2: float) -> float:
        """Match two amounts with tolerance"""
        try:
            if amount1 == 0 or amount2 == 0:
                return 0.5
            
            diff_percent = abs(amount1 - amount2) / max(amount1, amount2) * 100
            
            if diff_percent == 0:
                return 1.0
            elif diff_percent <= DuplicateDetectionService.AMOUNT_TOLERANCE_PERCENT:
                return 1.0 - (diff_percent / DuplicateDetectionService.AMOUNT_TOLERANCE_PERCENT) * 0.2
            else:
                return 0.0
        except:
            return 0.5
