#!/usr/bin/env python3
"""
Technical Entity Extractor Module
Extracts structured technical entities from cleaned documentation text
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple
from enum import Enum

class EntityType(Enum):
    PIN = "pin"
    REGISTER = "register"
    VOLTAGE = "voltage"
    TIMING = "timing"
    FREQUENCY = "frequency"
    CURRENT = "current"
    BITFIELD = "bitfield"
    PROCEDURE_STEP = "procedure_step"
    ERROR_CODE = "error_code"
    CONFIGURATION = "configuration"

@dataclass
class TechnicalEntity:
    entity_type: EntityType
    name: str
    value: Optional[str]
    unit: Optional[str]
    context: str
    metadata: Optional[Dict[str, str]] = None

class TechnicalEntityExtractor:
    """Extract technical entities from text"""
    
    def __init__(self):
        # Compile regex patterns for efficiency
        self.patterns = {
            'pin': [
                re.compile(r'[Pp]in\s+(\d+)\s*[=:]\s*([A-Z_][A-Z0-9_]*(?:\s+[A-Z_][A-Z0-9_]*)*)'),
                re.compile(r'[Pp]in\s+([A-Z][0-9]+)\s*[=:]\s*([A-Z_][A-Z0-9_]*)'),
                re.compile(r'([A-Z_][A-Z0-9_]*)\s+on\s+[Pp]in\s+(\d+)'),
            ],
            'register': [
                re.compile(r'[Rr]egister\s+(?:at\s+)?0x([0-9A-Fa-f]+)'),
                re.compile(r'0x([0-9A-Fa-f]+)\s*[=:]\s*0x([0-9A-Fa-f]+)'),
                re.compile(r'([A-Z_][A-Z0-9_]*)\s+[Rr]egister\s*[=:]\s*0x([0-9A-Fa-f]+)'),
                re.compile(r'[Aa]ddress\s*[=:]\s*0x([0-9A-Fa-f]+)'),
            ],
            'voltage': [
                re.compile(r'(\d+\.?\d*)\s*V\s*(?:±\s*(\d+\.?\d*)%)?'),
                re.compile(r'([A-Z_][A-Z0-9_]*)\s*[=:]\s*(\d+\.?\d*)\s*V'),
                re.compile(r'[Vv]oltage\s*[=:]\s*(\d+\.?\d*)\s*V'),
            ],
            'timing': [
                re.compile(r'(\d+\.?\d*)\s*(ns|us|ms|μs|s)\s+([a-zA-Z\s]+time)'),
                re.compile(r'([a-zA-Z\s]+time)\s*[=:]\s*(\d+\.?\d*)\s*(ns|us|ms|μs|s)'),
                re.compile(r'[Tt]iming\s*[=:]\s*(\d+\.?\d*)\s*(ns|us|ms|μs|s)'),
                re.compile(r'[Dd]elay\s*[=:]\s*(\d+\.?\d*)\s*(ns|us|ms|μs|s)'),
            ],
            'frequency': [
                re.compile(r'(\d+\.?\d*)\s*(MHz|GHz|KHz|Hz)'),
                re.compile(r'[Ff]requency\s*[=:]\s*(\d+\.?\d*)\s*(MHz|GHz|KHz|Hz)'),
                re.compile(r'[Cc]lock\s*[=:]\s*(\d+\.?\d*)\s*(MHz|GHz|KHz|Hz)'),
            ],
            'current': [
                re.compile(r'(\d+\.?\d*)\s*(mA|A|μA)\s*(?:±\s*(\d+\.?\d*)%)?'),
                re.compile(r'[Cc]urrent\s*[=:]\s*(\d+\.?\d*)\s*(mA|A|μA)'),
                re.compile(r'[Mm]ax\s+[Cc]urrent\s*[=:]\s*(\d+\.?\d*)\s*(mA|A|μA)'),
            ],
            'bitfield': [
                re.compile(r'[Bb]it\s*\[(\d+):(\d+)\]\s*[=:]\s*([A-Z_][A-Z0-9_]*)'),
                re.compile(r'[Bb]it\s+(\d+)\s*[=:]\s*([01])\s*[=:]\s*([A-Z_][A-Z0-9_]*)'),
                re.compile(r'[Bb]its?\s+(\d+)(?:-(\d+))?\s*[=:]\s*([A-Z_][A-Z0-9_]*)'),
            ],
        }
    
    def extract_all_entities(self, text: str) -> List[TechnicalEntity]:
        """Extract all types of technical entities from text"""
        entities = []
        
        # Extract each entity type
        entities.extend(self.extract_pin_info(text))
        entities.extend(self.extract_register_info(text))
        entities.extend(self.extract_voltage_specs(text))
        entities.extend(self.extract_timing_specs(text))
        entities.extend(self.extract_frequency_specs(text))
        entities.extend(self.extract_current_specs(text))
        entities.extend(self.extract_bitfield_info(text))
        entities.extend(self.extract_error_codes(text))
        entities.extend(self.extract_procedures(text))
        
        return entities
    
    def extract_pin_info(self, text: str) -> List[TechnicalEntity]:
        """Extract pin-related information"""
        entities = []
        
        for pattern in self.patterns['pin']:
            for match in pattern.finditer(text):
                if len(match.groups()) == 2:
                    pin_num, function = match.groups()
                    entities.append(TechnicalEntity(
                        entity_type=EntityType.PIN,
                        name=f'Pin {pin_num}',
                        value=function.strip(),
                        unit=None,
                        context=self._get_context(text, match),
                        metadata={'pin_number': pin_num}
                    ))
        
        return self._deduplicate_entities(entities)
    
    def extract_register_info(self, text: str) -> List[TechnicalEntity]:
        """Extract register addresses and values"""
        entities = []
        
        for pattern in self.patterns['register']:
            for match in pattern.finditer(text):
                groups = match.groups()
                
                if len(groups) == 1:  # Just address
                    addr = groups[0]
                    entities.append(TechnicalEntity(
                        entity_type=EntityType.REGISTER,
                        name=f'Register',
                        value=f'0x{addr.upper()}',
                        unit=None,
                        context=self._get_context(text, match),
                        metadata={'address': f'0x{addr.upper()}'}
                    ))
                elif len(groups) == 2:  # Name and address or address and value
                    if groups[0].replace('_', '').isalpha():
                        name, addr = groups
                        entities.append(TechnicalEntity(
                            entity_type=EntityType.REGISTER,
                            name=name,
                            value=f'0x{addr.upper()}',
                            unit=None,
                            context=self._get_context(text, match),
                            metadata={'address': f'0x{addr.upper()}'}
                        ))
                    else:
                        addr, val = groups
                        entities.append(TechnicalEntity(
                            entity_type=EntityType.REGISTER,
                            name=f'Register 0x{addr.upper()}',
                            value=f'0x{val.upper()}',
                            unit=None,
                            context=self._get_context(text, match),
                            metadata={'address': f'0x{addr.upper()}', 'value': f'0x{val.upper()}'}
                        ))
        
        return self._deduplicate_entities(entities)
    
    def extract_voltage_specs(self, text: str) -> List[TechnicalEntity]:
        """Extract voltage specifications"""
        entities = []
        
        for pattern in self.patterns['voltage']:
            for match in pattern.finditer(text):
                groups = match.groups()
                
                if len(groups) >= 1:
                    voltage = groups[0]
                    tolerance = groups[1] if len(groups) > 1 and groups[1] else None
                    
                    # Try to find what this voltage is for
                    context = self._get_context(text, match)
                    name = self._extract_voltage_name(context, match.start())
                    
                    metadata = {'voltage': voltage}
                    if tolerance:
                        metadata['tolerance'] = f'±{tolerance}%'
                    
                    entities.append(TechnicalEntity(
                        entity_type=EntityType.VOLTAGE,
                        name=name,
                        value=voltage,
                        unit='V',
                        context=context,
                        metadata=metadata
                    ))
        
        return self._deduplicate_entities(entities)
    
    def extract_timing_specs(self, text: str) -> List[TechnicalEntity]:
        """Extract timing specifications"""
        entities = []
        
        for pattern in self.patterns['timing']:
            for match in pattern.finditer(text):
                groups = match.groups()
                
                if len(groups) == 3:
                    # Determine order based on pattern
                    if groups[2].endswith('time'):
                        value, unit, name = groups
                    else:
                        name, value, unit = groups
                    
                    entities.append(TechnicalEntity(
                        entity_type=EntityType.TIMING,
                        name=name.strip(),
                        value=value,
                        unit=unit,
                        context=self._get_context(text, match),
                        metadata={'time_value': value, 'time_unit': unit}
                    ))
        
        return self._deduplicate_entities(entities)
    
    def extract_frequency_specs(self, text: str) -> List[TechnicalEntity]:
        """Extract frequency specifications"""
        entities = []
        
        for pattern in self.patterns['frequency']:
            for match in pattern.finditer(text):
                groups = match.groups()
                
                if len(groups) >= 2:
                    freq, unit = groups[0], groups[1]
                    context = self._get_context(text, match)
                    name = self._extract_frequency_name(context, match.start())
                    
                    entities.append(TechnicalEntity(
                        entity_type=EntityType.FREQUENCY,
                        name=name,
                        value=freq,
                        unit=unit,
                        context=context,
                        metadata={'frequency': freq, 'unit': unit}
                    ))
        
        return self._deduplicate_entities(entities)
    
    def extract_current_specs(self, text: str) -> List[TechnicalEntity]:
        """Extract current specifications"""
        entities = []
        
        for pattern in self.patterns['current']:
            for match in pattern.finditer(text):
                groups = match.groups()
                
                if len(groups) >= 2:
                    current = groups[0]
                    unit = groups[1]
                    tolerance = groups[2] if len(groups) > 2 and groups[2] else None
                    
                    context = self._get_context(text, match)
                    name = self._extract_current_name(context, match.start())
                    
                    metadata = {'current': current, 'unit': unit}
                    if tolerance:
                        metadata['tolerance'] = f'±{tolerance}%'
                    
                    entities.append(TechnicalEntity(
                        entity_type=EntityType.CURRENT,
                        name=name,
                        value=current,
                        unit=unit,
                        context=context,
                        metadata=metadata
                    ))
        
        return self._deduplicate_entities(entities)
    
    def extract_bitfield_info(self, text: str) -> List[TechnicalEntity]:
        """Extract bit field information"""
        entities = []
        
        for pattern in self.patterns['bitfield']:
            for match in pattern.finditer(text):
                groups = match.groups()
                
                if len(groups) >= 2:
                    # Handle different bit notations
                    if len(groups) == 3 and groups[1] and groups[2]:  # Bit range
                        start_bit = groups[0]
                        end_bit = groups[1]
                        function = groups[2]
                        name = f'Bits[{start_bit}:{end_bit}]'
                        metadata = {'start_bit': start_bit, 'end_bit': end_bit}
                    else:  # Single bit
                        bit_num = groups[0]
                        function = groups[-1]
                        name = f'Bit {bit_num}'
                        metadata = {'bit': bit_num}
                    
                    entities.append(TechnicalEntity(
                        entity_type=EntityType.BITFIELD,
                        name=name,
                        value=function,
                        unit=None,
                        context=self._get_context(text, match),
                        metadata=metadata
                    ))
        
        return self._deduplicate_entities(entities)
    
    def extract_error_codes(self, text: str) -> List[TechnicalEntity]:
        """Extract error codes and their meanings"""
        entities = []
        
        # Pattern for error codes
        error_patterns = [
            re.compile(r'[Ee]rror\s+(?:[Cc]ode\s+)?0x([0-9A-Fa-f]+)\s*[=:]\s*(.+?)(?=\n|$)'),
            re.compile(r'0x([0-9A-Fa-f]+)\s*[=:]\s*([A-Z_][A-Z0-9_]*_ERROR)'),
            re.compile(r'[Ee]rror\s+(\d+)\s*[=:]\s*(.+?)(?=\n|$)'),
        ]
        
        for pattern in error_patterns:
            for match in pattern.finditer(text):
                code, description = match.groups()
                
                entities.append(TechnicalEntity(
                    entity_type=EntityType.ERROR_CODE,
                    name=f'Error Code {code}',
                    value=description.strip(),
                    unit=None,
                    context=self._get_context(text, match),
                    metadata={'code': code}
                ))
        
        return self._deduplicate_entities(entities)
    
    def extract_procedures(self, text: str) -> List[TechnicalEntity]:
        """Extract step-by-step procedures"""
        entities = []
        
        # Pattern for procedures
        procedure_patterns = [
            re.compile(r'[Ss]tep\s+(\d+)\s*[:.]\s*(.+?)(?=\n[Ss]tep|\n\n|\Z)', re.DOTALL),
            re.compile(r'(\d+)\.\s+([A-Z][^.]+\.)', re.MULTILINE),
            re.compile(r'[Tt]o\s+([a-z]+\s+[^:]+):\s*\n(.+?)(?=\n\n|\Z)', re.DOTALL),
        ]
        
        for pattern in procedure_patterns:
            for match in pattern.finditer(text):
                if len(match.groups()) == 2:
                    step_num, step_desc = match.groups()
                    
                    # Clean up step description
                    step_desc = ' '.join(step_desc.split())
                    
                    entities.append(TechnicalEntity(
                        entity_type=EntityType.PROCEDURE_STEP,
                        name=f'Step {step_num}',
                        value=step_desc,
                        unit=None,
                        context=self._get_context(text, match, context_size=150),
                        metadata={'step_number': step_num}
                    ))
        
        return self._deduplicate_entities(entities)
    
    def _get_context(self, text: str, match: re.Match, context_size: int = 100) -> str:
        """Get context around a match"""
        start = max(0, match.start() - context_size)
        end = min(len(text), match.end() + context_size)
        return text[start:end].strip()
    
    def _extract_voltage_name(self, context: str, position: int) -> str:
        """Extract what the voltage specification is for"""
        # Look for voltage rail names
        rail_pattern = re.compile(r'([A-Z_][A-Z0-9_]*(?:_[A-Z0-9]+)*)\s+(?:voltage|rail|supply)', re.IGNORECASE)
        match = rail_pattern.search(context[:position])
        
        if match:
            return f'{match.group(1)} Voltage'
        
        # Look for component names
        comp_pattern = re.compile(r'([A-Z_][A-Z0-9_]*)\s+(?:requires|operates)', re.IGNORECASE)
        match = comp_pattern.search(context[:position])
        
        if match:
            return f'{match.group(1)} Operating Voltage'
        
        return 'Voltage Specification'
    
    def _extract_frequency_name(self, context: str, position: int) -> str:
        """Extract what the frequency specification is for"""
        # Look for clock names
        clock_pattern = re.compile(r'([A-Z_][A-Z0-9_]*)\s+(?:clock|frequency)', re.IGNORECASE)
        match = clock_pattern.search(context[:position])
        
        if match:
            return f'{match.group(1)} Clock'
        
        return 'Frequency Specification'
    
    def _extract_current_name(self, context: str, position: int) -> str:
        """Extract what the current specification is for"""
        # Look for current type
        current_pattern = re.compile(r'(maximum|typical|minimum|idle|peak)\s+current', re.IGNORECASE)
        match = current_pattern.search(context[:position])
        
        if match:
            return f'{match.group(1).capitalize()} Current'
        
        return 'Current Specification'
    
    def _deduplicate_entities(self, entities: List[TechnicalEntity]) -> List[TechnicalEntity]:
        """Remove duplicate entities based on name and value"""
        seen = set()
        unique_entities = []
        
        for entity in entities:
            key = (entity.entity_type, entity.name, entity.value)
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
        
        return unique_entities
