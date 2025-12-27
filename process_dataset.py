#!/usr/bin/env python3
"""
Main Dataset Processing Pipeline
Converts OCR-extracted PDF text to Q&A dataset for LoRA fine-tuning
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict, Optional
from tqdm import tqdm
import logging

# Import our modules
from ocr_cleaner import OCRTextCleaner
from entity_extractor import TechnicalEntityExtractor
from table_reconstructor import TableReconstructor
from qa_generator import EnhancedQAGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatasetProcessor:
    """Main pipeline for processing OCR text to Q&A dataset"""
    
    def __init__(self, verbose: bool = True):
        self.cleaner = OCRTextCleaner()
        self.extractor = TechnicalEntityExtractor()
        self.table_reconstructor = TableReconstructor()
        self.qa_generator = EnhancedQAGenerator()
        self.verbose = verbose
        
        # Statistics tracking
        self.stats = {
            'total_entities': 0,
            'entities_by_type': {},
            'total_tables': 0,
            'tables_by_type': {},
            'total_qa_pairs': 0,
            'qa_by_category': {},
            'qa_by_difficulty': {}
        }
    
    def process_text_file(self, input_path: str, output_path: str, 
                         chunk_size: int = 1000) -> Dict[str, int]:
        """Process entire text file to Q&A dataset"""
        
        logger.info(f"Starting processing of {input_path}")
        
        # Read raw text
        with open(input_path, 'r', encoding='utf-8') as f:
            raw_text = f.read()
        
        logger.info(f"Loaded {len(raw_text)} characters of text")
        
        # Step 1: Clean text
        logger.info("🧹 Cleaning OCR text...")
        cleaned_text = self.cleaner.clean_text(raw_text)
        logger.info(f"Cleaned text: {len(cleaned_text)} characters")
        
        # Save cleaned text for debugging
        debug_dir = Path(output_path).parent / 'debug'
        debug_dir.mkdir(exist_ok=True)
        
        with open(debug_dir / 'cleaned_text.txt', 'w', encoding='utf-8') as f:
            f.write(cleaned_text)
        
        # Step 2: Segment into chunks
        logger.info("📄 Segmenting text into chunks...")
        chunks = self.cleaner.segment_into_chunks(cleaned_text, chunk_size)
        logger.info(f"Created {len(chunks)} chunks")
        
        # Step 3: Extract entities and tables from each chunk
        all_entities = []
        all_tables = []
        
        logger.info("🔍 Extracting technical entities and tables...")
        for idx, chunk in enumerate(tqdm(chunks, desc="Processing chunks")):
            # Extract entities
            chunk_entities = self.extractor.extract_all_entities(chunk)
            all_entities.extend(chunk_entities)
            
            # Extract tables
            chunk_tables = self.table_reconstructor.detect_and_extract_tables(chunk)
            all_tables.extend(chunk_tables)
            
            # Log progress periodically
            if self.verbose and idx % 10 == 0:
                logger.debug(f"Chunk {idx}: {len(chunk_entities)} entities, {len(chunk_tables)} tables")
        
        # Update statistics
        self._update_entity_stats(all_entities)
        self._update_table_stats(all_tables)
        
        logger.info(f"✅ Found {len(all_entities)} technical entities")
        logger.info(f"✅ Found {len(all_tables)} tables")
        
        # Log entity breakdown
        for entity_type, count in self.stats['entities_by_type'].items():
            logger.info(f"   - {entity_type}: {count}")
        
        # Step 4: Generate Q&A pairs
        logger.info("📝 Generating Q&A pairs...")
        qa_dataset = []
        
        # Generate from entities
        entity_qa = self.qa_generator.generate_qa_pairs(all_entities)
        qa_dataset.extend(entity_qa)
        logger.info(f"Generated {len(entity_qa)} Q&A pairs from entities")
        
        # Generate from tables
        for table in tqdm(all_tables, desc="Processing tables"):
            table_qa = self.qa_generator.generate_table_qa_pairs(table)
            qa_dataset.extend(table_qa)
        
        # Generate contextual Q&A pairs
        contextual_qa = self.qa_generator.generate_contextual_qa_pairs(all_entities)
        qa_dataset.extend(contextual_qa)
        logger.info(f"Generated {len(contextual_qa)} contextual Q&A pairs")
        
        # Remove duplicates
        qa_dataset = self._deduplicate_qa_pairs(qa_dataset)
        
        logger.info(f"✅ Total Q&A pairs after deduplication: {len(qa_dataset)}")
        self.stats['total_qa_pairs'] = len(qa_dataset)
        
        # Step 5: Save to JSONL
        logger.info(f"💾 Saving dataset to: {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            for qa in qa_dataset:
                f.write(json.dumps(qa, ensure_ascii=False) + '\n')
        
        # Save statistics
        stats_path = Path(output_path).parent / 'dataset_statistics.json'
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2)
        
        logger.info(f"📊 Statistics saved to: {stats_path}")
        
        # Save sample Q&As for review
        self._save_samples(qa_dataset, debug_dir)
        
        return self.stats
    
    def _update_entity_stats(self, entities):
        """Update entity statistics"""
        self.stats['total_entities'] = len(entities)
        
        for entity in entities:
            entity_type = entity.entity_type.value
            if entity_type not in self.stats['entities_by_type']:
                self.stats['entities_by_type'][entity_type] = 0
            self.stats['entities_by_type'][entity_type] += 1
    
    def _update_table_stats(self, tables):
        """Update table statistics"""
        self.stats['total_tables'] = len(tables)
        
        for table in tables:
            if table.table_type not in self.stats['tables_by_type']:
                self.stats['tables_by_type'][table.table_type] = 0
            self.stats['tables_by_type'][table.table_type] += 1
    
    def _deduplicate_qa_pairs(self, qa_pairs: List[Dict]) -> List[Dict]:
        """Remove duplicate Q&A pairs"""
        seen = set()
        unique_pairs = []
        
        for qa in qa_pairs:
            # Create a unique key based on question
            key = qa['messages'][0]['content'].lower().strip()
            
            if key not in seen:
                seen.add(key)
                unique_pairs.append(qa)
        
        return unique_pairs
    
    def _save_samples(self, qa_dataset: List[Dict], output_dir: Path, 
                     sample_size: int = 50):
        """Save sample Q&A pairs for manual review"""
        import random
        
        samples = random.sample(qa_dataset, min(sample_size, len(qa_dataset)))
        
        samples_path = output_dir / 'qa_samples.json'
        with open(samples_path, 'w', encoding='utf-8') as f:
            json.dump(samples, f, indent=2, ensure_ascii=False)
        
        # Also save in readable format
        readable_path = output_dir / 'qa_samples_readable.txt'
        with open(readable_path, 'w', encoding='utf-8') as f:
            for idx, qa in enumerate(samples):
                f.write(f"\n{'='*60}\n")
                f.write(f"Sample {idx + 1}:\n")
                f.write(f"Q: {qa['messages'][0]['content']}\n")
                f.write(f"A: {qa['messages'][1]['content']}\n")
        
        logger.info(f"📋 Saved {len(samples)} Q&A samples to: {samples_path}")

def main():
    parser = argparse.ArgumentParser(
        description="Convert OCR-extracted text to Q&A dataset for LoRA fine-tuning"
    )
    parser.add_argument(
        '--input', 
        type=str, 
        default='/mnt/user-data/uploads/chunks_output.txt',
        help='Path to input OCR text file'
    )
    parser.add_argument(
        '--output', 
        type=str, 
        default='/home/kylan/Coding/UnSlothPHi3.5/network_docs_chat_format.jsonl',
        help='Path to output JSONL file'
    )
    parser.add_argument(
        '--chunk-size', 
        type=int, 
        default=1000,
        help='Size of text chunks for processing'
    )
    parser.add_argument(
        '--verbose', 
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Create processor
    processor = DatasetProcessor(verbose=args.verbose)
    
    # Process file
    stats = processor.process_text_file(
        input_path=args.input,
        output_path=args.output,
        chunk_size=args.chunk_size
    )
    
    # Print summary
    print("\n" + "="*60)
    print("✨ Processing Complete!")
    print("="*60)
    print(f"📊 Summary:")
    print(f"   - Total entities extracted: {stats['total_entities']}")
    print(f"   - Total tables found: {stats['total_tables']}")
    print(f"   - Total Q&A pairs generated: {stats['total_qa_pairs']}")
    print(f"\n💾 Output saved to: {args.output}")
    print("="*60)

if __name__ == "__main__":
    main()
