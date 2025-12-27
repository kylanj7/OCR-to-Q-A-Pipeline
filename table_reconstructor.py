#!/usr/bin/env python3
"""
Table Reconstructor Module
Reconstructs tables from linearized OCR text
"""

import re
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

@dataclass
class TableCell:
    content: str
    row: int
    col: int

@dataclass
class Table:
    headers: List[str]
    rows: List[List[str]]
    context: str
    table_type: str  # pin_table, register_table, spec_table, etc.

class TableReconstructor:
    """Reconstruct tables from linearized OCR text"""
    
    def __init__(self):
        # Common table header patterns
        self.header_patterns = [
            # Pin tables
            re.compile(r'[Pp]in\s+[Nn]ame\s+[Ff]unction'),
            re.compile(r'[Pp]in\s+[Nn]umber\s+[Ss]ignal\s+[Nn]ame\s+[Dd]escription'),
            re.compile(r'[Pp]in\s+[Tt]ype\s+[Dd]escription'),
            
            # Register tables
            re.compile(r'[Rr]egister\s+[Aa]ddress\s+[Dd]escription'),
            re.compile(r'[Aa]ddress\s+[Nn]ame\s+[Aa]ccess\s+[Dd]efault'),
            re.compile(r'[Bb]it\s+[Ff]ield\s+[Aa]ccess\s+[Dd]escription'),
            
            # Specification tables
            re.compile(r'[Pp]arameter\s+[Mm]in\s+[Tt]yp\s+[Mm]ax\s+[Uu]nit'),
            re.compile(r'[Ss]ymbol\s+[Pp]arameter\s+[Cc]onditions\s+[Mm]in\s+[Mm]ax'),
            
            # Generic tables
            re.compile(r'[Nn]ame\s+[Vv]alue\s+[Dd]escription'),
            re.compile(r'[Ii]tem\s+[Ss]pecification'),
        ]
        
        # Patterns to identify table rows
        self.row_patterns = {
            'pin_row': re.compile(r'^\s*(\d+)\s+([A-Z_][A-Z0-9_]*)\s+(.+)$'),
            'register_row': re.compile(r'^\s*0x([0-9A-Fa-f]+)\s+([A-Z_][A-Z0-9_]*)\s+(.+)$'),
            'spec_row': re.compile(r'^\s*([A-Z_][A-Z0-9_]*)\s+(\d+\.?\d*)\s*(\w*)\s+(\d+\.?\d*)\s*(\w*)\s+(\d+\.?\d*)\s*(\w*)'),
            'bit_field_row': re.compile(r'^\s*\[?(\d+)(?::(\d+))?\]?\s+([A-Z_][A-Z0-9_]*)\s+([RW]/?[WO]?)\s+(.+)$'),
        }
    
    def detect_and_extract_tables(self, text: str) -> List[Table]:
        """Detect and extract all tables from text"""
        tables = []
        
        # Split text into potential table sections
        sections = self._split_into_sections(text)
        
        for section in sections:
            # Check if section contains a table
            table = self._extract_table_from_section(section)
            if table and len(table.rows) > 0:
                tables.append(table)
        
        return tables
    
    def _split_into_sections(self, text: str) -> List[str]:
        """Split text into sections that might contain tables"""
        # Use various delimiters to identify potential table boundaries
        sections = []
        
        # First, try to split by explicit table markers
        table_markers = [
            r'[Tt]able\s+\d+[:.]\s*',
            r'[Ff]igure\s+\d+[:.]\s*',
            r'\n\s*[-=]+\s*\n',  # Horizontal lines
        ]
        
        current_pos = 0
        for marker_pattern in table_markers:
            for match in re.finditer(marker_pattern, text):
                if match.start() > current_pos:
                    sections.append(text[current_pos:match.start()])
                current_pos = match.start()
        
        # Add remaining text
        if current_pos < len(text):
            sections.append(text[current_pos:])
        
        # If no explicit markers found, use paragraph-based splitting
        if len(sections) <= 1:
            sections = text.split('\n\n')
        
        return [s.strip() for s in sections if s.strip()]
    
    def _extract_table_from_section(self, section: str) -> Optional[Table]:
        """Extract a table from a text section"""
        lines = section.split('\n')
        
        # Try to find table headers
        header_line_idx = None
        headers = None
        table_type = None
        
        for idx, line in enumerate(lines):
            for pattern in self.header_patterns:
                if pattern.search(line):
                    header_line_idx = idx
                    headers = self._extract_headers(line)
                    table_type = self._determine_table_type(line)
                    break
            if headers:
                break
        
        if not headers:
            # Try heuristic detection
            headers, header_line_idx, table_type = self._heuristic_header_detection(lines)
        
        if not headers:
            return None
        
        # Extract rows starting from the line after headers
        rows = []
        for idx in range(header_line_idx + 1, len(lines)):
            line = lines[idx].strip()
            if not line:
                continue
            
            # Stop at next section or table
            if self._is_section_boundary(line):
                break
            
            row = self._extract_row(line, table_type, len(headers))
            if row and len(row) > 0:
                rows.append(row)
        
        if rows:
            return Table(
                headers=headers,
                rows=rows,
                context=section,
                table_type=table_type or 'generic'
            )
        
        return None
    
    def _extract_headers(self, line: str) -> List[str]:
        """Extract headers from a header line"""
        # Remove extra spaces and split by multiple spaces or tabs
        line = re.sub(r'\s+', ' ', line.strip())
        
        # Try different splitting strategies
        # First, try splitting by 2+ spaces
        headers = re.split(r'\s{2,}', line)
        
        if len(headers) <= 1:
            # Try splitting by common delimiters
            headers = re.split(r'\s*[|,]\s*', line)
        
        if len(headers) <= 1:
            # Last resort: split by single space
            headers = line.split()
        
        return [h.strip() for h in headers if h.strip()]
    
    def _determine_table_type(self, header_line: str) -> Optional[str]:
        """Determine the type of table based on headers"""
        header_lower = header_line.lower()
        
        if 'pin' in header_lower:
            return 'pin_table'
        elif 'register' in header_lower or 'address' in header_lower:
            return 'register_table'
        elif 'bit' in header_lower and 'field' in header_lower:
            return 'bit_field_table'
        elif any(word in header_lower for word in ['parameter', 'specification', 'min', 'max']):
            return 'spec_table'
        elif 'error' in header_lower or 'code' in header_lower:
            return 'error_table'
        
        return 'generic_table'
    
    def _heuristic_header_detection(self, lines: List[str]) -> Tuple[Optional[List[str]], Optional[int], Optional[str]]:
        """Use heuristics to detect table headers when no explicit pattern matches"""
        for idx, line in enumerate(lines):
            if idx >= len(lines) - 1:
                continue
            
            # Look for lines with consistent structure
            words = line.split()
            if 2 <= len(words) <= 6:  # Reasonable number of columns
                # Check if next few lines have similar structure
                similar_lines = 0
                for next_idx in range(idx + 1, min(idx + 4, len(lines))):
                    next_words = lines[next_idx].split()
                    if abs(len(next_words) - len(words)) <= 1:
                        similar_lines += 1
                
                if similar_lines >= 2:
                    # Likely found a table
                    headers = self._extract_headers(line)
                    table_type = self._guess_table_type_from_content(lines[idx:idx+5])
                    return headers, idx, table_type
        
        return None, None, None
    
    def _guess_table_type_from_content(self, lines: List[str]) -> str:
        """Guess table type from content"""
        content = ' '.join(lines).lower()
        
        if re.search(r'\bpin\s+\d+\b', content):
            return 'pin_table'
        elif re.search(r'0x[0-9a-f]+', content):
            return 'register_table'
        elif re.search(r'\d+\.\d+\s*[vm]', content):
            return 'spec_table'
        
        return 'generic_table'
    
    def _extract_row(self, line: str, table_type: Optional[str], expected_cols: int) -> Optional[List[str]]:
        """Extract a row from a line based on table type"""
        if not line.strip():
            return None
        
        # Try specific patterns based on table type
        if table_type:
            for pattern_name, pattern in self.row_patterns.items():
                if table_type in pattern_name or table_type == 'generic_table':
                    match = pattern.match(line)
                    if match:
                        return list(match.groups())
        
        # Fallback: intelligent splitting
        return self._intelligent_split(line, expected_cols)
    
    def _intelligent_split(self, line: str, expected_cols: int) -> List[str]:
        """Intelligently split a line into columns"""
        # First, try splitting by multiple spaces
        parts = re.split(r'\s{2,}', line.strip())
        
        if len(parts) == expected_cols:
            return parts
        
        # Try splitting by tabs
        parts = line.strip().split('\t')
        if len(parts) == expected_cols:
            return parts
        
        # Try to identify columns by patterns
        # Look for common patterns like numbers, hex values, etc.
        patterns = [
            r'0x[0-9A-Fa-f]+',  # Hex numbers
            r'\b\d+\b',  # Integers
            r'\b\d+\.\d+\b',  # Decimals
            r'\b[A-Z_][A-Z0-9_]*\b',  # Identifiers
        ]
        
        # Extract all pattern matches and their positions
        matches = []
        for pattern in patterns:
            for match in re.finditer(pattern, line):
                matches.append((match.start(), match.end(), match.group()))
        
        # Sort by position
        matches.sort(key=lambda x: x[0])
        
        # Build columns
        columns = []
        last_end = 0
        
        for start, end, text in matches:
            # Check if there's text between matches
            if start > last_end:
                between_text = line[last_end:start].strip()
                if between_text and not between_text.isspace():
                    columns.append(between_text)
            
            columns.append(text)
            last_end = end
        
        # Add any remaining text
        if last_end < len(line):
            remaining = line[last_end:].strip()
            if remaining:
                columns.append(remaining)
        
        # If we still don't have the right number of columns, use simple split
        if len(columns) != expected_cols:
            columns = line.strip().split()[:expected_cols]
        
        return columns
    
    def _is_section_boundary(self, line: str) -> bool:
        """Check if a line marks the boundary of a section"""
        # Check for common section markers
        section_patterns = [
            r'^[A-Z][A-Z\s]+:?\s*$',  # All caps headers
            r'^\d+\.\s+[A-Z]',  # Numbered sections
            r'^[Nn]ote:',  # Notes
            r'^[Cc]aution:',  # Cautions
            r'^[-=]{5,}$',  # Horizontal lines
        ]
        
        for pattern in section_patterns:
            if re.match(pattern, line.strip()):
                return True
        
        return False
    
    def tables_to_entities(self, table: Table) -> List[Dict[str, any]]:
        """Convert a table to a list of entity dictionaries for Q&A generation"""
        entities = []
        
        for row in table.rows:
            entity = {
                'table_type': table.table_type,
                'headers': table.headers,
                'values': row,
                'data': {}
            }
            
            # Map values to headers
            for idx, header in enumerate(table.headers):
                if idx < len(row):
                    entity['data'][header] = row[idx]
            
            entities.append(entity)
        
        return entities
