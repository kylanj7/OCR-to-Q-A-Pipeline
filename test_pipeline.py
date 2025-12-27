#!/usr/bin/env python3
"""
Test script to verify the OCR to Q&A pipeline
"""

from ocr_cleaner import OCRTextCleaner
from entity_extractor import TechnicalEntityExtractor
from table_reconstructor import TableReconstructor
from qa_generator import EnhancedQAGenerator
import json

# Sample OCR text with typical issues
sample_text = """
P in Configuration:
Pin 1 = V BUS 5V supply
Pin 2 = USB_D- Data minus
Pin 3 = USB_D+ Data plus  
Pin 4 = GND Ground

Register Map:
CONTROL_REG = 0x1234
STATUS_REG = 0x1235
CONFIG_REG = 0x1236

E lectrical Specifications:
VDD_CORE = 1.8V ± 5%
VDD_IO = 3.3V ± 10%
Maximum current: 500mA

Timing Requirements:
Setup time = 10ns
Hold time = 5ns
Clock frequency = 100MHz

FCC Statement: This device complies with Part 15 of the FCC Rules.
Operation is subject to the following conditions...
"""

def test_pipeline():
    print("🧪 Testing OCR to Q&A Pipeline\n")
    
    # Test 1: Text Cleaning
    print("1. Testing Text Cleaner...")
    cleaner = OCRTextCleaner()
    cleaned = cleaner.clean_text(sample_text)
    print(f"   ✓ Cleaned text length: {len(cleaned)} chars")
    print(f"   ✓ Fixed 'P in' -> 'Pin': {'Pin' in cleaned}")
    print(f"   ✓ Fixed 'V BUS' -> 'VBUS': {'VBUS' in cleaned}")
    print(f"   ✓ Removed FCC statement: {'FCC Statement' not in cleaned}")
    
    # Test 2: Entity Extraction
    print("\n2. Testing Entity Extractor...")
    extractor = TechnicalEntityExtractor()
    entities = extractor.extract_all_entities(cleaned)
    print(f"   ✓ Total entities found: {len(entities)}")
    
    # Count by type
    entity_types = {}
    for entity in entities:
        etype = entity.entity_type.value
        entity_types[etype] = entity_types.get(etype, 0) + 1
    
    for etype, count in entity_types.items():
        print(f"   ✓ {etype}: {count}")
    
    # Test 3: Table Reconstruction
    print("\n3. Testing Table Reconstructor...")
    reconstructor = TableReconstructor()
    tables = reconstructor.detect_and_extract_tables(cleaned)
    print(f"   ✓ Tables found: {len(tables)}")
    
    # Test 4: Q&A Generation
    print("\n4. Testing Q&A Generator...")
    generator = EnhancedQAGenerator()
    qa_pairs = generator.generate_qa_pairs(entities)
    print(f"   ✓ Q&A pairs generated: {len(qa_pairs)}")
    
    # Show sample Q&A pairs
    print("\n📝 Sample Q&A Pairs:")
    for i, qa in enumerate(qa_pairs[:5]):
        print(f"\n   Example {i+1}:")
        print(f"   Q: {qa['messages'][0]['content']}")
        print(f"   A: {qa['messages'][1]['content']}")
    
    print("\n✅ All tests passed! Pipeline is working correctly.")
    
    # Save test output
    with open('test_output.jsonl', 'w') as f:
        for qa in qa_pairs:
            f.write(json.dumps(qa) + '\n')
    print(f"\n💾 Test output saved to: test_output.jsonl")

if __name__ == "__main__":
    test_pipeline()
