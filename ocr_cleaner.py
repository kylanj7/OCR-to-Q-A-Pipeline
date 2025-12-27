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
        
    def fix_ocr_artifacts(self, text: str) -> str:
        """Fix common OCR issues"""
        # Fix tech abbreviations first
        for correct, variants in self.tech_abbreviations.items():
            for variant in variants:
                text = re.sub(r'\b' + re.escape(variant) + r'\b', correct, text, flags=re.IGNORECASE)
        
        # Fix split words (but preserve intentional spaces in numbers/measurements)
        # Don't join if second part is a number or unit
        text = re.sub(r'(\w)\s+(\w)(?![0-9])', r'\1\2', text)
        
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
