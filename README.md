# OCR to Q&A Dataset Processor for LoRA Fine-Tuning

This pipeline converts unorganized OCR-extracted text from technical PDFs into high-quality Q&A pairs for fine-tuning language models using LoRA adapters.

## Features

- **OCR Artifact Cleaning**: Fixes common OCR issues (split words, spacing, abbreviations)
- **Compliance Filtering**: Automatically removes FCC statements and safety warnings
- **Multi-Entity Extraction**:
  - Pin configurations
  - Register addresses and values
  - Voltage/current specifications
  - Timing requirements
  - Bit field definitions
  - Error codes
  - Step-by-step procedures
- **Table Reconstruction**: Rebuilds tables from linearized OCR text
- **Context-Aware Q&A Generation**: Creates multiple question types per fact:
  - Factual questions
  - Reverse lookups
  - Troubleshooting scenarios
  - Integration questions
  - Comparison questions
- **Granular Output**: Generates highly specific Q&A pairs perfect for technical documentation

## Installation

```bash
# Install required packages
pip install tqdm

# Clone or copy all modules to your working directory
```

## Usage

### Basic Usage

```bash
python process_dataset.py --input /path/to/ocr_text.txt --output /path/to/qa_dataset.jsonl
```

### With Custom Options

```bash
python process_dataset.py \
    --input /mnt/user-data/uploads/chunks_output.txt \
    --output /home/kylan/Coding/UnSlothPHi3.5/network_docs_chat_format.jsonl \
    --chunk-size 1500 \
    --verbose
```

### Parameters

- `--input`: Path to OCR-extracted text file
- `--output`: Path for output JSONL file (compatible with your Unsloth training script)
- `--chunk-size`: Size of text chunks for processing (default: 1000 words)
- `--verbose`: Enable detailed logging

## Output Format

The pipeline generates a JSONL file where each line contains:

```json
{
  "messages": [
    {"role": "user", "content": "What is the function of Pin 3?"},
    {"role": "assistant", "content": "VBUS - 5V power supply"}
  ]
}
```

## Example Outputs

### Pin Information
- Q: "What is the function of Pin 7?"
- A: "GPIO_12 - General Purpose Input/Output"

### Register Configuration
- Q: "How do I configure the CONTROL_REG?"
- A: "Write the appropriate value to CONTROL_REG at address 0x1234. Ensure the device is in configuration mode before writing."

### Voltage Specifications
- Q: "What voltage is required for VDD_CORE?"
- A: "1.8V ± 5%"

### Troubleshooting
- Q: "What should I check if Pin 5 is not functioning correctly?"
- A: "Verify that Pin 5 is properly connected and providing USB_D+. Check for proper voltage levels and ensure no shorts to ground or adjacent pins."

## Generated Files

The processor creates several files:

1. **Main Output**: `network_docs_chat_format.jsonl` - Training dataset
2. **Debug Files** (in `debug/` folder):
   - `cleaned_text.txt` - OCR-cleaned text
   - `qa_samples.json` - Sample Q&A pairs (JSON format)
   - `qa_samples_readable.txt` - Human-readable samples
3. **Statistics**: `dataset_statistics.json` - Processing statistics

## Customization

### Adding New Entity Types

Edit `entity_extractor.py` to add new patterns:

```python
self.patterns['new_type'] = [
    re.compile(r'your_pattern_here'),
]
```

### Modifying Q&A Templates

Edit `qa_generator.py` to add new question templates:

```python
self.templates[EntityType.YOUR_TYPE] = {
    'factual': [
        ("Your question template with {name}?", "Answer with {value}"),
    ],
}
```

## Troubleshooting

### No entities found
- Check if compliance filtering is too aggressive
- Verify OCR quality in cleaned_text.txt
- Adjust regex patterns for your document format

### Low Q&A count
- Increase chunk size for better context
- Check entity extraction patterns match your data
- Review table detection thresholds

## Performance Tips

- Process in batches if handling multiple files
- Use `--verbose` to identify bottlenecks
- Review samples before full training
- Adjust chunk_size based on document structure

## Integration with LoRA Training

The output is directly compatible with your Unsloth training script:

```python
# Your existing code works as-is!
dataset = load_dataset('json', data_files=CONFIG['dataset_path'], split='train')
```
