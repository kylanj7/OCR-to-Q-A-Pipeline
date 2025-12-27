#!/usr/bin/env python3
"""
OCR Text Cleaner Module
Cleans and normalizes OCR-extracted text from technical documentation
"""

import re
from typing import List, Dict, Tuple

class OCRTextCleaner:
    """Clean and normalize OCR-extracted text"""

    def __init__(self):
        # Common technical abbreviations that get split by OCR
        self.tech_abbreviations = {
            'PCIe': ['pcie', 'pci-e', 'pci e', 'PC Ie', 'PCI E'],
            'GPIO': ['gpio', 'gp io', 'GP IO'],
            'VBUS': ['vbus', 'v bus', 'V BUS'],
            'UART': ['uart', 'u art', 'U ART'],
            'I2C': ['i2c', 'i 2c', 'I 2 C'],
            'SPI': ['spi', 's pi', 'S PI'],
            'USB': ['usb', 'u sb', 'U SB'],
            'BIOS': ['bios', 'bi os', 'B IOS'],
            'DDR4': ['ddr4', 'ddr 4', 'DDR 4'],
            'DIMM': ['dimm', 'di mm', 'D IMM'],
            'CPU': ['cpu', 'c pu', 'C PU'],
            'MHz': ['mhz', 'm hz', 'M Hz'],
            'GHz': ['ghz', 'g hz', 'G Hz'],
        }

        # Compliance/safety patterns to remove
        self.compliance_patterns = [
            r'FCC\s+[Ss]tatement.*?(?=\n\n|[A-Z][a-z]+:|\Z)',
            r'[Ss]afety\s+[Ww]arning.*?(?=\n\n|[A-Z][a-z]+:|\Z)',
            r'[Cc]ompliance\s+[Nn]ote.*?(?=\n\n|[A-Z][a-z]+:|\Z)',
            r'[Ww]arranty\s+[Dd]isclaimer.*?(?=\n\n|[A-Z][a-z]+:|\Z)',
            r'[Ll]egal\s+[Nn]otice.*?(?=\n\n|[A-Z][a-z]+:|\Z)',
            r'This\s+device\s+complies\s+with.*?(?=\n\n|[A-Z][a-z]+:|\Z)',
            r'[Cc]aution:.*?electric\s+shock.*?(?=\n\n|[A-Z][a-z]+:|\Z)',
        ]

    def fix_ocr_artifacts(self, text: str) -> str:
        """Fix common OCR issues"""

        # Fix tech abbreviations first
        for correct, variants in self.tech_abbreviations.items():
            for variant in variants:
                text = re.sub(r'\b' + re.escape(variant) + r'\b', correct, text, flags=re.IGNORECASE)

        # Smart word separation using multiple patterns

        # 1. Add space between lowercase and uppercase
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)

        # 2. Common words that often get concatenated - insert spaces around them
        common_words = [
            'the', 'and', 'for', 'are', 'was', 'were', 'has', 'have', 'with', 'from',
            'that', 'this', 'these', 'those', 'after', 'before', 'during', 'through',
            'about', 'above', 'below', 'between', 'into', 'onto', 'upon', 'within',
            'without', 'because', 'since', 'unless', 'until', 'while', 'where',
            'when', 'what', 'which', 'who', 'why', 'how', 'if', 'then', 'else',
            'step', 'goto', 'complete', 'ensure', 'check', 'verify', 'perform',
            'configure', 'install', 'update', 'system', 'error', 'warning', 'message',
            'procedure', 'following', 'indicates', 'unit', 'specification'
        ]

        # Create word boundary pattern for common words
        for word in common_words:
            # Add space before the word if preceded by non-space
            pattern = rf'(?<=[a-zA-Z])({word})(?=[A-Z])'
            text = re.sub(pattern, r' \1 ', text, flags=re.IGNORECASE)

        # 3. Fix specific technical documentation patterns
        text = re.sub(r'([a-z])(YES|NO)([A-Z])', r'\1 \2 \3', text)
        text = re.sub(r'step(\d+)', r'step \1', text, flags=re.IGNORECASE)
        text = re.sub(r'Gotostep', 'Go to step', text, flags=re.IGNORECASE)
        text = re.sub(r'Performthe', 'Perform the', text, flags=re.IGNORECASE)
        text = re.sub(r'Completethe', 'Complete the', text, flags=re.IGNORECASE)

        # 4. Fix patterns like "ResultsIf" or "ProcedurevTo"
        text = re.sub(r'Results([A-Z])', r'Results \1', text)
        text = re.sub(r'Procedure([a-z])', r'Procedure \1', text)
        text = re.sub(r'([a-z])Procedure', r'\1 Procedure', text)

        # Fix spacing around punctuation
        text = re.sub(r'\s+([.,;:])', r'\1', text)
        text = re.sub(r'([.,;:])\s*([a-zA-Z])', r'\1 \2', text)

        # Fix parentheses spacing
        text = re.sub(r'\(\s+', '(', text)
        text = re.sub(r'\s+\)', ')', text)

        # Fix equals signs and colons
        text = re.sub(r'\s*=\s*', ' = ', text)
        text = re.sub(r'\s*:\s*', ': ', text)

        # Normalize multiple spaces (but preserve paragraph breaks)
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Fix common OCR number/letter confusion
        text = re.sub(r'\b0x([0-9A-Fa-f]+)\b', r'0x\1', text)  # Hex numbers
        text = re.sub(r'\bl([0-9]+)\b', r'1\1', text)  # l -> 1
        text = re.sub(r'\bO([0-9]+)\b', r'0\1', text)  # O -> 0

        return text.strip()

    def remove_compliance_sections(self, text: str) -> str:
        """Remove FCC/safety compliance text"""
        for pattern in self.compliance_patterns:
            text = re.sub(pattern, '', text, flags=re.DOTALL | re.MULTILINE)
        return text

    def normalize_technical_terms(self, text: str) -> str:
        """Normalize technical terms and units"""
        # Normalize units
        text = re.sub(r'(\d+)\s*(ns|ms|us|μs)', r'\1\2', text)
        text = re.sub(r'(\d+)\s*(MHz|GHz|KHz)', r'\1\2', text)
        text = re.sub(r'(\d+)\s*(mA|A|μA)', r'\1\2', text)
        text = re.sub(r'(\d+)\s*(V|mV)', r'\1\2', text)
        text = re.sub(r'(\d+)\s*(K|M|G)B', r'\1\2B', text)

        # Normalize hex notation
        text = re.sub(r'\b0[xX]([0-9A-Fa-f]+)\b', r'0x\1', text)

        # Normalize bit notation
        text = re.sub(r'[Bb]it\s*\[(\d+):(\d+)\]', r'Bit[\1:\2]', text)
        text = re.sub(r'[Bb]it\s+(\d+)', r'Bit \1', text)

        return text

    def segment_into_chunks(self, text: str, chunk_size: int = 1000) -> List[str]:
        """Segment text into meaningful chunks for processing"""
        # Split by double newlines first (paragraph boundaries)
        paragraphs = text.split('\n\n')

        chunks = []
        current_chunk = []
        current_size = 0

        for para in paragraphs:
            para_size = len(para.split())

            if current_size + para_size > chunk_size and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [para]
                current_size = para_size
            else:
                current_chunk.append(para)
                current_size += para_size

        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))

        return chunks

    def clean_text(self, text: str) -> str:
        """Main cleaning pipeline"""
        # Apply all cleaning steps in order
        text = self.fix_ocr_artifacts(text)
        text = self.remove_compliance_sections(text)
        text = self.normalize_technical_terms(text)
        return text
